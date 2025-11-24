# -*- coding: utf-8 -*-
"""
widgets/post_event_widget.py (mit Synchronisation)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QComboBox, QHeaderView, QMessageBox, QDialog,
    QListWidget, QListWidgetItem, QDialogButtonBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal

class PostEventWidget(QWidget):
    """Widget zur Nachbereitung von Events."""
    event_selection_changed = pyqtSignal(int)

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._init_ui()
        self._populate_event_combobox()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche."""
        main_layout = QVBoxLayout(self)
        title_label = QLabel("Nachbereitung von Events")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title_label)
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(QLabel("<b>Abgeschlossenes Event auswählen:</b>"))
        self.event_combobox = QComboBox()
        self.event_combobox.setMinimumWidth(300)
        top_bar_layout.addWidget(self.event_combobox)
        top_bar_layout.addStretch()
        main_layout.addLayout(top_bar_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Schicht", "Aufgabe", "Geplanter Helfer", "Finaler Status", "Anmerkung (Vertreter)"
        ])
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        main_layout.addWidget(self.table)
        button_layout = QHBoxLayout()
        self.set_all_done_button = QPushButton("Alle auf 'Erledigt' setzen")
        self.set_selection_done_button = QPushButton("Auswahl auf 'Erledigt' setzen")
        button_layout.addWidget(self.set_all_done_button)
        button_layout.addWidget(self.set_selection_done_button)
        button_layout.addStretch()
        self.save_button = QPushButton("Änderungen speichern")
        button_layout.addWidget(self.save_button)
        main_layout.addLayout(button_layout)
        self.event_combobox.currentIndexChanged.connect(self.on_event_changed)
        self.save_button.clicked.connect(self.save_changes)
        self.set_all_done_button.clicked.connect(self.set_all_to_done)
        self.set_selection_done_button.clicked.connect(self.set_selection_to_done)

    def on_event_changed(self):
        """Sendet nur noch das Signal, wenn der Benutzer eine Änderung vornimmt."""
        if not self.event_combobox.signalsBlocked():
            event_id = self.event_combobox.currentData()
            self.event_selection_changed.emit(event_id)
        self.load_assignments()

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
            self.load_assignments()

    def refresh_view(self):
        self._populate_event_combobox()
        self.load_assignments()

    def _populate_event_combobox(self):
        self.event_combobox.blockSignals(True) # Blockieren
        
        current_id = self.event_combobox.currentData()
        self.event_combobox.clear()
        self.event_combobox.addItem("--- Bitte Event wählen ---", -1)
        
        # Hier nur abgeschlossene Events
        events = self.db_manager.get_completed_events()
        if events:
            for event in events:
                self.event_combobox.addItem(event['name'], event['event_id'])
        
        index = self.event_combobox.findData(current_id)
        if index != -1:
            self.event_combobox.setCurrentIndex(index)
            
        self.event_combobox.blockSignals(False) # Freigeben

    def load_assignments(self):
        self.table.setRowCount(0)
        event_id = self.event_combobox.currentData()
        if event_id == -1: return
        assignments = self.db_manager.get_assignments_for_event(event_id)
        self.table.setRowCount(len(assignments))
        status_options = ['Geplant', 'Erledigt', 'Nicht Erschienen', 'Entschuldigt', 'Erledigt (durch Vertreter)']
        for row_idx, assignment in enumerate(assignments):
            shift_text = f"{assignment['shift_date']} {assignment['start_time']}-{assignment['end_time']}"
            self.table.setItem(row_idx, 0, QTableWidgetItem(shift_text))
            self.table.setItem(row_idx, 1, QTableWidgetItem(assignment['task_name']))
            self.table.setItem(row_idx, 2, QTableWidgetItem(assignment['person_name']))
            combo = QComboBox()
            combo.addItems(status_options)
            combo.setCurrentText(assignment['attendance_status'])
            combo.setProperty("assignment_id", assignment['assignment_id'])
            combo.setProperty("row", row_idx)
            self.table.setCellWidget(row_idx, 3, combo)
            note_item = QTableWidgetItem(assignment['substitute_name'] if assignment['substitute_name'] else "")
            note_item.setData(Qt.UserRole, None)
            self.table.setItem(row_idx, 4, note_item)
            combo.currentTextChanged.connect(self.on_status_changed)
        self.table.resizeRowsToContents()

    def on_status_changed(self, text):
        combo = self.sender()
        row = combo.property("row")
        if text == 'Erledigt (durch Vertreter)':
            dialog = SubstituteDialog(self.db_manager, self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_person_id:
                note_item = self.table.item(row, 4)
                note_item.setText(dialog.selected_person_name)
                note_item.setData(Qt.UserRole, dialog.selected_person_id)
            else:
                combo.setCurrentText('Geplant')
        else:
            note_item = self.table.item(row, 4)
            note_item.setText("")
            note_item.setData(Qt.UserRole, None)

    def save_changes(self):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 3)
            note_item = self.table.item(row, 4)
            assignment_id = combo.property("assignment_id")
            new_status = combo.currentText()
            substitute_id = note_item.data(Qt.UserRole)
            self.db_manager.update_assignment_status(assignment_id, new_status, substitute_id)
        QMessageBox.information(self, "Gespeichert", "Die Änderungen wurden erfolgreich gespeichert.")
        self.load_assignments()

    def set_all_to_done(self):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 3)
            if combo:
                combo.setCurrentText("Erledigt")

    def set_selection_to_done(self):
        selected_rows = {index.row() for index in self.table.selectedIndexes()}
        if not selected_rows:
            QMessageBox.information(self, "Keine Auswahl", "Bitte markieren Sie zuerst eine oder mehrere Zeilen.")
            return
        for row in selected_rows:
            combo = self.table.cellWidget(row, 3)
            if combo:
                combo.setCurrentText("Erledigt")

class SubstituteDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_person_id = None
        self.selected_person_name = None
        self.setWindowTitle("Vertreter auswählen")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Bitte wählen Sie den Vertreter aus:"))
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self._populate_list()

    def _populate_list(self):
        persons = self.db_manager.get_all_persons()
        for person in persons:
            item = QListWidgetItem(person['display_name'])
            item.setData(Qt.UserRole, person['person_id'])
            self.list_widget.addItem(item)

    def accept(self):
        if self.list_widget.currentItem():
            self.selected_person_id = self.list_widget.currentItem().data(Qt.UserRole)
            self.selected_person_name = self.list_widget.currentItem().text()
        super().accept()