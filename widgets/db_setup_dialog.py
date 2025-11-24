# -*- coding: utf-8 -*-
"""
widgets/db_setup_dialog.py

Dialog, der beim ersten Start angezeigt wird, um eine Datenbank zu erstellen oder auszuwählen.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QFileDialog,
)


class DbSetupDialog(QDialog):
    """Dialog zur Einrichtung der Datenbankverbindung."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_path = ""
        self.create_demo = False  # NEU: Merker für Demodaten
        
        self.setWindowTitle("Datenbank einrichten")
        self.setModal(True)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Willkommen beim EquiShift!"))
        layout.addWidget(QLabel("Bitte wählen Sie eine Option, um zu starten:"))

        # Button 1: Leer
        new_db_button = QPushButton("Neue, leere Datenbank erstellen")
        new_db_button.clicked.connect(self.create_new_db)
        layout.addWidget(new_db_button)

        # Button 2: Demo (NEU)
        demo_db_button = QPushButton("Neue Datenbank mit Demodaten erstellen")
        demo_db_button.clicked.connect(self.create_demo_db)
        layout.addWidget(demo_db_button)

        # Button 3: Öffnen
        open_db_button = QPushButton("Bestehende Datenbankdatei öffnen")
        open_db_button.clicked.connect(self.open_existing_db)
        layout.addWidget(open_db_button)

    def create_new_db(self):
        """Öffnet einen Dialog zum Speichern einer neuen DB-Datei."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Neue Datenbank speichern",
            "EquiShift.db",
            "Datenbankdateien (*.db)",
        )
        if path:
            self.db_path = path
            self.create_demo = False # Keine Demo
            self.accept()

    def create_demo_db(self):
        """Öffnet Dialog zum Speichern und setzt das Demo-Flag."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Demo-Datenbank speichern",
            "EquiShift_demo.db",
            "Datenbankdateien (*.db)",
        )
        if path:
            self.db_path = path
            self.create_demo = True # WICHTIG: Demo anfordern
            self.accept()

    def open_existing_db(self):
        """Öffnet einen Dialog zum Auswählen einer bestehenden DB-Datei."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Bestehende Datenbank öffnen", "", "Datenbankdateien (*.db)"
        )
        if path:
            self.db_path = path
            self.create_demo = False
            self.accept()