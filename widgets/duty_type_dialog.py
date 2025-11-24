# -*- coding: utf-8 -*-
"""
widgets/duty_type_dialog.py

Dialog zum Anlegen und Bearbeiten eines Dienst-Typs.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt5.QtCore import pyqtSignal


class DutyTypeDialog(QDialog):
    """Ein Dialogfenster zur Eingabe von Dienst-Typ-Daten."""

    data_changed = pyqtSignal()

    def __init__(self, db_manager, duty_type_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.duty_type_id = duty_type_id  # KORREKTUR

        title = (
            "Dienst-Typ bearbeiten"
            if self.duty_type_id
            else "Neuen Dienst-Typ anlegen"
        )
        self.setWindowTitle(title)
        self.setMinimumWidth(350)

        self._init_ui()

        if self.duty_type_id:
            self._load_data()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche des Dialogs."""
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(80)

        form_layout.addRow("Name*:", self.name_input)
        form_layout.addRow("Beschreibung:", self.description_input)
        main_layout.addLayout(form_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Save).setText("Speichern")
        button_box.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _load_data(self):
        """Lädt die Daten des Dienst-Typs und füllt die Felder."""
        # Wir brauchen eine neue Methode im DB-Manager
        duty_type = self.db_manager.get_duty_type_by_id(self.duty_type_id)
        if duty_type:
            self.name_input.setText(duty_type["name"])
            self.description_input.setPlainText(duty_type["description"])

    def accept(self):
        """Validiert und speichert die Daten."""
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()

        if not name:
            QMessageBox.warning(
                self, "Fehlende Eingabe", "Der Name ist ein Pflichtfeld."
            )
            return

        if self.duty_type_id is None:
            # Wir brauchen eine neue Methode im DB-Manager
            self.db_manager.add_duty_type(name, description)
        else:
            # Wir brauchen eine neue Methode im DB-Manager
            self.db_manager.update_duty_type(
                self.duty_type_id, name, description
            )

        self.data_changed.emit()
        super().accept()
