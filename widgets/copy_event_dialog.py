# -*- coding: utf-8 -*-
"""
widgets/copy_event_dialog.py

Dialog zum Kopieren eines Events mit verschiedenen Modi.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDateEdit,
    QDialogButtonBox,
    QGroupBox,
    QRadioButton,
    QMessageBox,
)
from PyQt5.QtCore import QDate


class CopyEventDialog(QDialog):
    """Dialog zur Eingabe der Parameter für das Kopieren eines Events."""

    def __init__(self, source_event_name, source_start_date, parent=None):
        super().__init__(parent)
        self.source_event_name = source_event_name
        self.source_start_date = source_start_date
        
        self.new_name = ""
        self.new_start_date = ""
        self.copy_mode = "structure" # Default

        self.setWindowTitle("Event kopieren")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setText(f"Kopie von {self.source_event_name}")
        
        self.date_input = QDateEdit(calendarPopup=True)
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        # Standard: Das alte Datum + 1 Jahr (typischer Vereins-Zyklus)
        if self.source_start_date:
            old_date = QDate.fromString(self.source_start_date, "yyyy-MM-dd")
            self.date_input.setDate(old_date.addYears(1))
        else:
            self.date_input.setDate(QDate.currentDate())

        form_layout.addRow("Neuer Name:", self.name_input)
        form_layout.addRow("Neues Startdatum:", self.date_input)
        layout.addLayout(form_layout)

        # --- Modi Auswahl ---
        mode_group = QGroupBox("Was soll kopiert werden?")
        mode_layout = QVBoxLayout()
        
        self.rb_structure = QRadioButton("Nur Struktur (Aufgaben)")
        self.rb_structure.setToolTip("Kopiert nur das Event und die definierten Aufgaben (z.B. 'Bar', 'Aufbau').")
        
        self.rb_shifts = QRadioButton("Struktur & Schichten")
        self.rb_shifts.setToolTip("Kopiert Aufgaben und Schichten. Die Schicht-Daten werden entsprechend verschoben.")
        self.rb_shifts.setChecked(True) # Sinnvoller Standard
        
        self.rb_full = QRadioButton("Komplett (Struktur, Schichten & Helfer)")
        self.rb_full.setToolTip("Kopiert alles, inklusive der Helfer-Zuweisungen (Status wird auf 'Geplant' gesetzt).")

        mode_layout.addWidget(self.rb_structure)
        mode_layout.addWidget(self.rb_shifts)
        mode_layout.addWidget(self.rb_full)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Kopieren starten")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Fehlende Eingabe", "Bitte geben Sie einen Namen für das neue Event ein.")
            return
        
        self.new_name = self.name_input.text().strip()
        self.new_start_date = self.date_input.date().toString("yyyy-MM-dd")
        
        if self.rb_structure.isChecked():
            self.copy_mode = "structure"
        elif self.rb_shifts.isChecked():
            self.copy_mode = "shifts"
        else:
            self.copy_mode = "full"
            
        super().accept()