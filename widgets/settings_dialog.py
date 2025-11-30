# -*- coding: utf-8 -*-
"""
widgets/settings_dialog.py

Dialog zur Verwaltung der Anwendungseinstellungen.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QTextEdit,
    QSpinBox,
)
from PyQt5.QtCore import pyqtSignal


class SettingsDialog(QDialog):
    """Dialog für die Anwendungseinstellungen."""

    settings_changed = pyqtSignal()

    # ÄNDERUNG: parent kommt jetzt als ERSTES Argument
    def __init__(self, parent, settings_manager, db_manager):
        super().__init__(parent)  # Hier wird das parent an QDialog übergeben
        self.settings = settings_manager
        self.db_manager = db_manager
        
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(500)

        font = self.font()
        font.setPointSize(self.settings.get_font_size())
        self.setFont(font)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- UI-Einstellungen ---
        form_layout.addRow(QLabel("<b>Benutzeroberfläche</b>"))
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["8", "9", "10", "11", "12", "14", "16", "18"])
        current_size = str(self.settings.get_font_size())
        self.font_size_combo.setCurrentText(current_size)
        form_layout.addRow("Globale Schriftgröße (in pt):", self.font_size_combo)
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 12)
        self.duration_spin.setSuffix(" Stunden")
        self.duration_spin.setValue(self.settings.get_default_shift_duration())
        form_layout.addRow("Standard-Dauer für neue Schichten:", self.duration_spin)
        # Vereins-Einstellungen ---
        form_layout.addRow(QLabel("<b>Vereins-Regeln</b>"))
        self.mandatory_spin = QSpinBox()
        self.mandatory_spin.setRange(0, 500)
        self.mandatory_spin.setSuffix(" Stunden")
        self.mandatory_spin.setValue(self.settings.get_mandatory_hours())
        form_layout.addRow("Pflichtstunden pro Jahr:", self.mandatory_spin)

        # Altersgrenzen
        self.age_bar_spin = QSpinBox()
        self.age_bar_spin.setRange(14, 99)
        self.age_bar_spin.setValue(self.settings.get_min_age_bar())
        form_layout.addRow("Mindestalter 'Bar':", self.age_bar_spin)

        self.age_kasse_spin = QSpinBox()
        self.age_kasse_spin.setRange(14, 99)
        self.age_kasse_spin.setValue(self.settings.get_min_age_kasse())
        form_layout.addRow("Mindestalter 'Kasse':", self.age_kasse_spin)        

        # PDF-Einstellungen
        form_layout.addRow(QLabel("<b>PDF Export</b>"))

        self.club_name_input = QLineEdit()
        self.club_name_input.setText(self.settings.get_pdf_club_name())
        form_layout.addRow("Vereinsname:", self.club_name_input)

        self.feedback_email_input = QLineEdit()
        self.feedback_email_input.setText(self.settings.get_feedback_email())
        self.feedback_email_input.setPlaceholderText("z.B. orga@meinverein.de")
        form_layout.addRow("E-Mail für Rückmeldungen:", self.feedback_email_input)

        logo_layout = QHBoxLayout()
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setText(self.settings.get_pdf_logo_path())
        browse_button = QPushButton("Durchsuchen...")
        browse_button.clicked.connect(self.select_logo_path)
        logo_layout.addWidget(self.logo_path_input)
        logo_layout.addWidget(browse_button)
        form_layout.addRow("Pfad zum Logo:", logo_layout)

        self.footer_text_input = QTextEdit()
        self.footer_text_input.setText(self.settings.get_pdf_footer_text())
        self.footer_text_input.setFixedHeight(100)
        form_layout.addRow("Footer-Text (links):", self.footer_text_input)

        # --- System-Infos ---
        form_layout.addRow(QLabel("<b>System</b>"))
        
        db_version = self.db_manager.get_database_version()
        version_label = QLabel(str(db_version))
        version_label.setStyleSheet("color: #555; font-weight: bold;")
        form_layout.addRow("Datenbank-Version:", version_label)

        layout.addLayout(form_layout)
        
        note_label = QLabel("\nÄnderungen an der Schriftgröße erfordern einen Neustart der Anwendung.")
        note_label.setStyleSheet("font-style: italic;")
        layout.addWidget(note_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def select_logo_path(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Logo-Datei auswählen",
            "",
            "Bilddateien (*.png *.jpg *.jpeg)",
        )
        if path:
            self.logo_path_input.setText(path)

    def accept(self):
        font_changed = False
        new_size = int(self.font_size_combo.currentText())
        if new_size != self.settings.get_font_size():
            self.settings.set_font_size(new_size)
            font_changed = True

        self.settings.set_default_shift_duration(self.duration_spin.value())
        self.settings.set_mandatory_hours(self.mandatory_spin.value())
        self.settings.set_min_age_bar(self.age_bar_spin.value())
        self.settings.set_min_age_kasse(self.age_kasse_spin.value())
        self.settings.set_pdf_club_name(self.club_name_input.text())
        self.settings.set_feedback_email(self.feedback_email_input.text())
        self.settings.set_pdf_logo_path(self.logo_path_input.text())
        self.settings.set_pdf_footer_text(self.footer_text_input.toPlainText())

        self.settings.save_settings()

        if font_changed:
            self.settings_changed.emit()

        super().accept()