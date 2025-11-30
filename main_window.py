# -*- coding: utf-8 -*-
"""
main_window.py (Finale Version mit Wächter-Logik)
"""
import shutil
from datetime import datetime
import os

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget,
    QListWidgetItem, QLabel, QStatusBar, QAction, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from widgets.stammdaten_widget import StammdatenWidget
from widgets.duty_types_widget import DutyTypesWidget
from widgets.events_widget import EventsWidget
from widgets.planning_widget import PlanningWidget
from widgets.plan_matrix_widget import PlanMatrixWidget
from widgets.post_event_widget import PostEventWidget
from widgets.ranking_widget import RankingWidget
from widgets.settings_dialog import SettingsDialog
from widgets.help_dialog import HelpDialog

class MainWindow(QMainWindow):
    restart_requested = pyqtSignal(str)
    full_restart_requested = pyqtSignal()

    def __init__(self, db_manager, settings):
        super().__init__()
        self.db_manager = db_manager
        self.settings = settings
        self.current_event_id = -1
        self.setWindowTitle("EquiShift")
        
        font = self.font()
        font.setPointSize(self.settings.get_font_size())
        self.setFont(font)
        self.menuBar().setFont(font)

        if self.settings.get_start_fullscreen():
            self.showFullScreen()
        else:
            width, height = self.settings.get_window_size()
            self.resize(width, height)
        self._create_menu_bar()
        self._init_ui()

    def _create_menu_bar(self):
            menu_bar = self.menuBar()
            font = self.font()

            file_menu = menu_bar.addMenu("&Datei")
            file_menu.setFont(font)
            
            new_db_action = QAction("Neue Datenbank...", self)
            new_db_action.triggered.connect(self.create_new_db)
            file_menu.addAction(new_db_action)
            
            open_db_action = QAction("Datenbank öffnen...", self)
            open_db_action.triggered.connect(self.open_existing_db)
            file_menu.addAction(open_db_action)
            
            file_menu.addSeparator()
            
            backup_action = QAction("Backup erstellen...", self)
            backup_action.triggered.connect(self.create_backup)
            file_menu.addAction(backup_action)
            
            show_path_action = QAction("Aktuellen Datenbank-Pfad anzeigen", self)
            show_path_action.triggered.connect(self.show_db_path)
            file_menu.addAction(show_path_action)
            
            file_menu.addSeparator()
            
            settings_action = QAction("Einstellungen...", self)
            settings_action.triggered.connect(self.open_settings)
            file_menu.addAction(settings_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction("Beenden", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            help_menu = menu_bar.addMenu("&Hilfe")
            help_menu.setFont(font)
            
            show_help_action = QAction("Hilfe anzeigen", self)
            show_help_action.triggered.connect(self.show_help)
            help_menu.addAction(show_help_action)
            
            help_menu.addSeparator()
            
            about_action = QAction("Über EquiShift", self)
            about_action.triggered.connect(self.show_about_dialog)
            help_menu.addAction(about_action)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0; border: none; font-size: 12pt; padding-top: 10px;
            }
            QListWidget::item { padding: 10px; }
            QListWidget::item:selected {
                background-color: #e0c8f5;
                border-left: 5px solid #6b14b8;
                color: black;
            }
        """)
        main_layout.addWidget(self.nav_list)
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        self.setStatusBar(QStatusBar(self))
        self.status_label = QLabel("Bereit.")
        self.statusBar().addWidget(self.status_label)
        self.statusBar().setStyleSheet("font-size: 10pt; padding: 3px;")
        self.pages = {} 
        self.create_pages()
        self.nav_list.currentRowChanged.connect(self.on_page_changed)
        self.nav_list.setCurrentRow(0)

    def create_pages(self):
            stammdaten_page = StammdatenWidget(self.db_manager, self.settings, self)
            self.add_page(stammdaten_page, "Stammdaten")
            duty_types_page = DutyTypesWidget(self.db_manager, self)
            self.add_page(duty_types_page, "Dienst-Typen")
            
            event_page = EventsWidget(self.db_manager, self.settings, self)
            event_page.event_selection_changed.connect(self.on_event_selected)
            self.add_page(event_page, "Events verwalten")
            
            plan_page = PlanningWidget(self.db_manager, self.settings, self)
            plan_page.plan_changed.connect(self.update_status_bar)
            self.add_page(plan_page, "Schichtplanung")
            matrix_page = PlanMatrixWidget(self.db_manager, self)
            self.add_page(matrix_page, "Grafische Übersicht")
            post_event_page = PostEventWidget(self.db_manager, self)
            self.add_page(post_event_page, "Nachbereitung")
            ranking_page = RankingWidget(self.db_manager, self.settings, self)
            self.add_page(ranking_page, "Auswertungen")

            planning_widget = self.pages["Schichtplanung"]
            matrix_widget = self.pages["Grafische Übersicht"]
            post_event_widget = self.pages["Nachbereitung"]
            planning_widget.event_selection_changed.connect(self.on_event_selected)
            matrix_widget.event_selection_changed.connect(self.on_event_selected)
            post_event_widget.event_selection_changed.connect(self.on_event_selected)

    def add_page(self, widget, name):
        self.stack.addWidget(widget)
        self.pages[name] = widget
        list_item = QListWidgetItem(name)
        list_item.setTextAlignment(Qt.AlignCenter)
        self.nav_list.addItem(list_item)

    def on_page_changed(self, index):
        page_name = self.nav_list.item(index).text()
        
        if page_name == "Nachbereitung":
            event = self.db_manager.get_event_by_id(self.current_event_id)
            
            if event and event['status'] != 'Abgeschlossen':
                reply = QMessageBox.warning(
                    self, 
                    "Aktion nicht möglich",
                    f"Die Nachbereitung ist nur für abgeschlossene Events möglich.\n"
                    f"Das aktuelle Event '{event['name']}' hat den Status '{event['status']}'.\n\n"
                    "Möchten Sie jetzt zur Event-Verwaltung wechseln, um den Status zu ändern?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                previous_widget = self.stack.currentWidget()
                previous_index = self.stack.indexOf(previous_widget)
                if previous_index != -1:
                    self.nav_list.blockSignals(True)
                    self.nav_list.setCurrentRow(previous_index)
                    self.nav_list.blockSignals(False)

                if reply == QMessageBox.Yes:
                    for i in range(self.nav_list.count()):
                        if self.nav_list.item(i).text() == "Events verwalten":
                            QTimer.singleShot(0, lambda: self.nav_list.setCurrentRow(i))
                            QTimer.singleShot(50, lambda: self._select_event_in_manager(self.current_event_id))
                            return
                return

        self.stack.setCurrentIndex(index)
        if hasattr(self.pages[page_name], 'refresh_view'):
            self.pages[page_name].refresh_view()

    def _select_event_in_manager(self, event_id):
        events_widget = self.pages.get("Events verwalten")
        if events_widget and hasattr(events_widget, 'select_event_by_id'):
            events_widget.select_event_by_id(event_id)

    def on_event_selected(self, event_id):
            if self.current_event_id == event_id:
                return
            self.current_event_id = event_id
            
            event = self.db_manager.get_event_by_id(event_id)
            event_name = event['name'] if event else "Unbekannt"
            self.update_status_bar(event_id, event_name)
            
            sender_widget = self.sender()
            for page_name, page_widget in self.pages.items():
                if page_widget != sender_widget and hasattr(page_widget, 'set_current_event'):
                    page_widget.set_current_event(event_id)

    def update_status_bar(self, event_id, event_name):
        if event_id == -1:
            self.status_label.setText("Kein Event ausgewählt.")
            self.statusBar().setStyleSheet("background-color: #f0f0f0;")
            return
        required, assigned = self.db_manager.get_event_staffing_summary(event_id)
        open_slots = required - assigned
        missing_tl_shifts = self.db_manager.check_team_leader_compliance(event_id)
        num_missing_tl = len(missing_tl_shifts)
        if required == 0:
            status_text = f"Event '{event_name}': Noch keine Schichten geplant."
            color = "#f0f0f0"
        elif open_slots > 0:
            status_text = f"Event '{event_name}': <b>{open_slots} von {required} Helfern benötigt.</b>"
            color = "#ffc107"
        elif num_missing_tl > 0:
            status_text = f"Event '{event_name}': Alle Plätze besetzt, ABER <b>{num_missing_tl} Schichten fehlen ein Teamleiter!</b>"
            color = "#dc3545"
        else:
            status_text = f"Event '{event_name}': Planung abgeschlossen! Alle {required} Plätze besetzt und TLs vorhanden. ✅"
            color = "#28a745"
        self.status_label.setText(status_text)
        self.statusBar().setStyleSheet(f"background-color: {color}; font-size: 10pt; padding: 3px;")

    def create_new_db(self):
        path, _ = QFileDialog.getSaveFileName(self, "Neue Datenbank speichern", "vereinsplaner.db", "Datenbankdateien (*.db)")
        if path:
            self.restart_requested.emit(path)
            self.close()

    def open_existing_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Bestehende Datenbank öffnen", "", "Datenbankdateien (*.db)")
        if path:
            self.restart_requested.emit(path)
            self.close()
            
    def show_db_path(self):
        QMessageBox.information(self, "Datenbank-Pfad", f"Die aktuell verwendete Datenbank befindet sich unter:\n{self.db_manager.db_path}")

    def create_backup(self):
        current_db_path = self.db_manager.db_path
        if not current_db_path or not os.path.exists(current_db_path):
            QMessageBox.warning(self, "Fehler", "Keine Datenbank geladen, um ein Backup zu erstellen.")
            return
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_filename = f"vereinsplaner_backup_{timestamp}.db"
        path, _ = QFileDialog.getSaveFileName(self, "Backup speichern unter...", default_filename, "Datenbankdateien (*.db)")
        if path:
            try:
                shutil.copy2(current_db_path, path)
                QMessageBox.information(self, "Backup erfolgreich", f"Ein Backup der Datenbank wurde erfolgreich unter\n{path}\ngespeichert.")
            except Exception as e:
                QMessageBox.critical(self, "Backup fehlgeschlagen", f"Das Backup konnte nicht erstellt werden:\n{e}")

    def open_settings(self):
            # WICHTIG: Reihenfolge muss exakt zur __init__ passen!
            # 1. self (das Parent-Fenster)
            # 2. self.settings
            # 3. self.db_manager
            dialog = SettingsDialog(self, self.settings, self.db_manager)
            
            dialog.settings_changed.connect(self.request_full_restart)
            dialog.exec_()

    def request_full_restart(self):
        QMessageBox.information(self, "Neustart erforderlich", "Die Einstellungen wurden gespeichert.\nDie Anwendung wird jetzt neu gestartet, um die Änderungen zu übernehmen.")
        self.full_restart_requested.emit()
        self.close()

    def show_help(self):
        if not hasattr(self, 'help_dialog'):
            self.help_dialog = HelpDialog(self)
        self.help_dialog.show()
        self.help_dialog.raise_()
        self.help_dialog.activateWindow()

    def show_about_dialog(self):
            about_text = """
                <h2>EquiShift</h2>
                <p>Version 1.1</p>
                <p>Copyright © 2025 Raiko347</p>
                <p>Als umfassende End-to-End-Lösung konzipiert, meistert diese Anwendung die gesamte
                Orchestrierung komplexer Veranstaltungen. Von der strategischen Personaldisposition über
                die Live-Planung bis hin zur detaillierten Auswertung wird jeder Prozessschritt für maximale
                Effizienz und Transparenz digitalisiert.</p>
                <hr>
                <p><b>Entwicklungsumgebung & Technologien:</b></p>
                <ul>
                    <li>Visual Studio Code Version 1.106.0</li>
                    <li>Python 3.12.11 64-bit</li>
                    <li>Qt 5.15.15 / PyQt5 5.15.11</li>
                    <li>Windows_NT x64 10.0.26200</li>
                    <li>Chromium: 138.0.7204.251</li>
                    <li>Gemini 3.0 Pro</li>
                </ul>
                <p><b>Kern-Bibliotheken:</b></p>
                <ul>
                    <li>SQLite</li>
                    <li>pandas & openpyxl</li>
                    <li>reportlab & pypdf</li>
                    <li>matplotlib</li>
                </ul>

                <p style='font-size: 12px; color: #555;'><b>Haftungsausschluss (Disclaimer):</b><br>
                Die Software wird "wie besehen" zur Verfügung gestellt, ohne jegliche Gewährleistung. 
                Die Nutzung erfolgt auf eigenes Risiko. Der Entwickler haftet nicht für Schäden, Datenverluste 
                oder fehlerhafte Planungen. Die Prüfung der erstellten Dienstpläne und der Aktualität angehängter 
                Dokumente obliegt allein dem Anwender.</p>
            """
            QMessageBox.about(self, "Über EquiShift", about_text)

    def closeEvent(self, event):
        is_fullscreen = self.isFullScreen()
        self.settings.set_start_fullscreen(is_fullscreen)
        if not is_fullscreen:
            size = self.size()
            self.settings.set_window_size(size.width(), size.height())
            self.settings.set_last_event_id(self.current_event_id)
        self.settings.save_settings()
        event.accept()