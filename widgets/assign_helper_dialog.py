# -*- coding: utf-8 -*-
"""
widgets/assign_helper_dialog.py

Dialog zur Auswahl und Zuweisung eines Helfers zu einer Schicht.
Enthält Sicherheitslogik (Jugendschutz-Sperre).
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
    QAbstractItemView
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt


class AssignHelperDialog(QDialog):
    """Dialog zur Auswahl eines verfügbaren Helfers."""

    def __init__(self, db_manager, shift_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.shift_id = shift_id
        self.selected_person_ids = []
        
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
        self.helper_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Signal verbinden, um Button zu sperren/entsperren
        self.helper_list.itemSelectionChanged.connect(self._check_selection)
        layout.addWidget(self.helper_list)

        legend_label = QLabel(
            "<font color='blue'><b>Blau: Teamleiter</b></font><br>"
            "<font color='green'><b>Grün: Kompetenz vorhanden</b></font><br>"
            "<font color='red'>Rot: Warnung (Pausen / Überlastung / Jugendschutz)</font>"
        )
        layout.addWidget(legend_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("Zuweisen")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Warn-Label für gesperrte Auswahl
        self.block_label = QLabel("")
        self.block_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.block_label)

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
            
            # Prüfen auf Jugendschutz
            is_underage = "Zu jung" in helper['warnings']
            
            if helper['warnings']:
                display_text += f" ⚠️ ({helper['warnings']})"

            item = QListWidgetItem(display_text)
            item.setData(1, helper["person_id"])
            
            # Sperr-Status speichern (UserRole + 1)
            item.setData(Qt.UserRole + 1, is_underage)

            if helper["is_team_leader"]:
                item.setForeground(QColor("blue"))
                font = item.font(); font.setBold(True); item.setFont(font)
            elif helper["has_competence"]:
                item.setForeground(QColor("green"))
            
            if helper['warnings']:
                item.setForeground(QColor("red"))
                
            if is_underage:
                item.setForeground(QColor("darkred"))

            self.helper_list.addItem(item)
            
        self._check_selection()

    def _check_selection(self):
        """Prüft, ob die Auswahl zulässig ist (Jugendschutz)."""
        selected_items = self.helper_list.selectedItems()
        ok_button = self.button_box.button(QDialogButtonBox.Ok)
        
        if not selected_items:
            ok_button.setEnabled(False)
            self.block_label.setText("")
            return

        blocked = False
        for item in selected_items:
            if item.data(Qt.UserRole + 1): # Ist is_underage True?
                blocked = True
                break
        
        ok_button.setEnabled(not blocked)
        
        if blocked:
            self.block_label.setText("⛔ Auswahl enthält minderjährige Person für diesen Dienst!")
        else:
            self.block_label.setText("")

    def accept(self):
        selected_items = self.helper_list.selectedItems()
        if not selected_items:
            return

        self.selected_person_ids = [item.data(1) for item in selected_items if item.data(1)]
        super().accept()