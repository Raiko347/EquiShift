# -*- coding: utf-8 -*-
"""
widgets/stammdaten_widget.py

Widget zur Verwaltung der Mitglieder-Stammdaten.
"""

import os

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QDialog,
)
from PyQt5.QtCore import Qt
from .person_dialog import PersonDialog
from .import_dialog import ImportDialog
from utils.exporter import Exporter


class StammdatenWidget(QWidget):
    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.settings = settings
        self._init_ui()
        self.load_persons_data()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche für dieses Widget."""
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        title_label = QLabel("Stammdaten der Mitglieder")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        self.template_button = QPushButton("Vorlage herunterladen")
        self.import_button = QPushButton("Mitglieder importieren...")
        self.export_button = QPushButton("Mitglieder exportieren...")
        top_layout.addWidget(self.template_button)
        top_layout.addWidget(self.import_button)
        top_layout.addWidget(self.export_button)
        layout.addLayout(top_layout)

        self.persons_table = QTableWidget()
        self.column_map = {
            "ID": "person_id", "Status": "status", "Vorname": "first_name",
            "Nachname": "last_name", "Anzeigename": "display_name",
            "Geburtsdatum": "birth_date", "Straße": "street", "PLZ": "postal_code",
            "Ort": "city", "E-Mail": "email", "Telefon 1": "phone1",
            "Telefon 2": "phone2", "Eintritt": "entry_date", "Austritt": "exit_date",
            "Notizen": "notes"
        }
        self.persons_table.setColumnCount(len(self.column_map))
        self.persons_table.setHorizontalHeaderLabels(self.column_map.keys())
        self.persons_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.persons_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.persons_table.verticalHeader().setVisible(False)
        self.persons_table.setAlternatingRowColors(True)
        self.persons_table.hideColumn(0)
        
        # NEU: Sortierung durch Klick auf den Header erlauben
        self.persons_table.setSortingEnabled(True)
        
        layout.addWidget(self.persons_table)

        bottom_layout = QHBoxLayout()
        self.add_button = QPushButton("Neues Mitglied anlegen")
        self.edit_button = QPushButton("Mitglied bearbeiten / Einschränkungen")
        self.delete_button = QPushButton("Mitglied löschen")
        bottom_layout.addWidget(self.add_button)
        bottom_layout.addWidget(self.edit_button)
        bottom_layout.addWidget(self.delete_button)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

        self.add_button.clicked.connect(self.add_person)
        self.edit_button.clicked.connect(self.edit_person)
        self.delete_button.clicked.connect(self.delete_person)
        self.template_button.clicked.connect(self.download_template)
        self.import_button.clicked.connect(self.import_members)
        self.export_button.clicked.connect(self.export_members)

    def _format_date_for_display(self, date_str_from_db):
        if not date_str_from_db:
            return ""
        try:
            date_obj = datetime.strptime(date_str_from_db, "%Y-%m-%d")
            return date_obj.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            return date_str_from_db

    def load_persons_data(self):
        """Lädt alle Personendaten aus der Datenbank und füllt die Tabelle."""
        # Merke dir die aktuelle Sortierung
        header = self.persons_table.horizontalHeader()
        sort_column = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder()

        # Blockiere die Sortierung während des Füllens, um Performance zu verbessern
        self.persons_table.setSortingEnabled(False)

        persons = self.db_manager.get_all_persons()
        self.persons_table.setRowCount(len(persons))
        date_columns = ['birth_date', 'entry_date', 'exit_date']
        for row_idx, person in enumerate(persons):
            for col_idx, db_key in enumerate(self.column_map.values()):
                value = person[db_key]
                item_text = self._format_date_for_display(value) if db_key in date_columns else (str(value) if value is not None else "")
                self.persons_table.setItem(row_idx, col_idx, QTableWidgetItem(item_text))
        
        # Aktiviere die Sortierung wieder
        self.persons_table.setSortingEnabled(True)
        
        # Stelle die ursprüngliche Sortierung wieder her
        self.persons_table.sortByColumn(sort_column, sort_order)

        self.persons_table.resizeColumnsToContents()

    def add_person(self):
        dialog = PersonDialog(self.db_manager, parent=self)
        dialog.data_changed.connect(self.load_persons_data)
        dialog.exec_()

    def edit_person(self):
        selected_row = self.persons_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Auswahl erforderlich",
                "Bitte wählen Sie zuerst ein Mitglied aus der Liste aus.",
            )
            return
        person_id = int(self.persons_table.item(selected_row, 0).text())
        dialog = PersonDialog(
            self.db_manager, person_id=person_id, parent=self
        )
        dialog.data_changed.connect(self.load_persons_data)
        dialog.exec_()

    def delete_person(self):
        selected_row = self.persons_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Auswahl erforderlich",
                "Bitte wählen Sie zuerst ein Mitglied aus der Liste aus.",
            )
            return
        person_id = int(self.persons_table.item(selected_row, 0).text())
        display_name = self.persons_table.item(selected_row, 4).text()
        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            f"Sind Sie sicher, dass Sie das Mitglied '{display_name}' unwiderruflich löschen möchten?\n\n"
            "Alle zugehörigen Dienst-Einschränkungen und Schicht-Zuweisungen werden ebenfalls entfernt.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db_manager.delete_person(person_id)
            self.load_persons_data()
            QMessageBox.information(
                self,
                "Erfolg",
                f"Das Mitglied '{display_name}' wurde gelöscht.",
            )

    def download_template(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Import-Vorlage speichern",
            "Mitglieder_Import_Vorlage.xlsx",
            "Excel-Datei (*.xlsx)",
        )
        if not file_path:
            return
        success = Exporter.create_member_template(file_path)
        if success:
            QMessageBox.information(
                self,
                "Vorlage gespeichert",
                f"Die Vorlagedatei wurde erfolgreich unter\n{file_path}\ngespeichert.",
            )
        else:
            QMessageBox.critical(
                self, "Fehler", "Die Vorlage konnte nicht erstellt werden."
            )

    def export_members(self):
        """Exportiert die aktuelle Mitgliederliste inkl. Kompetenzen in eine XLSX-Datei."""
        # Rufe die neue, umfassende DB-Methode auf
        all_members, duty_type_names = self.db_manager.get_all_members_with_details()
        
        if not all_members:
            QMessageBox.information(self, "Keine Daten", "Es sind keine Mitglieder zum Exportieren vorhanden.")
            return

        last_path = self.settings.get_last_export_path()
        default_filename = os.path.join(last_path, "Vereinsmitglieder_Komplett.xlsx")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Mitgliederliste exportieren",
            default_filename,
            "Excel-Datei (*.xlsx)"
        )

        if not file_path:
            return
        
        self.settings.set_last_export_path(os.path.dirname(file_path))

        # Übergebe beide Teile (Daten und Spaltennamen) an den Exporter
        success = Exporter.export_members_to_xlsx(all_members, duty_type_names, file_path)

        if success:
            QMessageBox.information(self, "Export erfolgreich",
                                    f"Die Mitgliederliste wurde erfolgreich nach\n{file_path}\ngespeichert.")
        else:
            QMessageBox.critical(self, "Fehler", "Die Mitgliederliste konnte nicht exportiert werden.")

    def import_members(self):
        dialog = ImportDialog(self.db_manager, self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.load_persons_data()
