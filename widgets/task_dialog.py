# -*- coding: utf-8 -*-
"""
widgets/task_dialog.py

Dialog zum Anlegen und Bearbeiten einer Aufgabe für ein Event.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt5.QtCore import pyqtSignal


class TaskDialog(QDialog):
    """Ein Dialogfenster zur Eingabe von Aufgabendaten."""

    data_changed = pyqtSignal()

    def __init__(self, db_manager, event_id, task_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.event_id = event_id
        self.task_id = task_id

        title = (
            "Aufgabe bearbeiten" if self.task_id else "Neue Aufgabe anlegen"
        )
        self.setWindowTitle(title)
        self.setMinimumWidth(350)

        self._init_ui()

        if self.task_id:
            self._load_data()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche des Dialogs."""
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.duty_type_combo = QComboBox()
        self._populate_duty_types()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("z.B. 'Cocktailbar im Foyer'")

        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(80)

        form_layout.addRow("Dienst-Typ*:", self.duty_type_combo)
        form_layout.addRow("Spezifischer Name*:", self.name_input)
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

    def _populate_duty_types(self):
        """Füllt das Dropdown-Menü mit allen verfügbaren Dienst-Typen."""
        self.duty_type_combo.addItem("--- Bitte wählen ---", -1)
        duty_types = self.db_manager.get_all_duty_types()
        if duty_types:
            for duty_type in duty_types:
                self.duty_type_combo.addItem(
                    duty_type["name"], duty_type["duty_type_id"]
                )

    def _load_data(self):
        """Lädt die Daten der Aufgabe und füllt die Felder."""
        task = self.db_manager.get_task_by_id(self.task_id)
        if task:
            self.name_input.setText(task["name"])
            self.description_input.setPlainText(task["description"])

            index = self.duty_type_combo.findData(task["duty_type_id"])
            if index != -1:
                self.duty_type_combo.setCurrentIndex(index)

    def accept(self):
        """Validiert und speichert die Daten."""
        duty_type_id = self.duty_type_combo.currentData()
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()

        if duty_type_id == -1 or not name:
            QMessageBox.warning(
                self,
                "Fehlende Eingabe",
                "Bitte wählen Sie einen Dienst-Typ und geben Sie einen Namen an.",
            )
            return

        task_data = {
            "duty_type_id": duty_type_id,
            "name": name,
            "description": description,
        }

        if self.task_id is None:
            task_data["event_id"] = self.event_id
            self.db_manager.add_task(**task_data)
        else:
            self.db_manager.update_task(self.task_id, **task_data)

        self.data_changed.emit()
        super().accept()
