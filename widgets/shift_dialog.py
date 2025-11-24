# -*- coding: utf-8 -*-
"""
widgets/shift_dialog.py

Dialog zum Anlegen und Bearbeiten einer Schicht mit Datumsauswahl.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QTimeEdit,
    QSpinBox,
    QDialogButtonBox,
    QMessageBox,
    QDateEdit,
    QAbstractSpinBox
)
from PyQt5.QtCore import QTime, QDate, pyqtSignal


class ShiftDialog(QDialog):
    data_changed = pyqtSignal()

    def __init__(
        self,
        db_manager,
        task_id,
        event_start_date,
        event_end_date,
        shift_id=None,
        parent=None,
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        self.task_id = task_id
        self.shift_id = shift_id

        title = (
            "Schicht bearbeiten" if self.shift_id else "Neue Schicht anlegen"
        )
        self.setWindowTitle(title)
        self.setMinimumWidth(300)

        self._init_ui(event_start_date, event_end_date)

        if self.shift_id:
            self._load_data()

    def _init_ui(self, start_date, end_date):
        """Erstellt die Benutzeroberfläche des Dialogs."""
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.shift_date_input = QDateEdit(calendarPopup=True)
        self.shift_date_input.setDisplayFormat("dd.MM.yyyy")
        self.shift_date_input.setMinimumDate(QDate.fromString(start_date, "yyyy-MM-dd"))
        if end_date:
            self.shift_date_input.setMaximumDate(QDate.fromString(end_date, "yyyy-MM-dd"))
        else:
            self.shift_date_input.setMaximumDate(QDate.fromString(start_date, "yyyy-MM-dd"))
        self.shift_date_input.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))

        self.start_time_input = QTimeEdit()
        self.start_time_input.setDisplayFormat("HH:mm")
        # Die folgende Zeile wurde entfernt:
        # self.start_time_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.start_time_input.setTime(QTime(18, 0))

        self.end_time_input = QTimeEdit()
        self.end_time_input.setDisplayFormat("HH:mm")
        # Die folgende Zeile wurde entfernt:
        # self.end_time_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.end_time_input.setTime(QTime(20, 0))

        self.required_people_input = QSpinBox()
        self.required_people_input.setMinimum(1)
        self.required_people_input.setValue(2)

        form_layout.addRow("Datum der Schicht:", self.shift_date_input)
        form_layout.addRow("Startzeit:", self.start_time_input)
        form_layout.addRow("Endzeit:", self.end_time_input)
        form_layout.addRow("Benötigte Helfer:", self.required_people_input)
        main_layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _load_data(self):
        shift = self.db_manager.get_shift_by_id(self.shift_id)
        if shift:
            self.shift_date_input.setDate(
                QDate.fromString(shift["shift_date"], "yyyy-MM-dd")
            )
            self.start_time_input.setTime(
                QTime.fromString(shift["start_time"], "HH:mm")
            )
            self.end_time_input.setTime(
                QTime.fromString(shift["end_time"], "HH:mm")
            )
            self.required_people_input.setValue(shift["required_people"])

    def accept(self):
        """Validiert und speichert die Daten."""
        start_date = self.shift_date_input.date()
        start_time = self.start_time_input.time()
        end_time = self.end_time_input.time()
        required_people = self.required_people_input.value()

        # KORRIGIERTE VALIDIERUNG: Nur prüfen, ob die Zeiten identisch sind.
        if start_time == end_time:
            QMessageBox.warning(self, "Ungültige Eingabe", "Start- und Endzeit dürfen nicht identisch sein.")
            return

        shift_data = {
            "shift_date": start_date.toString("yyyy-MM-dd"),
            "start_time": start_time.toString("HH:mm"),
            "end_time": end_time.toString("HH:mm"),
            "required_people": required_people
        }

        # Überschneidungsprüfung
        existing_shifts = self.db_manager.get_shifts_for_task(self.task_id)
        for shift in existing_shifts:
            if self.shift_id and self.shift_id == shift['shift_id']:
                continue

            shift_date_obj = QDate.fromString(shift['shift_date'], "yyyy-MM-dd")
            if shift_date_obj == start_date:
                existing_start = QTime.fromString(shift['start_time'], "HH:mm")
                existing_end = QTime.fromString(shift['end_time'], "HH:mm")
                
                # KORRIGIERTE ÜBERSCHNEIDUNGSPRÜFUNG für Mitternacht
                # Normalisiere Zeiten auf einen 48-Stunden-Zeitraum, um Mitternacht zu behandeln
                new_start_secs = start_time.hour() * 3600 + start_time.minute() * 60
                new_end_secs = end_time.hour() * 3600 + end_time.minute() * 60
                if new_end_secs <= new_start_secs: new_end_secs += 24 * 3600

                existing_start_secs = existing_start.hour() * 3600 + existing_start.minute() * 60
                existing_end_secs = existing_end.hour() * 3600 + existing_end.minute() * 60
                if existing_end_secs <= existing_start_secs: existing_end_secs += 24 * 3600

                # Überlappungs-Formel mit Sekunden
                if new_start_secs < existing_end_secs and new_end_secs > existing_start_secs:
                    QMessageBox.warning(self, "Zeitkonflikt",
                                        f"Die neue Schicht überschneidet sich mit einer bestehenden Schicht ({shift['start_time']} - {shift['end_time']}) an diesem Tag.")
                    return

        # Speichern
        if self.shift_id is None:
            shift_data['task_id'] = self.task_id
            self.db_manager.add_shift(**shift_data)
        else:
            self.db_manager.update_shift(self.shift_id, **shift_data)

        self.data_changed.emit()
        super().accept()