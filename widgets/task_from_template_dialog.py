# -*- coding: utf-8 -*-
"""
widgets/task_from_template_dialog.py

Dialog zur schnellen Erstellung von Aufgaben aus Dienst-Typ-Vorlagen.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QCheckBox,
    QDialogButtonBox,
    QLabel,
    QScrollArea,
    QWidget,
)
from PyQt5.QtCore import pyqtSignal


class TaskFromTemplateDialog(QDialog):
    """Dialog zur Auswahl von Dienst-Typen, um daraus Aufgaben zu erstellen."""

    data_changed = pyqtSignal()

    def __init__(self, db_manager, event_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.event_id = event_id
        self.checkboxes = []

        self.setWindowTitle("Aufgaben aus Vorlagen erstellen")
        self.setMinimumWidth(300)

        self._init_ui()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche."""
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(
            QLabel(
                "<b>Wählen Sie die für dieses Event benötigten Aufgaben:</b>"
            )
        )

        # Scrollbereich, falls es viele Dienst-Typen gibt
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        self.checkbox_layout = QVBoxLayout(content_widget)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self._populate_duty_types()

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Ok).setText("Auswahl erstellen")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _populate_duty_types(self):
        """Füllt den Dialog mit Checkboxen für jeden Dienst-Typ."""
        duty_types = self.db_manager.get_all_duty_types()
        for duty_type in duty_types:
            checkbox = QCheckBox(duty_type["name"])
            # Speichere die ID und den Namen in der Checkbox
            checkbox.setProperty("duty_type_id", duty_type["duty_type_id"])
            checkbox.setProperty("duty_type_name", duty_type["name"])
            self.checkbox_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)
        self.checkbox_layout.addStretch()

    def accept(self):
        """Erstellt Aufgaben für alle ausgewählten Dienst-Typen."""
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                duty_type_id = checkbox.property("duty_type_id")
                duty_type_name = checkbox.property("duty_type_name")

                # add_task(event_id, duty_type_id, name, description="")
                self.db_manager.add_task(
                    self.event_id, duty_type_id, duty_type_name
                )

        self.data_changed.emit()
        super().accept()
