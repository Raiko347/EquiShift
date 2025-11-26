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
    QHBoxLayout
)
from PyQt5.QtGui import QColor, QFont


class AssignHelperDialog(QDialog):
    """Dialog zur Auswahl eines verfügbaren Helfers."""

    def __init__(self, db_manager, shift_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.shift_id = shift_id
        self.selected_person_id = None
        
        # Daten zwischenspeichern für Sortierung
        self.helpers_data = []

        self.setWindowTitle("Helfer zuweisen")
        self.setMinimumSize(450, 500)

        self._init_ui()
        self._load_data() # Daten laden (aber noch nicht anzeigen)
        self._update_list() # Liste anzeigen (mit Standard-Sortierung)

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche."""
        layout = QVBoxLayout(self)
        
        # --- Sortier-Optionen ---
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
        # ------------------------

        self.helper_list = QListWidget()
        layout.addWidget(self.helper_list)

        # Legende
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
        """Lädt die Rohdaten aus der DB."""
        self.helpers_data = self.db_manager.get_available_helpers_for_shift(
            self.shift_id
        )

    def _update_list(self):
        """Sortiert die Daten neu und füllt die Liste."""
        self.helper_list.clear()

        if not self.helpers_data:
            self.helper_list.addItem("Keine verfügbaren Helfer gefunden.")
            self.helper_list.setEnabled(False)
            return

        sort_mode = self.sort_combo.currentIndex()
        
        # Sortier-Logik
        if sort_mode == 0: # Eignung (Standard)
            self.helpers_data.sort(key=lambda x: (
                -x['is_team_leader'],
                -x['has_competence'],
                -(len(x['warnings']) == 0),
                x['score'], # Bei gleicher Eignung: Wer hat weniger Punkte?
                x['display_name']
            ))
        elif sort_mode == 1: # Score aufsteigend (Die Faulen zuerst)
            self.helpers_data.sort(key=lambda x: (x['score'], x['display_name']))
        elif sort_mode == 2: # Score absteigend (Die Fleißigen zuerst)
            self.helpers_data.sort(key=lambda x: (-x['score'], x['display_name']))
        elif sort_mode == 3: # Name A-Z
            self.helpers_data.sort(key=lambda x: x['display_name'])

        # Liste befüllen
        for helper in self.helpers_data:
            # Text bauen: Name [Score: X]
            display_text = f"{helper['display_name']} [Score: {helper['score']}]"
            
            if helper['warnings']:
                display_text += f" ⚠️ ({helper['warnings']})"

            item = QListWidgetItem(display_text)
            item.setData(1, helper["person_id"])

            # Farben setzen
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
        """Setzt die ID des ausgewählten Helfers."""
        selected_item = self.helper_list.currentItem()
        if not selected_item or not selected_item.data(1):
            return

        self.selected_person_id = selected_item.data(1)
        super().accept()