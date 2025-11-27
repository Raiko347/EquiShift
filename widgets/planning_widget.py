# -*- coding: utf-8 -*-
"""
widgets/planning_widget.py (Final für Synchronisation)
"""
import os
from collections import defaultdict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QTreeWidgetItem, QLabel, QComboBox, QFrame, QHeaderView, QMessageBox,
    QFileDialog, QDialog, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTime
from PyQt5.QtGui import QBrush, QColor, QFont
from .shift_dialog import ShiftDialog
from .shift_details_widget import ShiftDetailsWidget
from .task_from_template_dialog import TaskFromTemplateDialog
from .task_dialog import TaskDialog
from .export_dialog import ExportDialog
from utils.exporter import Exporter

class PlanningWidget(QWidget):
    plan_changed = pyqtSignal(int, str)
    event_selection_changed = pyqtSignal(int)

    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.settings = settings
        self.plan_is_dirty = False
        self.warning_shown = False
        self._last_event_id = -1
        self._init_ui()
        self._populate_event_combobox()

    def _init_ui(self):
            main_layout = QVBoxLayout(self)
            
            # Titel
            title_layout = QHBoxLayout()
            title_label = QLabel("Schichtplanung")
            title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
            title_layout.addWidget(title_label)
            title_layout.addStretch()
            main_layout.addLayout(title_layout)
            
            # Top Bar (Event Auswahl & Export)
            top_bar_layout = QHBoxLayout()
            top_bar_layout.addWidget(QLabel("<b>Event für die Planung auswählen:</b>"))
            self.event_combobox = QComboBox()
            self.event_combobox.setMinimumWidth(300)
            top_bar_layout.addWidget(self.event_combobox)
            top_bar_layout.addStretch()
            self.export_button = QPushButton("Dienstplan exportieren")
            top_bar_layout.addWidget(self.export_button)
            main_layout.addLayout(top_bar_layout)
            
            # Proposal Bar (Buttons)
            proposal_layout = QHBoxLayout()
            proposal_layout.addWidget(QLabel("Malus-Basis:"))
            self.proposal_limit_combo = QComboBox()
            self.proposal_limit_combo.addItems(["Alle Dienste", "Letzter Dienst", "Letzte 2 Dienste", "Letzte 3 Dienste", "Letzte 4 Dienste"])
            proposal_layout.addWidget(self.proposal_limit_combo)
            proposal_layout.addStretch(1)
            
            self.proposal_button = QPushButton("Automatischen Planungsvorschlag erstellen")
            self.proposal_button.setStyleSheet("background-color: #cde; font-weight: bold;")
            
            self.check_plan_button = QPushButton("Dienstplan prüfen")
            
            proposal_layout.addWidget(self.proposal_button)
            proposal_layout.addWidget(self.check_plan_button)
            
            self.reset_proposal_button = QPushButton("Planung zurücksetzen")
            proposal_layout.addWidget(self.reset_proposal_button)
            main_layout.addLayout(proposal_layout)
            
            # Trennlinie
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            main_layout.addWidget(line)
            
            # Hauptinhalt (Split Layout)
            content_layout = QHBoxLayout()
            
            # --- LINKES PANEL (Baum) ---
            left_panel = QVBoxLayout()
            left_panel.addWidget(QLabel("Aufgaben und Schichten:"))
            
            self.plan_tree = QTreeWidget()
            self.plan_tree.setHeaderLabels(["Planungsstruktur", "Status"])
            
            # OPTIMIERUNG 1: Spaltenbreiten
            self.plan_tree.header().setSectionResizeMode(0, QHeaderView.Stretch) # Nimmt den ganzen Platz
            self.plan_tree.header().setSectionResizeMode(1, QHeaderView.Fixed)   # Fixe Breite
            self.plan_tree.header().resizeSection(1, 50) # 50 Pixel für "[5/5]" reichen
            
            left_panel.addWidget(self.plan_tree)
            
            # Buttons unter dem Baum
            button_layout = QHBoxLayout()
            self.add_task_button = QPushButton("Aufgaben aus Vorlagen...")
            self.add_shift_button = QPushButton("Neue Schicht")
            self.edit_item_button = QPushButton("Auswahl bearbeiten")
            self.delete_item_button = QPushButton("Auswahl löschen")
            button_layout.addWidget(self.add_task_button)
            button_layout.addWidget(self.add_shift_button)
            button_layout.addWidget(self.edit_item_button)
            button_layout.addWidget(self.delete_item_button)
            left_panel.addLayout(button_layout)
            
            # OPTIMIERUNG 2: Layout-Verhältnis (2:1)
            content_layout.addLayout(left_panel, 2) # Linkes Panel bekommt 2/3 der Breite
            
            # --- RECHTES PANEL (Details) ---
            right_panel = QVBoxLayout()
            right_panel.addWidget(QLabel("<b>Details zur ausgewählten Schicht:</b>"))
            self.details_widget = ShiftDetailsWidget(self.db_manager, self)
            right_panel.addWidget(self.details_widget)
            
            content_layout.addLayout(right_panel, 1) # Rechtes Panel bekommt 1/3 der Breite
            
            main_layout.addLayout(content_layout)
            
            # Signale verbinden
            self.event_combobox.currentIndexChanged.connect(self.on_event_changed)
            self.plan_tree.itemSelectionChanged.connect(self._update_button_states)
            self.plan_tree.itemSelectionChanged.connect(self._update_details_view)
            self.add_task_button.clicked.connect(self._add_task)
            self.add_shift_button.clicked.connect(self._add_shift)
            self.edit_item_button.clicked.connect(self._edit_item)
            self.delete_item_button.clicked.connect(self._delete_item)
            self.details_widget.data_changed.connect(self.update_plan_view)
            self.proposal_button.clicked.connect(self._generate_proposal)
            self.check_plan_button.clicked.connect(self._check_plan)
            self.reset_proposal_button.clicked.connect(self._reset_planning)
            self.export_button.clicked.connect(self._export_plan)
            
            self._update_button_states()

    def on_event_changed(self):
        if not self.event_combobox.signalsBlocked():
            event_id = self.event_combobox.currentData()
            self.event_selection_changed.emit(event_id)
        self.update_plan_view()

    def set_current_event(self, event_id):
        index = self.event_combobox.findData(event_id)
        if index == -1:
            self._populate_event_combobox()
            index = self.event_combobox.findData(event_id)
        if index == -1: index = 0
        if self.event_combobox.currentIndex() != index:
            self.event_combobox.blockSignals(True)
            self.event_combobox.setCurrentIndex(index)
            self.event_combobox.blockSignals(False)
            self.update_plan_view()

    def refresh_view(self):
        self._populate_event_combobox()
        self.update_plan_view()

    def _populate_event_combobox(self):
        self.event_combobox.blockSignals(True)
        current_id = self.event_combobox.currentData()
        self.event_combobox.clear()
        self.event_combobox.addItem("--- Bitte Event wählen ---", -1)
        events = self.db_manager.get_all_events()
        if events:
            for event in events:
                self.event_combobox.addItem(event['name'], event['event_id'])
        index = self.event_combobox.findData(current_id)
        if index != -1:
            self.event_combobox.setCurrentIndex(index)
        self.event_combobox.blockSignals(False)

    def update_plan_view(self):
        selected_item_data = None
        if self.plan_tree.currentItem():
            selected_item_data = self.plan_tree.currentItem().data(0, Qt.UserRole)
        self.plan_tree.clear()
        event_id = self.event_combobox.currentData()
        event_name = self.event_combobox.currentText()
        self.plan_changed.emit(event_id, event_name)
        if self._last_event_id != event_id:
            self.plan_is_dirty = False
            self.warning_shown = False
        self._last_event_id = event_id
        if event_id == -1:
            self._update_button_states()
            self._update_details_view()
            return
        tasks = self.db_manager.get_tasks_for_event(event_id)
        task_sort_keys = {}
        for task in tasks:
            shifts = self.db_manager.get_shifts_for_task(task['task_id'])
            if shifts:
                min_shift = min(shifts, key=lambda s: (s['shift_date'], s['start_time']))
                task_sort_keys[task['task_id']] = (min_shift['shift_date'], min_shift['start_time'])
            else:
                task_sort_keys[task['task_id']] = ('9999-12-31', '23:59')
        sorted_tasks = sorted(tasks, key=lambda t: task_sort_keys[t['task_id']])
        item_to_reselect = None
        light_red = QBrush(QColor(255, 220, 220))
        for task in sorted_tasks:
            task_item = QTreeWidgetItem(self.plan_tree)
            task_item.setText(0, task['name'])
            task_item.setData(0, Qt.UserRole, {'type': 'task', 'id': task['task_id']})
            if selected_item_data and selected_item_data['type'] == 'task' and selected_item_data['id'] == task['task_id']:
                item_to_reselect = task_item
            shifts = self.db_manager.get_shifts_for_task(task['task_id'])
            sorted_shifts = sorted(shifts, key=lambda s: (s['shift_date'], s['start_time']))
            for shift in sorted_shifts:
                assigned = shift['assigned_count']
                required = shift['required_people']
                status_text = f"[{assigned}/{required}]"
                formatted_date = QDate.fromString(shift['shift_date'], "yyyy-MM-dd").toString("dd.MM.yyyy")
                shift_item = QTreeWidgetItem(task_item)
                shift_item.setText(0, f"Schicht: {formatted_date} {shift['start_time']} - {shift['end_time']}")
                shift_item.setText(1, status_text)
                shift_item.setData(0, Qt.UserRole, {'type': 'shift', 'id': shift['shift_id']})
                if assigned < required:
                    shift_item.setBackground(0, light_red)
                    shift_item.setBackground(1, light_red)
                if selected_item_data and selected_item_data['type'] == 'shift' and selected_item_data['id'] == shift['shift_id']:
                    item_to_reselect = shift_item
        self.plan_tree.expandAll()
        if item_to_reselect:
            self.plan_tree.setCurrentItem(item_to_reselect)
        self._update_button_states()
        self._update_details_view()

    def _update_button_states(self):
        selected_item = self.plan_tree.currentItem()
        event_id = self.event_combobox.currentData()
        event_selected = event_id != -1
        is_editable = False
        if event_selected:
            event = self.db_manager.get_event_by_id(event_id)
            if event and event['status'] != 'Abgeschlossen':
                is_editable = True
        
        if self.plan_is_dirty:
            self.proposal_button.setText("Planungsvorschlag AKTUALISIEREN (!)")
            self.proposal_button.setStyleSheet("background-color: #ffc107; font-weight: bold;")
            if not self.warning_shown and is_editable:
                QMessageBox.warning(self, "Planung veraltet", "Die Planungsstruktur wurde geändert.\nEs wird empfohlen, den Planungsvorschlag zu aktualisieren.")
                self.warning_shown = True
        else:
            self.proposal_button.setText("Automatischen Planungsvorschlag erstellen")
            self.proposal_button.setStyleSheet("background-color: #cde; font-weight: bold;")
            self.warning_shown = False
            
        self.add_task_button.setEnabled(is_editable)
        self.proposal_button.setEnabled(is_editable)
        self.check_plan_button.setEnabled(event_selected)
        self.reset_proposal_button.setEnabled(is_editable)
        self.export_button.setEnabled(event_selected)
        self.details_widget.set_editable(is_editable)
        self.add_shift_button.setEnabled(False)
        self.edit_item_button.setEnabled(False)
        self.delete_item_button.setEnabled(False)
        if not selected_item or not is_editable:
            return
        item_data = selected_item.data(0, Qt.UserRole)
        item_type = item_data.get('type') if item_data else None
        if item_type == 'task':
            self.add_shift_button.setEnabled(True)
            self.edit_item_button.setEnabled(True)
            self.delete_item_button.setEnabled(True)
        elif item_type == 'shift':
            self.edit_item_button.setEnabled(True)
            self.delete_item_button.setEnabled(True)

    def _update_details_view(self):
        selected_item = self.plan_tree.currentItem()
        if not selected_item:
            self.details_widget.clear_view()
            return
        item_data = selected_item.data(0, Qt.UserRole)
        item_type = item_data.get('type') if item_data else None
        if item_type == 'shift':
            shift_id = item_data['id']
            self.details_widget.load_shift_data(shift_id)
        else:
            self.details_widget.clear_view()

    def _add_task(self):
        event_id = self.event_combobox.currentData()
        if event_id == -1:
            QMessageBox.warning(self, "Kein Event", "Bitte wählen Sie zuerst ein Event aus.")
            return
        dialog = TaskFromTemplateDialog(self.db_manager, event_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.plan_is_dirty = True
            self.update_plan_view()

    def _add_shift(self):
        selected_item = self.plan_tree.currentItem()
        if not selected_item: return
        item_data = selected_item.data(0, Qt.UserRole)
        if not item_data or item_data.get('type') != 'task': return
        task_id = item_data['id']
        event_id = self.event_combobox.currentData()
        event = self.db_manager.get_event_by_id(event_id)
        if not event: return
        existing_shifts = self.db_manager.get_shifts_for_task(task_id)
        default_start_time = QTime(18, 0)
        if existing_shifts:
            last_shift = max(existing_shifts, key=lambda s: (s['shift_date'], s['end_time']))
            default_start_time = QTime.fromString(last_shift['end_time'], "HH:mm")
        dialog = ShiftDialog(self.db_manager, task_id, event['start_date'], event['end_date'], parent=self)
        dialog.start_time_input.setTime(default_start_time)
        dialog.end_time_input.setTime(default_start_time.addSecs(2 * 3600))
        if dialog.exec_() == QDialog.Accepted:
            self.plan_is_dirty = True
            self.update_plan_view()

    def _generate_proposal(self):
        event_id = self.event_combobox.currentData()
        event_name = self.event_combobox.currentText()
        if event_id == -1: return
        limit_text = self.proposal_limit_combo.currentText()
        limit = None
        if "Letzte" in limit_text: limit = int(limit_text.split(' ')[1])
        elif "Letzter" in limit_text: limit = 1
        reply = QMessageBox.question(self, "Planungsvorschlag erstellen", f"Möchten Sie wirklich einen neuen automatischen Planungsvorschlag für das Event '{event_name}' erstellen?\n\nACHTUNG: Alle bestehenden Zuweisungen für dieses Event werden zuerst entfernt!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.clear_assignments_for_event(event_id)
            filled, total = self.db_manager.generate_planning_proposal(event_id, limit=limit)
            self.plan_is_dirty = False
            self.update_plan_view()
            QMessageBox.information(self, "Planung abgeschlossen", f"Der automatische Planungsvorschlag ist fertig.\n\nEs konnten {filled} von {total} Plätzen besetzt werden.")

    def _check_plan(self):
        event_id = self.event_combobox.currentData()
        if event_id == -1: return
        
        warnings = self.db_manager.validate_event_plan(event_id)
        
        if not warnings:
            QMessageBox.information(self, "Planprüfung", "✅ Es wurden keine Regelverstöße gefunden.\nDer Plan sieht gut aus!")
        else:
            msg = QDialog(self)
            msg.setWindowTitle("Planprüfung - Warnungen")
            msg.setMinimumSize(600, 400)
            layout = QVBoxLayout(msg)
            
            font_size = self.settings.get_font_size()
            font = QFont()
            font.setPointSize(font_size)

            header = QLabel(f"<b>Es wurden {len(warnings)} potenzielle Probleme gefunden:</b>")
            header.setFont(font)
            layout.addWidget(header)
            
            scroll = QScrollArea()
            content = QLabel("\n".join(warnings))
            content.setWordWrap(True)
            content.setTextInteractionFlags(Qt.TextSelectableByMouse)
            content.setFont(font)
            content.setStyleSheet("padding: 5px;")
            
            scroll.setWidget(content)
            scroll.setWidgetResizable(True)
            layout.addWidget(scroll)
            
            btn = QPushButton("OK")
            btn.setFont(font)
            btn.clicked.connect(msg.accept)
            layout.addWidget(btn)
            
            msg.exec_()

    def _reset_planning(self):
        event_id = self.event_combobox.currentData()
        event_name = self.event_combobox.currentText()
        if event_id == -1: return
        reply = QMessageBox.question(self, "Planung zurücksetzen", f"Sind Sie sicher, dass Sie alle Helfer-Zuweisungen für das Event '{event_name}' entfernen möchten?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.clear_assignments_for_event(event_id)
            self.plan_is_dirty = False 
            self.warning_shown = False
            self.update_plan_view()
            if self.window().statusBar():
                self.window().statusBar().showMessage(f"Planung für '{event_name}' wurde erfolgreich zurückgesetzt.", 5000)

    def _edit_item(self):
        selected_item = self.plan_tree.currentItem()
        if not selected_item: return
        item_data = selected_item.data(0, Qt.UserRole)
        if not item_data: return
        item_type = item_data.get('type')
        item_id = item_data.get('id')
        dialog = None
        if item_type == 'task':
            event_id = self.event_combobox.currentData()
            dialog = TaskDialog(self.db_manager, event_id, task_id=item_id, parent=self)
        elif item_type == 'shift':
            task_id = selected_item.parent().data(0, Qt.UserRole)['id']
            event_id = self.event_combobox.currentData()
            event = self.db_manager.get_event_by_id(event_id)
            if not event: return
            dialog = ShiftDialog(self.db_manager, task_id, event['start_date'], event['end_date'], shift_id=item_id, parent=self)
        if dialog and dialog.exec_() == QDialog.Accepted:
            self.plan_is_dirty = True
            self.update_plan_view()

    def _delete_item(self):
        selected_item = self.plan_tree.currentItem()
        if not selected_item: return
        item_data = selected_item.data(0, Qt.UserRole)
        if not item_data: return
        item_type = item_data.get('type')
        item_id = item_data.get('id')
        item_name = selected_item.text(0)
        message = ""
        if item_type == 'task':
            message = f"Möchten Sie die Aufgabe '{item_name}' wirklich löschen?\n\nAlle zugehörigen Schichten und Zuweisungen werden ebenfalls entfernt."
        elif item_type == 'shift':
            message = f"Möchten Sie die '{item_name}' wirklich löschen?\n\nAlle Zuweisungen für diese Schicht werden entfernt."
        else:
            return
        reply = QMessageBox.question(self, "Löschen bestätigen", message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if item_type == 'task':
                self.db_manager.delete_task(item_id)
            elif item_type == 'shift':
                self.db_manager.delete_shift(item_id)
            self.plan_is_dirty = True
            self.update_plan_view()

    def _export_plan(self):
        event_id = self.event_combobox.currentData()
        event_name = self.event_combobox.currentText()
        if event_id == -1: return
        dialog = ExportDialog(self.db_manager, event_id, self)
        if dialog.exec_() != QDialog.Accepted: return
        export_type = dialog.export_type
        export_format = dialog.export_format
        selected_task_id = dialog.selected_task_id
        if export_type == 'total':
            self.export_total_plan(event_id, event_name, export_format)
        elif export_type == 'daily':
            self.export_daily_plans(event_id, event_name, export_format)
        elif export_type == 'duty':
            self.export_duty_plan(event_id, event_name, export_format, selected_task_id)
        elif export_type in ['post_event_all', 'post_event_single']:
            self.export_post_event_sheets(event_id, event_name, selected_task_id if export_type == 'post_event_single' else None)
        else:
            QMessageBox.information(self, "Noch nicht implementiert", f"Der Export-Typ '{export_type}' ist noch nicht implementiert.")

    def export_total_plan(self, event_id, event_name, export_format):
        last_path = self.settings.get_last_export_path()
        default_filename = os.path.join(last_path, f"Dienstplan_{event_name.replace(' ', '_')}")
        file_filter = "PDF-Datei (*.pdf)" if export_format == 'pdf' else "Excel-Datei (*.xlsx)"
        file_path, _ = QFileDialog.getSaveFileName(self, "Gesamtplan exportieren", default_filename, file_filter)
        if not file_path: return
        self.settings.set_last_export_path(os.path.dirname(file_path))
        export_data = self.db_manager.get_export_data_for_event(event_id)
        # --- NEU: Anhänge laden und übergeben ---
        attachments = []
        if export_format == 'pdf':
            att_data = self.db_manager.get_attachments_for_event(event_id)
            attachments = [a['file_path'] for a in att_data]
        # ----------------------------------------
        self._execute_export(export_data, event_name, file_path, export_format, attachments=attachments)

    def export_daily_plans(self, event_id, event_name, export_format):
            last_path = self.settings.get_last_export_path()
            folder_path = QFileDialog.getExistingDirectory(self, "Ordner für Tagespläne auswählen", last_path)
            if not folder_path: return
            self.settings.set_last_export_path(folder_path)
            
            all_data = self.db_manager.get_export_data_for_event(event_id)
            if not all_data:
                QMessageBox.information(self, "Keine Daten", "Für dieses Event sind keine Schichten geplant.")
                return
                
            # --- NEU: Anhänge einmal laden ---
            attachments = []
            if export_format == 'pdf':
                att_data = self.db_manager.get_attachments_for_event(event_id)
                attachments = [a['file_path'] for a in att_data]
            # ---------------------------------

            unique_dates = sorted(list(set(row['shift_date'] for row in all_data)))
            exported_files = []
            
            for date in unique_dates:
                daily_data = [row for row in all_data if row['shift_date'] == date]
                formatted_date = QDate.fromString(date, "yyyy-MM-dd").toString("dd_MM_yyyy")
                file_name = f"Tagesplan_{event_name.replace(' ', '_')}_{formatted_date}.{export_format}"
                file_path = os.path.join(folder_path, file_name)
                daily_event_name = f"{event_name} ({QDate.fromString(date, 'yyyy-MM-dd').toString('dd.MM.yyyy')})"
                
                # --- NEU: Anhänge übergeben ---
                if self._execute_export(daily_data, daily_event_name, file_path, export_format, attachments=attachments):
                    exported_files.append(file_name)
                # ------------------------------

            if exported_files:
                QMessageBox.information(self, "Export erfolgreich", f"{len(exported_files)} Tagespläne wurden erfolgreich im Ordner\n{folder_path}\ngespeichert.")
            else:
                QMessageBox.critical(self, "Export fehlgeschlagen", "Es konnten keine Tagespläne exportiert werden.")

    def export_duty_plan(self, event_id, event_name, export_format, task_id):
        if task_id == -99:
            self.export_all_duty_plans(event_id, event_name, export_format)
            return
        if task_id is None:
            QMessageBox.warning(self, "Keine Auswahl", "Bitte wählen Sie einen Dienst aus dem Dropdown-Menü aus.")
            return
            
        task = self.db_manager.get_task_by_id(task_id)
        task_name = task['name'] if task else "Unbekannter_Dienst"
        
        last_path = self.settings.get_last_export_path()
        default_filename = os.path.join(last_path, f"Dienstplan_{task_name.replace(' ', '_')}")
        file_filter = "PDF-Datei (*.pdf)" if export_format == 'pdf' else "Excel-Datei (*.xlsx)"
        file_path, _ = QFileDialog.getSaveFileName(self, f"Plan für '{task_name}' exportieren", default_filename, file_filter)
        if not file_path: return
        self.settings.set_last_export_path(os.path.dirname(file_path))
        
        export_data = self.db_manager.get_export_data_for_event(event_id, filter_task_id=task_id)
        export_title = f"{event_name} - {task_name}"
        
        # --- NEU: Anhänge laden und übergeben ---
        attachments = []
        if export_format == 'pdf':
            att_data = self.db_manager.get_attachments_for_event(event_id)
            attachments = [a['file_path'] for a in att_data]
        # ----------------------------------------

        self._execute_export(export_data, export_title, file_path, export_format, tasks_to_show=[task_name], attachments=attachments)

    def export_all_duty_plans(self, event_id, event_name, export_format):
        last_path = self.settings.get_last_export_path()
        folder_path = QFileDialog.getExistingDirectory(self, "Ordner für Dienst-Pläne auswählen", last_path)
        if not folder_path: return
        self.settings.set_last_export_path(folder_path)
        
        tasks = self.db_manager.get_tasks_for_event(event_id)
        if not tasks:
            QMessageBox.information(self, "Keine Daten", "Für dieses Event sind keine Aufgaben geplant.")
            return
            
        # --- NEU: Anhänge einmal laden ---
        attachments = []
        if export_format == 'pdf':
            att_data = self.db_manager.get_attachments_for_event(event_id)
            attachments = [a['file_path'] for a in att_data]
        # ---------------------------------

        exported_files = []
        for task in tasks:
            task_id = task['task_id']
            task_name = task['name']
            export_data = self.db_manager.get_export_data_for_event(event_id, filter_task_id=task_id)
            if not export_data: continue
            
            file_name = f"Dienstplan_{task_name.replace(' ', '_')}.{export_format}"
            file_path = os.path.join(folder_path, file_name)
            export_title = f"{event_name} - {task_name}"
            
            # --- NEU: Anhänge übergeben ---
            if self._execute_export(export_data, export_title, file_path, export_format, tasks_to_show=[task_name], attachments=attachments):
                exported_files.append(file_name)
            # ------------------------------

        if exported_files:
            QMessageBox.information(self, "Export erfolgreich", f"{len(exported_files)} Dienst-Pläne wurden erfolgreich im Ordner\n{folder_path}\ngespeichert.")
        else:
            QMessageBox.critical(self, "Export fehlgeschlagen", "Es konnten keine Dienst-Pläne exportiert werden.")

    def export_post_event_sheets(self, event_id, event_name, task_id):
        last_path = self.settings.get_last_export_path()
        default_filename = os.path.join(last_path, f"Nachbereitung_{event_name.replace(' ', '_')}")
        file_path, _ = QFileDialog.getSaveFileName(self, "Nachbereitungs-Bögen speichern", default_filename, "PDF-Datei (*.pdf)")
        if not file_path: return
        self.settings.set_last_export_path(os.path.dirname(file_path))
        export_data = self.db_manager.get_post_event_data(event_id, filter_task_id=task_id)
        success = Exporter.export_post_event_sheets(export_data, event_name, file_path, self.settings)
        if success:
            QMessageBox.information(self, "Export erfolgreich", f"Die Nachbereitungs-Bögen wurden erfolgreich exportiert.")
        else:
            QMessageBox.critical(self, "Export fehlgeschlagen", "Die Bögen konnten nicht exportiert werden.")

    def _execute_export(self, data, name, path, format, tasks_to_show=None, attachments=None):
        success = False
        if format == 'xlsx':
            if tasks_to_show:
                data = [row for row in data if row['aufgabe'] in tasks_to_show]
            success = Exporter.export_to_xlsx(data, name, path)
        elif format == 'pdf':
            success = Exporter.export_to_pdf_matrix(data, name, path, self.settings, tasks_to_show=tasks_to_show, attachments=attachments)
        return success