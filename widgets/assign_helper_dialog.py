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
)
from PyQt5.QtGui import QColor, QFont


class AssignHelperDialog(QDialog):
    """Dialog zur Auswahl eines verfügbaren Helfers."""

    def __init__(self, db_manager, shift_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.shift_id = shift_id
        self.selected_person_id = None

        self.setWindowTitle("Helfer zuweisen")
        self.setMinimumSize(450, 500) # Etwas breiter für die Warnungen

        self._init_ui()
        self._populate_list()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche."""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Verfügbare Helfer (sortiert nach Eignung):"))

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

    def _populate_list(self):
        """Füllt die Liste mit verfügbaren Helfern."""
        helpers = self.db_manager.get_available_helpers_for_shift(
            self.shift_id
        )

        if not helpers:
            self.helper_list.addItem("Keine verfügbaren Helfer gefunden.")
            self.helper_list.setEnabled(False)
            return

        for helper in helpers:
            display_text = helper["display_name"]
            
            # Warnungen anhängen
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
            
            # Wenn Warnungen da sind, färben wir den Text rot (oder orange),
            # aber behalten die Info über TL/Kompetenz im Text bei.
            # Priorität: Warnung überschreibt Farbe, damit man es sieht.
            
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