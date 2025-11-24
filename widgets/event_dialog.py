# -*- coding: utf-8 -*-
"""
widgets/event_dialog.py

Dialog zum Anlegen und Bearbeiten eines Events inkl. Anhängen.
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit,
    QDialogButtonBox, QMessageBox, QTabWidget, QWidget, QListWidget,
    QHBoxLayout, QPushButton, QFileDialog, QListWidgetItem, QLabel
)
from PyQt5.QtCore import QDate, pyqtSignal, Qt

class EventDialog(QDialog):
    data_changed = pyqtSignal()

    def __init__(self, db_manager, event_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.event_id = event_id
        self.old_status = None
        
        # Liste für Anhänge (temporär im Speicher)
        # Format: [{'path': 'C:/...', 'name': 'hygiene.pdf'}]
        self.attachments = [] 

        title = "Event bearbeiten" if self.event_id else "Neues Event anlegen"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._init_ui()

        if self.event_id:
            self._load_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Tabs erstellen ---
        self.tabs = QTabWidget()
        self.tab_basics = QWidget()
        self.tab_attachments = QWidget()
        
        self.tabs.addTab(self.tab_basics, "Basisdaten")
        self.tabs.addTab(self.tab_attachments, "Anhänge (PDF)")
        main_layout.addWidget(self.tabs)

        # --- Tab 1: Basisdaten ---
        basics_layout = QFormLayout(self.tab_basics)
        self.name_input = QLineEdit()
        self.start_date_input = QDateEdit(calendarPopup=True)
        self.start_date_input.setDisplayFormat("dd.MM.yyyy")
        self.start_date_input.setDate(QDate.currentDate())
        self.end_date_input = QDateEdit(calendarPopup=True)
        self.end_date_input.setDisplayFormat("dd.MM.yyyy")
        self.end_date_input.setDate(QDate.currentDate().addDays(3))
        self.status_input = QComboBox()
        self.status_input.addItems(["In Planung", "Aktiv", "Abgeschlossen", "Abgesagt"])

        basics_layout.addRow("Name*:", self.name_input)
        basics_layout.addRow("Startdatum:", self.start_date_input)
        basics_layout.addRow("Enddatum (optional):", self.end_date_input)
        basics_layout.addRow("Status:", self.status_input)

        # --- Tab 2: Anhänge ---
        att_layout = QVBoxLayout(self.tab_attachments)
        att_layout.addWidget(QLabel("Diese Dokumente werden an den Dienstplan angehängt:"))
        
        self.att_list = QListWidget()
        att_layout.addWidget(self.att_list)
        
        btn_layout = QHBoxLayout()
        self.btn_add_att = QPushButton("Hinzufügen...")
        self.btn_remove_att = QPushButton("Entfernen")
        self.btn_up_att = QPushButton("▲")
        self.btn_down_att = QPushButton("▼")
        
        self.btn_add_att.clicked.connect(self.add_attachment)
        self.btn_remove_att.clicked.connect(self.remove_attachment)
        self.btn_up_att.clicked.connect(self.move_attachment_up)
        self.btn_down_att.clicked.connect(self.move_attachment_down)
        
        btn_layout.addWidget(self.btn_add_att)
        btn_layout.addWidget(self.btn_remove_att)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_up_att)
        btn_layout.addWidget(self.btn_down_att)
        att_layout.addLayout(btn_layout)

        # --- Buttons unten ---
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).setText("Speichern")
        button_box.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _load_data(self):
        # 1. Event Daten
        event = self.db_manager.get_event_by_id(self.event_id)
        if event:
            self.name_input.setText(event["name"])
            self.status_input.setCurrentText(event["status"])
            self.old_status = event["status"]
            if event["start_date"]:
                self.start_date_input.setDate(QDate.fromString(event["start_date"], "yyyy-MM-dd"))
            if event["end_date"]:
                self.end_date_input.setDate(QDate.fromString(event["end_date"], "yyyy-MM-dd"))

        # 2. Anhänge laden
        db_attachments = self.db_manager.get_attachments_for_event(self.event_id)
        if db_attachments:
            for att in db_attachments:
                self.attachments.append({
                    'path': att['file_path'],
                    'name': os.path.basename(att['file_path'])
                })
            self._refresh_att_list()

    def _refresh_att_list(self):
        self.att_list.clear()
        for att in self.attachments:
            item = QListWidgetItem(att['name'])
            item.setToolTip(att['path'])
            # Prüfen ob Datei existiert
            if not os.path.exists(att['path']):
                item.setForeground(Qt.red)
                item.setText(f"{att['name']} (Datei fehlt!)")
            self.att_list.addItem(item)

    def add_attachment(self):
        path, _ = QFileDialog.getOpenFileName(self, "PDF auswählen", "", "PDF-Dateien (*.pdf)")
        if path:
            self.attachments.append({
                'path': path,
                'name': os.path.basename(path)
            })
            self._refresh_att_list()

    def remove_attachment(self):
        row = self.att_list.currentRow()
        if row >= 0:
            del self.attachments[row]
            self._refresh_att_list()

    def move_attachment_up(self):
        row = self.att_list.currentRow()
        if row > 0:
            self.attachments[row], self.attachments[row-1] = self.attachments[row-1], self.attachments[row]
            self._refresh_att_list()
            self.att_list.setCurrentRow(row-1)

    def move_attachment_down(self):
        row = self.att_list.currentRow()
        if row < len(self.attachments) - 1 and row >= 0:
            self.attachments[row], self.attachments[row+1] = self.attachments[row+1], self.attachments[row]
            self._refresh_att_list()
            self.att_list.setCurrentRow(row+1)

    def accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehlende Eingabe", "Der Name ist ein Pflichtfeld.")
            return

        start_date = self.start_date_input.date()
        end_date = self.end_date_input.date()
        new_status = self.status_input.currentText()

        if end_date.isValid() and end_date < start_date:
            QMessageBox.warning(self, "Ungültiges Datum", "Das Enddatum darf nicht vor dem Startdatum liegen.")
            return

        if new_status == "Abgeschlossen":
            today = QDate.currentDate()
            check_date = end_date if end_date.isValid() else start_date
            if check_date > today:
                QMessageBox.warning(self, "Status unlogisch", "Das Event liegt in der Zukunft und kann daher noch nicht 'Abgeschlossen' sein.")
                return

        if self.old_status == "Abgeschlossen" and new_status != "Abgeschlossen":
            reply = QMessageBox.question(self, "Event reaktivieren?", "Sie ändern den Status von 'Abgeschlossen' zurück auf aktiv/in Planung.\nMöchten Sie fortfahren?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No: return

        if new_status == "Abgesagt" and self.old_status != "Abgesagt" and self.event_id:
            reply = QMessageBox.question(self, "Event abgesagt", "Das Event wird abgesagt. Sollen alle bisherigen Helfer-Zuweisungen gelöscht werden?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.db_manager.clear_assignments_for_event(self.event_id)

        event_data = {
            "name": name,
            "start_date": start_date.toString("yyyy-MM-dd"),
            "status": new_status,
        }
        if end_date.isValid():
            event_data["end_date"] = end_date.toString("yyyy-MM-dd")
        else:
            event_data["end_date"] = None

        # 1. Event speichern
        if self.event_id is None:
            self.event_id = self.db_manager.add_event(**event_data)
        else:
            self.db_manager.update_event(self.event_id, **event_data)

        # 2. Anhänge speichern (Strategie: Alle alten löschen, neue Liste einfügen)
        # Dazu holen wir erst die alten IDs, um sie zu löschen
        old_attachments = self.db_manager.get_attachments_for_event(self.event_id)
        for old_att in old_attachments:
            self.db_manager.delete_attachment(old_att['attachment_id'])
        
        # Neue Liste einfügen
        for att in self.attachments:
            self.db_manager.add_attachment(self.event_id, att['path'])

        self.data_changed.emit()
        super().accept()