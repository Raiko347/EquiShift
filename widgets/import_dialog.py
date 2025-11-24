# -*- coding: utf-8 -*-
"""
widgets/import_dialog.py

Dialog für den schrittweisen Import von Mitgliedern aus einer Datei.
"""
import pandas as pd
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QWidget,
)
from PyQt5.QtCore import pyqtSignal


class ImportDialog(QDialog):
    """Dialog zur Durchführung des Mitgliederimports."""

    data_changed = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.df = None  # DataFrame für die importierten Daten
        self.column_mapping = {}

        self.setWindowTitle("Mitglieder importieren (Schritt 1/2)")
        self.setMinimumSize(600, 400)

        self._init_ui()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche."""
        self.main_layout = QVBoxLayout(self)

        # --- Schritt 1: Dateiauswahl ---
        self.step1_widget = QWidget()
        step1_layout = QVBoxLayout(self.step1_widget)
        step1_layout.addWidget(QLabel("<b>Schritt 1: Datei auswählen</b>"))
        self.file_path_label = QLabel(
            "Bitte wählen Sie eine Excel- (.xlsx) oder CSV-Datei aus."
        )
        step1_layout.addWidget(self.file_path_label)
        select_file_button = QPushButton("Datei auswählen...")
        select_file_button.clicked.connect(self.select_file)
        step1_layout.addWidget(select_file_button)
        step1_layout.addStretch()
        self.main_layout.addWidget(self.step1_widget)

        # --- Schritt 2: Spaltenzuordnung (anfangs versteckt) ---
        self.step2_widget = QWidget()
        self.step2_widget.setVisible(False)
        step2_layout = QVBoxLayout(self.step2_widget)
        step2_layout.addWidget(QLabel("<b>Schritt 2: Spalten zuordnen</b>"))
        step2_layout.addWidget(
            QLabel(
                "Ordnen Sie die Spalten Ihrer Datei den Datenbankfeldern zu."
            )
        )

        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(
            ["Ihre Spalte", "Datenbankfeld"]
        )
        self.mapping_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        step2_layout.addWidget(self.mapping_table)

        self.import_button = QPushButton("Import starten")
        self.import_button.clicked.connect(self.start_import)
        step2_layout.addWidget(self.import_button)
        self.main_layout.addWidget(self.step2_widget)

    def select_file(self):
        """Öffnet den Dateidialog und lädt die Daten in ein DataFrame."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importdatei auswählen",
            "",
            "Excel-Dateien (*.xlsx);;CSV-Dateien (*.csv)",
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".xlsx"):
                self.df = pd.read_excel(file_path)
            else:
                self.df = pd.read_csv(file_path)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler beim Lesen",
                f"Die Datei konnte nicht gelesen werden:\n{e}",
            )
            return

        self.file_path_label.setText(f"Ausgewählte Datei: {file_path}")
        self.populate_mapping_table()
        self.step1_widget.setVisible(False)
        self.step2_widget.setVisible(True)
        self.setWindowTitle("Mitglieder importieren (Schritt 2/2)")

    def populate_mapping_table(self):
        """Füllt die Zuordnungstabelle mit Spalten aus der Datei."""
        db_fields = [
            "first_name",
            "last_name",
            "display_name",
            "birth_date",
            "street",
            "postal_code",
            "city",
            "email",
            "phone1",
            "phone2",
            "status",
            "entry_date",
            "notes",
        ]
        file_columns = self.df.columns.tolist()

        self.mapping_table.setRowCount(len(db_fields))

        for i, field in enumerate(db_fields):
            self.mapping_table.setItem(i, 1, QTableWidgetItem(field))

            combo = QComboBox()
            combo.addItem("--- Ignorieren ---")
            combo.addItems(file_columns)

            # Versuche, eine passende Spalte automatisch auszuwählen
            if field in file_columns:
                combo.setCurrentText(field)

            self.mapping_table.setCellWidget(i, 0, combo)

    def start_import(self):
        """Sammelt die Zuordnungen und startet den Import-Prozess."""
        mapping = {}
        for i in range(self.mapping_table.rowCount()):
            db_field = self.mapping_table.item(i, 1).text()
            combo = self.mapping_table.cellWidget(i, 0)
            file_column = combo.currentText()
            if file_column != "--- Ignorieren ---":
                mapping[file_column] = db_field

        self.df.rename(columns=mapping, inplace=True)

        required_cols = ["first_name", "last_name"]
        if not all(col in self.df.columns for col in required_cols):
            QMessageBox.critical(
                self,
                "Fehler",
                "Die Spalten 'first_name' und 'last_name' müssen zugeordnet werden.",
            )
            return

        import_data = self.df.to_dict("records")

        added, skipped = self.db_manager.import_members(import_data)

        # INTELLIGENTERE ERFOLGSMELDUNG ---
        message = "Import abgeschlossen.\n\n"
        message += f"{added} Mitglieder wurden neu hinzugefügt.\n"

        if skipped == 0:
            message += "Es wurden keine Duplikate oder fehlerhaften Zeilen in Ihrer Datei gefunden."
        else:
            message += f"{skipped} Mitglieder wurden übersprungen (existierten bereits oder hatten Fehler)."

        QMessageBox.information(self, "Import abgeschlossen", message)

        self.data_changed.emit()
        self.accept()
