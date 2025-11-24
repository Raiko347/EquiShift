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
        main_layout.addWidget(self.table)
        self.event_combobox.currentIndexChanged.connect(self.on_event_changed)

    def refresh_view(self):
        self._populate_event_combobox()
        self.update_matrix_view()

    def _populate_event_combobox(self):
        self.event_combobox.blockSignals(True) # Blockieren
        
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
            
        self.event_combobox.blockSignals(False) # Freigeben

    def on_event_changed(self):
        """Sendet nur noch das Signal, wenn der Benutzer eine Änderung vornimmt."""
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

        # 1. Daten aufbereiten
        tasks = sorted(list(set(row['task_name'] for row in plan_data)))
        shifts = sorted(list(set((row['shift_date'], row['start_time'], row['end_time']) for row in plan_data)))

        # 2. Tabellengröße und Header
        num_tasks = len(tasks)
        num_shifts = len(shifts)
        self.table.setRowCount(num_tasks + 2)
        self.table.setColumnCount(num_shifts + 1)

        dates = defaultdict(list)
        for i, (date, start, end) in enumerate(shifts):
            formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')
            dates[formatted_date].append(i + 1)
            time_item = QTableWidgetItem(f"{start} - {end}")
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(1, i + 1, time_item)

        for date_str, cols in dates.items():
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(0, cols[0], date_item)
            if len(cols) > 1:
                self.table.setSpan(0, cols[0], 1, len(cols))

        for i, task_name in enumerate(tasks):
            task_item = QTableWidgetItem(task_name)
            self.table.setItem(i + 2, 0, task_item)

        # 3. Zellen füllen und formatieren
        light_red = QBrush(QColor(255, 220, 220))
        light_gray = QBrush(QColor("#f0f0f0"))

        for row_idx, task_name in enumerate(tasks):
            for col_idx, (date, start, end) in enumerate(shifts):
                
                # Finde alle relevanten Einträge für DIESE ZELLE
                cell_data = [
                    row for row in plan_data 
                    if row['task_name'] == task_name and 
                       row['shift_date'] == date and 
                       row['start_time'] == start and 
                       row['end_time'] == end
                ]

                cell_item = QTableWidgetItem("")
                
                if not cell_data:
                    # Für diese Aufgabe gibt es diese Schicht nicht -> grau
                    cell_item.setBackground(light_gray)
                    self.table.setItem(row_idx + 2, col_idx + 1, cell_item)
                    continue

                # Es gibt eine Schicht, also fülle die Daten
                required = cell_data[0]['required_people']
                helpers = [row for row in cell_data if row['helper_name'] is not None]
                
                helper_texts = []
                sorted_helpers = sorted(helpers, key=lambda x: (x['is_team_leader'], x['has_competence'], x['helper_name']), reverse=True)
                for h in sorted_helpers:
                    text = h['helper_name']
                    if h['is_team_leader']: text += " (TL)"
                    elif h['has_competence']: text += " (*)"
                    helper_texts.append(text)
                
                cell_item.setText("\n".join(helper_texts))
                
                # HIER WURDE DIE FETTSCHRIFT ENTFERNT
                # if any(h['is_team_leader'] for h in helpers):
                #    cell_item.setFont(bold_font)

                if len(helpers) < required:
                    cell_item.setBackground(light_red)

                cell_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                self.table.setItem(row_idx + 2, col_idx + 1, cell_item)

        # 4. Layout anpassen
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)