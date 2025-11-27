# -*- coding: utf-8 -*-
"""
widgets/assign_helper_dialog.py

Dialog zur Auswahl und Zuweisung eines Helfers zu einer Schicht.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QAbstractItemView # NEU
)
from PyQt5.QtGui import QColor, QFont


class AssignHelperDialog(QDialog):
    """Dialog zur Auswahl eines verfügbaren Helfers."""

    def __init__(self, db_manager, shift_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.shift_id = shift_id
        self.selected_person_ids = [] # NEU: Liste statt einzelner ID
        
        self.helpers_data = []

        self.setWindowTitle("Helfer zuweisen")
        self.setMinimumSize(450, 500)

        self._init_ui()
        self._load_data()
        self._update_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Sortieren nach:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Eignung (Standard)", 
            "Score (Wenigste Punkte zuerst)", 
            "Score (Meiste Punkte zuerst)",
            "Name (A-Z)"
        ])
        self.sort_combo.currentIndexChanged.connect(self._update_list)
        sort_layout.addWidget(self.sort_combo)
        layout.addLayout(sort_layout)

        self.helper_list = QListWidget()
        # NEU: Mehrfachauswahl aktivieren
        self.helper_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.helper_list)

        legend_label = QLabel(
            "<font color='blue'><b>Blau: Teamleiter</b></font><br>"
            "<font color='green'><b>Grün: Kompetenz vorhanden</b></font><br>"
            "<font color='red'>Rot: Warnung (Pausen / Überlastung)</font>"
        )
        layout.addWidget(legend_label)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Ok).setText("Zuweisen")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_data(self):
        self.helpers_data = self.db_manager.get_available_helpers_for_shift(
            self.shift_id
        )

    def _update_list(self):
        self.helper_list.clear()

        if not self.helpers_data:
            self.helper_list.addItem("Keine verfügbaren Helfer gefunden.")
            self.helper_list.setEnabled(False)
            return

        sort_mode = self.sort_combo.currentIndex()
        
        if sort_mode == 0:
            self.helpers_data.sort(key=lambda x: (
                -x['is_team_leader'],
                -x['has_competence'],
                -(len(x['warnings']) == 0),
                x['score'],
                x['display_name']
            ))
        elif sort_mode == 1:
            self.helpers_data.sort(key=lambda x: (x['score'], x['display_name']))
        elif sort_mode == 2:
            self.helpers_data.sort(key=lambda x: (-x['score'], x['display_name']))
        elif sort_mode == 3:
            self.helpers_data.sort(key=lambda x: x['display_name'])

        for helper in self.helpers_data:
            display_text = f"{helper['display_name']} [Score: {helper['score']}]"
            
            if helper['warnings']:
                display_text += f" ⚠️ ({helper['warnings']})"

            item = QListWidgetItem(display_text)
            item.setData(1, helper["person_id"])

            if helper["is_team_leader"]:
                item.setForeground(QColor("blue"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            elif helper["has_competence"]:
                item.setForeground(QColor("green"))
            
            if helper['warnings']:
                item.setForeground(QColor("red"))

            self.helper_list.addItem(item)

    def accept(self):
        """Sammelt alle ausgewählten IDs ein."""
        selected_items = self.helper_list.selectedItems()
        if not selected_items:
            return

        self.selected_person_ids = [item.data(1) for item in selected_items if item.data(1)]
        super().accept()