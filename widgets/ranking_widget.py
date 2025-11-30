# -*- coding: utf-8 -*-
"""
widgets/ranking_widget.py

Widget zur Anzeige verschiedener Auswertungen (Ranking, Stunden, Details).
"""
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QAbstractItemView,
    QHeaderView,
    QCheckBox,
    QComboBox,
    QRadioButton,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QBrush, QColor
from utils.exporter import Exporter


class RankingWidget(QWidget):
    """Ein Widget zur Anzeige von Helfer-Auswertungen."""

    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.settings = settings
        self._init_ui()
        self.load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        title_label = QLabel("Auswertungen")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("<b>Ansicht:</b>"))
        self.rb_ranking = QRadioButton("Bonus/Malus-Ranking")
        self.rb_hours = QRadioButton("Geleistete Stunden")
        self.rb_details = QRadioButton("Detail-Matrix")
        self.rb_mandatory = QRadioButton("Pflichtstunden-Status")
        
        self.rb_ranking.setChecked(True)
        
        self.rb_ranking.toggled.connect(self.load_data)
        self.rb_hours.toggled.connect(self.load_data)
        self.rb_details.toggled.connect(self.load_data)
        self.rb_mandatory.toggled.connect(self.load_data)
        
        top_layout.addWidget(self.rb_ranking)
        top_layout.addWidget(self.rb_hours)
        top_layout.addWidget(self.rb_details)
        top_layout.addWidget(self.rb_mandatory)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        options_layout = QHBoxLayout()
        self.ranking_options = QWidget()
        ranking_options_layout = QHBoxLayout(self.ranking_options)
        ranking_options_layout.setContentsMargins(0, 0, 0, 0)
        self.inactive_checkbox = QCheckBox("Auch inaktive Mitglieder anzeigen")
        self.inactive_checkbox.stateChanged.connect(self.load_data)
        ranking_options_layout.addWidget(self.inactive_checkbox)
        ranking_options_layout.addStretch()
        options_layout.addWidget(self.ranking_options)

        self.hours_options = QWidget()
        hours_options_layout = QHBoxLayout(self.hours_options)
        hours_options_layout.setContentsMargins(0, 0, 0, 0)
        self.hours_filter_combo = QComboBox()
        self.hours_filter_combo.addItems(["Gesamt", "Aktuelles Jahr"])
        self.hours_filter_combo.currentIndexChanged.connect(self.load_data)
        hours_options_layout.addWidget(QLabel("Zeitraum:"))
        hours_options_layout.addWidget(self.hours_filter_combo)
        hours_options_layout.addStretch()
        self.export_button = QPushButton("Exportieren (XLSX)")
        self.export_button.clicked.connect(self.export_summary)
        hours_options_layout.addWidget(self.export_button)
        options_layout.addWidget(self.hours_options)
        layout.addLayout(options_layout)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def load_data(self):
        """Lädt die Daten für die aktuell ausgewählte Ansicht."""
        # Sichtbarkeit der Optionen steuern
        self.ranking_options.setVisible(self.rb_ranking.isChecked())
        # Export-Button ist jetzt IMMER sichtbar (da wir für alles Exporte haben)
        self.hours_options.setVisible(True)
        
        # Filter-Combo nur bei Stunden/Details/Pflicht anzeigen
        self.hours_filter_combo.setVisible(not self.rb_ranking.isChecked())
        self.hours_filter_combo.parentWidget().layout().itemAt(0).widget().setVisible(not self.rb_ranking.isChecked()) # Label "Zeitraum"

        if self.rb_ranking.isChecked():
            self._load_ranking_data()
        elif self.rb_hours.isChecked():
            self._load_hours_data()
        elif self.rb_details.isChecked():
            self._load_details_data()
        elif self.rb_mandatory.isChecked():
            self._load_mandatory_data()

    def _load_ranking_data(self):
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Rang", "Name", "Gesamt-Score"])
        
        include_inactive = self.inactive_checkbox.isChecked()
        scores = self.db_manager.calculate_scores(include_inactive=include_inactive)
        
        self.table.setRowCount(len(scores))
        for row_idx, score_data in enumerate(scores):
            rank_item = QTableWidgetItem(str(row_idx + 1))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, rank_item)
            self.table.setItem(row_idx, 1, QTableWidgetItem(score_data['name']))
            score_item = QTableWidgetItem(str(score_data['total_score']))
            score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 2, score_item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def _load_hours_data(self):
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Rang", "Name", "Geleistete Stunden"])
        time_filter = 'current_year' if self.hours_filter_combo.currentText() == "Aktuelles Jahr" else 'all'
        hours_data = self.db_manager.calculate_worked_hours(time_filter=time_filter)
        self.table.setRowCount(len(hours_data))
        for row_idx, data in enumerate(hours_data):
            rank_item = QTableWidgetItem(str(row_idx + 1))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, rank_item)
            self.table.setItem(row_idx, 1, QTableWidgetItem(data['name']))
            hours_str = f"{data['total_hours']:.2f}"
            hours_item = QTableWidgetItem(hours_str)
            hours_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 2, hours_item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def _load_details_data(self):
        self.table.clear()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Geleistete Stunden", "Erledigt", "Als Vertreter", "Entschuldigt", "Nicht Erschienen"])
        time_filter = 'current_year' if self.hours_filter_combo.currentText() == "Aktuelles Jahr" else 'all'
        details_data = self.db_manager.get_detailed_member_summary(time_filter=time_filter)
        if not details_data:
            self.table.setRowCount(0)
            return
        total_hours = sum(d['total_hours'] for d in details_data)
        total_done = sum(d['total_done'] for d in details_data)
        total_substitute = sum(d['total_substitute'] for d in details_data)
        total_excused = sum(d['total_excused'] for d in details_data)
        total_absent = sum(d['total_absent'] for d in details_data)
        self.table.setRowCount(len(details_data) + 1)
        for row_idx, data in enumerate(details_data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(data['name']))
            hours_item = QTableWidgetItem(f"{data['total_hours']:.2f}")
            hours_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 1, hours_item)
            done_item = QTableWidgetItem(str(data['total_done']))
            done_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 2, done_item)
            sub_item = QTableWidgetItem(str(data['total_substitute']))
            sub_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 3, sub_item)
            exc_item = QTableWidgetItem(str(data['total_excused']))
            exc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 4, exc_item)
            abs_item = QTableWidgetItem(str(data['total_absent']))
            abs_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 5, abs_item)
        summary_row_index = len(details_data)
        bold_font = QFont()
        bold_font.setBold(True)
        gray_background = QBrush(QColor("#f0f0f0"))
        label_item = QTableWidgetItem("Gesamt:")
        label_item.setFont(bold_font)
        label_item.setBackground(gray_background)
        self.table.setItem(summary_row_index, 0, label_item)
        sum_items = [f"{total_hours:.2f}", str(total_done), str(total_substitute), str(total_excused), str(total_absent)]
        for col_idx, text in enumerate(sum_items, start=1):
            item = QTableWidgetItem(text)
            item.setFont(bold_font)
            item.setBackground(gray_background)
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(summary_row_index, col_idx, item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def _load_mandatory_data(self):
        self.table.clear()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Ist (Std.)", "Soll (Std.)", "Differenz"])
        target_hours = self.settings.get_mandatory_hours()
        data = self.db_manager.get_mandatory_hours_status()
        self.table.setRowCount(len(data))
        red_brush = QBrush(QColor("#ffcccc"))
        green_brush = QBrush(QColor("#ccffcc"))
        for row_idx, entry in enumerate(data):
            worked = entry['worked_hours']
            diff = worked - target_hours
            name_item = QTableWidgetItem(entry['name'])
            worked_item = QTableWidgetItem(f"{worked:.2f}")
            worked_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item = QTableWidgetItem(f"{target_hours:.2f}")
            target_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            diff_item = QTableWidgetItem(f"{diff:.2f}")
            diff_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if diff < 0: diff_item.setBackground(red_brush)
            else: diff_item.setBackground(green_brush)
            self.table.setItem(row_idx, 0, name_item)
            self.table.setItem(row_idx, 1, worked_item)
            self.table.setItem(row_idx, 2, target_item)
            self.table.setItem(row_idx, 3, diff_item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def export_summary(self):
        """Exportiert die aktuelle Ansicht als XLSX."""
        time_filter_text = self.hours_filter_combo.currentText()
        time_filter_db = "current_year" if time_filter_text == "Aktuelles Jahr" else "all"
        
        export_func = None
        default_filename = ""

        if self.rb_ranking.isChecked():
            include_inactive = self.inactive_checkbox.isChecked()
            export_data = self.db_manager.calculate_scores(include_inactive=include_inactive)
            default_filename = "Bonus_Malus_Ranking.xlsx"
            export_func = lambda path: Exporter.export_ranking_to_xlsx(export_data, path)

        elif self.rb_hours.isChecked():
            export_data = self.db_manager.get_hours_and_duties_summary(time_filter=time_filter_db)
            default_filename = f"Stundenuebersicht_{time_filter_text.replace(' ', '_')}.xlsx"
            export_func = lambda path: Exporter.export_hours_summary_to_xlsx(export_data, path, time_filter_text)
            
        elif self.rb_details.isChecked():
            export_data = self.db_manager.get_detailed_member_summary(time_filter=time_filter_db)
            default_filename = f"Detail-Matrix_{time_filter_text.replace(' ', '_')}.xlsx"
            export_func = lambda path: Exporter.export_detailed_summary_to_xlsx(export_data, path)
            
        elif self.rb_mandatory.isChecked():
            export_data = self.db_manager.get_mandatory_hours_status()
            target_hours = self.settings.get_mandatory_hours()
            default_filename = f"Pflichtstunden_Status_{datetime.now().year}.xlsx"
            export_func = lambda path: Exporter.export_mandatory_status_to_xlsx(export_data, path, target_hours)
            
        if not export_func: return

        if not export_data:
            QMessageBox.information(self, "Keine Daten", "Es gibt keine Daten zum Exportieren.")
            return

        last_path = self.settings.get_last_export_path()
        default_filename = os.path.join(last_path, default_filename)

        file_path, _ = QFileDialog.getSaveFileName(self, "Exportieren", default_filename, "Excel-Datei (*.xlsx)")
        if not file_path: return

        self.settings.set_last_export_path(os.path.dirname(file_path))
        
        if export_func(file_path):
            QMessageBox.information(self, "Export erfolgreich", f"Die Übersicht wurde erfolgreich nach\n{file_path}\nexportiert.")
        else:
            QMessageBox.critical(self, "Export fehlgeschlagen", "Die Übersicht konnte nicht exportiert werden.")