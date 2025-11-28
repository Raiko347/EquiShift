# -*- coding: utf-8 -*-
"""
widgets/plan_matrix_widget.py (Final für Synchronisation)
"""
from collections import defaultdict
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont

class PlanMatrixWidget(QWidget):
    event_selection_changed = pyqtSignal(int)

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._init_ui()
        self._populate_event_combobox()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        title_label = QLabel("Grafische Übersicht")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(QLabel("<b>Event für die Matrix-Übersicht auswählen:</b>"))
        self.event_combobox = QComboBox()
        self.event_combobox.setMinimumWidth(300)
        top_bar_layout.addWidget(self.event_combobox)
        top_bar_layout.addStretch()
        main_layout.addLayout(top_bar_layout)
        
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("QTableWidget::item { padding: 5px; }")
        main_layout.addWidget(self.table)
        
        self.event_combobox.currentIndexChanged.connect(self.on_event_changed)

    def refresh_view(self):
        self._populate_event_combobox()
        self.update_matrix_view()

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

    def on_event_changed(self):
        if not self.event_combobox.signalsBlocked():
            event_id = self.event_combobox.currentData()
            self.event_selection_changed.emit(event_id)
        self.update_matrix_view()

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
            self.update_matrix_view()
            
    def update_matrix_view(self):
        """Baut die Kreuztabelle auf."""
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        
        event_id = self.event_combobox.currentData()
        if event_id == -1: return

        plan_data = self.db_manager.get_plan_matrix_data(event_id)
        if not plan_data: return

        tasks = sorted(list(set(row['task_name'] for row in plan_data)))
        shifts = sorted(list(set((row['shift_date'], row['start_time'], row['end_time']) for row in plan_data)))

        self.table.setRowCount(len(tasks))
        self.table.setColumnCount(len(shifts))

        self.table.setVerticalHeaderLabels(tasks)
        self.table.verticalHeader().setVisible(True)
        
        header_labels = []
        for date, start, end in shifts:
            formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.')
            header_labels.append(f"{formatted_date}\n{start}-{end}")
        
        self.table.setHorizontalHeaderLabels(header_labels)
        self.table.horizontalHeader().setVisible(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setMinimumSectionSize(100) 

        light_gray = QBrush(QColor("#f0f0f0"))
        
        # NEU: Wir merken uns, wie viele Zeilen Text die höchste Zelle pro Reihe hat
        row_max_lines = defaultdict(int)

        for row_idx, task_name in enumerate(tasks):
            for col_idx, (date, start, end) in enumerate(shifts):
                
                cell_data = [
                    row for row in plan_data 
                    if row['task_name'] == task_name and 
                       row['shift_date'] == date and 
                       row['start_time'] == start and 
                       row['end_time'] == end
                ]

                if not cell_data:
                    cell_item = QTableWidgetItem("")
                    cell_item.setBackground(light_gray)
                    self.table.setItem(row_idx, col_idx, cell_item)
                    continue

                required = cell_data[0]['required_people']
                helpers = [row for row in cell_data if row['helper_name'] is not None]
                
                if not helpers:
                    cell_item = QTableWidgetItem("")
                    if required > 0:
                        cell_item.setBackground(QBrush(QColor(255, 220, 220)))
                    self.table.setItem(row_idx, col_idx, cell_item)
                    continue

                sorted_helpers = sorted(helpers, key=lambda x: (
                    -x['is_team_leader'], # Minus für "True zuerst"
                    x['helper_name']      # A-Z
                ))
                
                html_lines = []
                for h in sorted_helpers:
                    name = h['helper_name']
                    if h['is_team_leader']:
                        html_lines.append(f"{name} (TL)")
                    elif h['has_competence']:
                        html_lines.append(f"{name} (*)")
                    else:
                        html_lines.append(name)
                
                # NEU: Anzahl der Zeilen zählen und Maximum für diese Reihe speichern
                row_max_lines[row_idx] = max(row_max_lines[row_idx], len(html_lines))
                
                label = QLabel("<br>".join(html_lines))
                label.setAlignment(Qt.AlignCenter)
                
                if len(helpers) < required:
                    label.setStyleSheet("QLabel { background-color: #ffdcdc; }")
                else:
                    label.setStyleSheet("QLabel { background-color: transparent; }")

                self.table.setCellWidget(row_idx, col_idx, label)

        # NEU: Manuelle Höhenberechnung statt resizeRowsToContents
        # Wir holen die Höhe einer Textzeile basierend auf der aktuellen Schriftart
        font_metrics = self.table.fontMetrics()
        line_height = font_metrics.lineSpacing()
        
        for row in range(self.table.rowCount()):
            lines = row_max_lines[row]
            if lines > 0:
                # Höhe = (Anzahl Zeilen * Zeilenhöhe) + Padding (oben/unten)
                # 20px Extra-Padding sorgen dafür, dass nichts abgeschnitten wird
                total_height = (lines * line_height) + 20 
                self.table.setRowHeight(row, total_height)
            else:
                self.table.setRowHeight(row, 40) # Standardhöhe für leere Zeilen
        # Spaltenbreite korrigieren (Puffer hinzufügen) ---
        # Erst automatisch anpassen...
        self.table.resizeColumnsToContents()
        
        # ...dann überall 20 Pixel draufschlagen
        for col in range(self.table.columnCount()):
            current_width = self.table.columnWidth(col)
            self.table.setColumnWidth(col, current_width + 50) # 25px Puffer