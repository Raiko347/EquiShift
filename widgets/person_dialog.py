# -*- coding: utf-8 -*-
"""
widgets/person_dialog.py

Dialog zum Anlegen und Bearbeiten eines Mitglieds, inklusive der Verwaltung
von Kompetenzen, Teamleiter-Status und Dienst-Einschränkungen.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QDialogButtonBox,
    QMessageBox,
    QGroupBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QWidget,
    QHBoxLayout,
)
from PyQt5.QtCore import QDate, pyqtSignal, Qt


class PersonDialog(QDialog):
    """Ein Dialogfenster zur Eingabe und Bearbeitung von Personendaten."""

    data_changed = pyqtSignal()

    def __init__(self, db_manager, person_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.person_id = person_id
        self.duty_type_checkboxes = []  # Für Einschränkungen
        self.competency_widgets = {}  # Für Kompetenzen

        title = (
            "Mitglied bearbeiten"
            if self.person_id
            else "Neues Mitglied anlegen"
        )
        self.setWindowTitle(title)
        self.setMinimumWidth(500)

        self._init_ui()

        if self.person_id:
            self._load_person_data()

        self._update_all_states()  # Initialer Logik-Check

    def _init_ui(self):
        """Erstellt die komplette Benutzeroberfläche des Dialogs."""
        main_layout = QVBoxLayout(self)

        # --- Formular für persönliche Daten ---
        personal_data_groupbox = QGroupBox("Persönliche Daten")
        form_layout = QFormLayout()
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.display_name_input = QLineEdit()
        self.birth_date_input = QDateEdit(calendarPopup=True)
        self.birth_date_input.setDisplayFormat("dd.MM.yyyy")
        self.street_input = QLineEdit()
        self.postal_code_input = QLineEdit()
        self.city_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone1_input = QLineEdit()
        self.phone2_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(["Aktiv", "Passiv", "Ruht", "Austritt"])
        self.entry_date_input = QDateEdit(calendarPopup=True)
        self.entry_date_input.setDisplayFormat("dd.MM.yyyy")
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(80)

        form_layout.addRow("Vorname*:", self.first_name_input)
        form_layout.addRow("Nachname*:", self.last_name_input)
        form_layout.addRow("Anzeigename*:", self.display_name_input)
        form_layout.addRow("Geburtsdatum:", self.birth_date_input)
        form_layout.addRow("Straße:", self.street_input)
        form_layout.addRow("PLZ:", self.postal_code_input)
        form_layout.addRow("Ort:", self.city_input)
        form_layout.addRow("E-Mail:", self.email_input)
        form_layout.addRow("Telefon 1:", self.phone1_input)
        form_layout.addRow("Telefon 2:", self.phone2_input)
        form_layout.addRow("Status:", self.status_input)
        form_layout.addRow("Eintrittsdatum:", self.entry_date_input)
        form_layout.addRow("Notizen:", self.notes_input)
        personal_data_groupbox.setLayout(form_layout)
        main_layout.addWidget(personal_data_groupbox)

        # --- Box für Kompetenzen ---
        competency_groupbox = QGroupBox("Kompetenzen & Teamleiter-Status")
        competency_layout = QVBoxLayout()
        self.competency_table = QTableWidget()
        self.competency_table.setColumnCount(3)
        self.competency_table.setHorizontalHeaderLabels(
            ["Dienst", "Kompetenz", "Teamleiter"]
        )
        self.competency_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.competency_table.verticalHeader().setVisible(False)
        competency_layout.addWidget(self.competency_table)
        competency_groupbox.setLayout(competency_layout)
        main_layout.addWidget(competency_groupbox)

        # --- Box für Einschränkungen ---
        restrictions_groupbox = QGroupBox("Dienst-Einschränkungen (max. 3)")
        self.restrictions_layout = QVBoxLayout()
        restrictions_groupbox.setLayout(self.restrictions_layout)
        main_layout.addWidget(restrictions_groupbox)

        self._populate_duties()  # Füllt Kompetenzen und Einschränkungen

        # --- Buttons ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Save).setText("Speichern")
        button_box.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _populate_duties(self):
        """Füllt die Kompetenztabelle und die Einschränkungs-Checkboxes."""
        duty_types = self.db_manager.get_all_duty_types()
        self.competency_table.setRowCount(len(duty_types))

        for idx, duty_type in enumerate(duty_types):
            duty_id = duty_type["duty_type_id"]
            duty_name = duty_type["name"]

            # 1. Kompetenztabelle füllen
            name_item = QTableWidgetItem(duty_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.competency_table.setItem(idx, 0, name_item)

            cb_competent = QCheckBox()
            cb_teamleader = QCheckBox()

            # Checkboxen in zentrierten Layouts platzieren
            cell_widget_competent = QWidget()
            layout_c = QHBoxLayout(cell_widget_competent)
            layout_c.addWidget(cb_competent)
            layout_c.setAlignment(Qt.AlignCenter)
            layout_c.setContentsMargins(0, 0, 0, 0)
            self.competency_table.setCellWidget(idx, 1, cell_widget_competent)

            cell_widget_tl = QWidget()
            layout_tl = QHBoxLayout(cell_widget_tl)
            layout_tl.addWidget(cb_teamleader)
            layout_tl.setAlignment(Qt.AlignCenter)
            layout_tl.setContentsMargins(0, 0, 0, 0)
            self.competency_table.setCellWidget(idx, 2, cell_widget_tl)

            self.competency_widgets[duty_id] = (cb_competent, cb_teamleader)

            # 2. Einschränkungs-Checkboxes füllen
            cb_restriction = QCheckBox(duty_name)
            cb_restriction.setProperty("duty_type_id", duty_id)
            self.restrictions_layout.addWidget(cb_restriction)
            self.duty_type_checkboxes.append(cb_restriction)

            # 3. Signale verbinden, um die Logik zu triggern
            cb_competent.stateChanged.connect(self._update_all_states)
            cb_restriction.stateChanged.connect(self._update_all_states)

    def _load_person_data(self):
        """Lädt die Daten des Mitglieds und füllt alle Formularfelder."""
        person = self.db_manager.get_person_by_id(self.person_id)
        if not person:
            QMessageBox.critical(self, "Fehler", "Mitglied nicht gefunden.")
            self.reject()
            return

        self.first_name_input.setText(person["first_name"])
        self.last_name_input.setText(person["last_name"])
        self.display_name_input.setText(person["display_name"])
        self.street_input.setText(person["street"])
        self.postal_code_input.setText(person["postal_code"])
        self.city_input.setText(person["city"])
        self.email_input.setText(person["email"])
        self.phone1_input.setText(person["phone1"])
        self.phone2_input.setText(person["phone2"])
        self.notes_input.setPlainText(person["notes"])
        self.status_input.setCurrentText(person["status"])
        if person["birth_date"]:
            self.birth_date_input.setDate(
                QDate.fromString(person["birth_date"], "yyyy-MM-dd")
            )
        if person["entry_date"]:
            self.entry_date_input.setDate(
                QDate.fromString(person["entry_date"], "yyyy-MM-dd")
            )

        competencies = self.db_manager.get_person_competencies(self.person_id)
        for duty_id, (cb_c, cb_tl) in self.competency_widgets.items():
            if duty_id in competencies:
                cb_c.setChecked(True)
                if competencies[duty_id]:
                    cb_tl.setChecked(True)

        restrictions = self.db_manager.get_person_restrictions(self.person_id)
        for cb_r in self.duty_type_checkboxes:
            if cb_r.property("duty_type_id") in restrictions:
                cb_r.setChecked(True)

    def _update_all_states(self):
        """Zentrale Logik-Funktion, die alle Abhängigkeiten prüft und UI-Elemente (de)aktiviert."""
        checked_restrictions = [
            cb for cb in self.duty_type_checkboxes if cb.isChecked()
        ]
        enable_restrictions = len(checked_restrictions) < 3
        for cb in self.duty_type_checkboxes:
            if cb not in checked_restrictions:
                cb.setEnabled(enable_restrictions)

        for duty_id, (cb_c, cb_tl) in self.competency_widgets.items():
            restriction_cb = next(
                cb
                for cb in self.duty_type_checkboxes
                if cb.property("duty_type_id") == duty_id
            )

            if restriction_cb.isChecked():
                cb_c.setChecked(False)
                cb_c.setEnabled(False)
                cb_tl.setChecked(False)
                cb_tl.setEnabled(False)
            else:
                cb_c.setEnabled(True)
                cb_tl.setEnabled(cb_c.isChecked())

    def accept(self):
        """Validiert und speichert alle Daten (persönlich, Einschränkungen, Kompetenzen)."""
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        display_name = self.display_name_input.text().strip()

        if not first_name or not last_name or not display_name:
            QMessageBox.warning(
                self,
                "Fehlende Eingabe",
                "Vorname, Nachname und Anzeigename sind Pflichtfelder.",
            )
            return

        person_data = {
            "first_name": first_name,
            "last_name": last_name,
            "display_name": display_name,
            "birth_date": self.birth_date_input.date().toString("yyyy-MM-dd"),
            "street": self.street_input.text().strip(),
            "postal_code": self.postal_code_input.text().strip(),
            "city": self.city_input.text().strip(),
            "email": self.email_input.text().strip(),
            "phone1": self.phone1_input.text().strip(),
            "phone2": self.phone2_input.text().strip(),
            "status": self.status_input.currentText(),
            "entry_date": self.entry_date_input.date().toString("yyyy-MM-dd"),
            "notes": self.notes_input.toPlainText().strip(),
        }

        selected_restriction_ids = [
            cb.property("duty_type_id")
            for cb in self.duty_type_checkboxes
            if cb.isChecked()
        ]

        selected_competencies = {}
        for duty_id, (cb_c, cb_tl) in self.competency_widgets.items():
            if cb_c.isChecked():
                selected_competencies[duty_id] = 1 if cb_tl.isChecked() else 0

        if self.person_id is None:
            new_id = self.db_manager.add_person(**person_data)
            self.db_manager.set_person_restrictions(
                new_id, selected_restriction_ids
            )
            self.db_manager.set_person_competencies(
                new_id, selected_competencies
            )
        else:
            self.db_manager.update_person(self.person_id, **person_data)
            self.db_manager.set_person_restrictions(
                self.person_id, selected_restriction_ids
            )
            self.db_manager.set_person_competencies(
                self.person_id, selected_competencies
            )

        self.data_changed.emit()
        super().accept()
