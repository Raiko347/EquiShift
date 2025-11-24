# -*- coding: utf-8 -*-
"""
widgets/export_dialog.py

Ein Assistent zur Auswahl verschiedener Export-Optionen mit konsistentem Layout.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QRadioButton, QComboBox, QDialogButtonBox, QWidget
)
from PyQt5.QtCore import pyqtSignal

class ExportDialog(QDialog):
    """Dialog zur Auswahl der Export-Optionen."""

    def __init__(self, db_manager, event_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.event_id = event_id
        
        self.export_type = 'total'
        self.export_format = 'pdf'
        self.selected_task_id = None

        self.setWindowTitle("Export-Assistent")
        self._init_ui()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche."""
        main_layout = QVBoxLayout(self)

        type_group = QGroupBox("Was möchten Sie exportieren?")
        type_layout = QVBoxLayout()
        
        self.rb_total = QRadioButton("Den Gesamtplan für das gesamte Event")
        self.rb_daily = QRadioButton("Die einzelnen Tagespläne (erzeugt eine Datei pro Tag)")
        self.rb_duty = QRadioButton("Den Plan für einen einzelnen Dienst (über alle Tage)")
        self.rb_post_event = QRadioButton("Nachbereitungs-Bögen zum Ausdrucken")
        self.rb_total.setChecked(True)
        
        type_layout.addWidget(self.rb_total)
        type_layout.addWidget(self.rb_daily)
        type_layout.addWidget(self.rb_duty)

        # --- Options-Widget für Dienst-Auswahl ---
        self.duty_options = QWidget()
        duty_layout = QHBoxLayout(self.duty_options)
        duty_layout.setContentsMargins(40, 0, 0, 0) # Einrücken
        self.duty_combo = QComboBox()
        self._populate_duties(self.duty_combo)
        duty_layout.addWidget(QLabel("Dienst:"))
        duty_layout.addWidget(self.duty_combo)
        type_layout.addWidget(self.duty_options)
        self.duty_options.setVisible(False) # Standardmäßig versteckt

        type_layout.addWidget(self.rb_post_event)
        
        # --- Options-Widget für Nachbereitungs-Bögen ---
        self.post_event_options = QWidget()
        post_event_layout = QVBoxLayout(self.post_event_options)
        post_event_layout.setContentsMargins(40, 0, 0, 0)
        self.rb_post_event_all = QRadioButton("Einen Bogen für alle Dienste erstellen")
        self.rb_post_event_single = QRadioButton("Nur einen Bogen für diesen Dienst:")
        self.post_event_combo = QComboBox()
        self._populate_duties(self.post_event_combo)
        self.rb_post_event_all.setChecked(True)
        self.post_event_combo.setEnabled(False)
        post_event_layout.addWidget(self.rb_post_event_all)
        single_duty_layout = QHBoxLayout()
        single_duty_layout.addWidget(self.rb_post_event_single)
        single_duty_layout.addWidget(self.post_event_combo)
        post_event_layout.addLayout(single_duty_layout)
        type_layout.addWidget(self.post_event_options)
        self.post_event_options.setVisible(False)

        type_group.setLayout(type_layout)
        main_layout.addWidget(type_group)

        self.format_group = QGroupBox("In welchem Format?")
        format_layout = QHBoxLayout()
        self.rb_pdf = QRadioButton("PDF")
        self.rb_xlsx = QRadioButton("Excel (XLSX)")
        self.rb_pdf.setChecked(True)
        format_layout.addWidget(self.rb_pdf)
        format_layout.addWidget(self.rb_xlsx)
        self.format_group.setLayout(format_layout)
        main_layout.addWidget(self.format_group)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Export starten")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # Signale verbinden
        self.rb_duty.toggled.connect(self.duty_options.setVisible)
        self.rb_post_event.toggled.connect(self.toggle_post_event_options)
        self.rb_post_event_single.toggled.connect(self.post_event_combo.setEnabled)

    def toggle_post_event_options(self, checked):
        self.post_event_options.setVisible(checked)
        if checked:
            self.format_group.setEnabled(False)
            self.rb_pdf.setChecked(True)
        else:
            self.format_group.setEnabled(True)

    def _populate_duties(self, combo):
        """Füllt das angegebene Dropdown mit den Aufgaben des Events."""
        # Option für alle Dienste hinzufügen
        if combo == self.duty_combo:
            combo.addItem("Alle Dienste (separate Dateien)", -99)
            combo.insertSeparator(1)

        tasks = self.db_manager.get_tasks_for_event(self.event_id)
        if tasks:
            for task in tasks:
                combo.addItem(task['name'], task['task_id'])

    def accept(self):
        if self.rb_total.isChecked(): self.export_type = 'total'
        elif self.rb_daily.isChecked(): self.export_type = 'daily'
        elif self.rb_duty.isChecked():
            self.export_type = 'duty'
            self.selected_task_id = self.duty_combo.currentData()
        elif self.rb_post_event.isChecked():
            if self.rb_post_event_all.isChecked():
                self.export_type = 'post_event_all'
            else:
                self.export_type = 'post_event_single'
                self.selected_task_id = self.post_event_combo.currentData()

        if self.rb_pdf.isChecked(): self.export_format = 'pdf'
        else: self.export_format = 'xlsx'
        
        super().accept()