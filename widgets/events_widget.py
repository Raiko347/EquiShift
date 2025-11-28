# -*- coding: utf-8 -*-
"""
widgets/events_widget.py

Widget zur Verwaltung der Events.
"""
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
    QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal  # pyqtSignal hinzugefügt
from .event_dialog import EventDialog
from .copy_event_dialog import CopyEventDialog

class EventsWidget(QWidget):
    """Ein Widget zur Anzeige und Verwaltung von Events."""
    
    # NEU: Signal für Synchronisation
    event_selection_changed = pyqtSignal(int)

    def __init__(self, db_manager, settings, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.settings = settings # Speichern
        self._init_ui()
        self.load_events_data()
        
        # NEU: Letztes Event wiederherstellen
        last_id = self.settings.get_last_event_id()
        if last_id != -1:
            # Wir nutzen QTimer, damit die UI erst fertig aufgebaut ist
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.set_current_event(last_id))
            # Auch das Signal senden, damit andere Widgets Bescheid wissen
            QTimer.singleShot(150, lambda: self.event_selection_changed.emit(last_id))
            
    def _init_ui(self):
        """Erstellt die Benutzeroberfläche für dieses Widget."""
        layout = QVBoxLayout(self)

        title_label = QLabel("Events verwalten")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        self.events_table = QTableWidget()
        self.events_table.setColumnCount(4)
        self.events_table.setHorizontalHeaderLabels(
            ["Name", "Startdatum", "Enddatum", "Status"]
        )
        self.events_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.events_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.events_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.events_table.verticalHeader().setVisible(False)
        self.events_table.setAlternatingRowColors(True)

        header = self.events_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        layout.addWidget(self.events_table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Neues Event anlegen")
        self.edit_button = QPushButton("Event bearbeiten")
        self.copy_button = QPushButton("Event kopieren")
        self.delete_button = QPushButton("Event löschen")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.add_button.clicked.connect(self.add_event)
        self.edit_button.clicked.connect(self.edit_event)
        self.copy_button.clicked.connect(self.copy_event) 
        self.delete_button.clicked.connect(self.delete_event)
        
        # Signal verbinden, wenn Zeile ausgewählt wird
        self.events_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.on_selection_changed()

    def _format_date_for_display(self, date_str_from_db):
        if not date_str_from_db:
            return ""
        try:
            date_obj = datetime.strptime(date_str_from_db, "%Y-%m-%d")
            return date_obj.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            return date_str_from_db

    def load_events_data(self):
            """Lädt die Events neu. Wählt NICHTS automatisch aus."""
            self.events_table.blockSignals(True) # Signale blockieren
            self.events_table.clearSelection()   # Auswahl leeren
            
            events = self.db_manager.get_all_events()
            self.events_table.setRowCount(len(events))

            for row_idx, event in enumerate(events):
                name_item = QTableWidgetItem(event["name"])
                name_item.setData(Qt.UserRole, event["event_id"])
                self.events_table.setItem(row_idx, 0, name_item)

                self.events_table.setItem(
                    row_idx,
                    1,
                    QTableWidgetItem(
                        self._format_date_for_display(event["start_date"])
                    ),
                )
                self.events_table.setItem(
                    row_idx,
                    2,
                    QTableWidgetItem(
                        self._format_date_for_display(event["end_date"])
                    ),
                )
                self.events_table.setItem(
                    row_idx, 3, QTableWidgetItem(event["status"])
                )
            
            self.events_table.blockSignals(False) # Signale wieder freigeben
            # WICHTIG: Keine automatische Selektion hier! Das macht der Aufrufer (copy_event) bei Bedarf.
        
        # Handler für Auswahländerung
    def on_selection_changed(self):
        selected_row = self.events_table.currentRow()
        if selected_row >= 0:
            item = self.events_table.item(selected_row, 0)
            if item:
                event_id = item.data(Qt.UserRole)
                self.event_selection_changed.emit(event_id)

    # NEU: Methode um von außen (MainWindow) gesteuert zu werden
    def set_current_event(self, event_id):
        """Wählt das Event mit der gegebenen ID in der Tabelle aus und setzt den Fokus."""
        self.events_table.blockSignals(True)
        self.events_table.clearSelection()
        
        found = False
        for row in range(self.events_table.rowCount()):
            item = self.events_table.item(row, 0)
            if item and item.data(Qt.UserRole) == event_id:
                self.events_table.selectRow(row)
                self.events_table.scrollToItem(item)
                found = True
                break
        
        self.events_table.blockSignals(False)
        
        # Fokus erzwingen, damit die Auswahl BLAU (aktiv) und nicht grau (inaktiv) ist
        if found:
            self.events_table.setFocus()

    def select_event_by_id(self, event_id):
        self.set_current_event(event_id)

    def copy_event(self):
        selected_row = self.events_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Auswahl erforderlich", "Bitte wählen Sie zuerst ein Event aus.")
            return
            
        event_id = self.events_table.item(selected_row, 0).data(Qt.UserRole)
        event_name = self.events_table.item(selected_row, 0).text()
        
        event_data = self.db_manager.get_event_by_id(event_id)
        if not event_data: return

        dialog = CopyEventDialog(event_name, event_data['start_date'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            # WICHTIG: 4 Rückgabewerte empfangen!
            success, message, new_event_id, attachments_copied = self.db_manager.copy_event(
                event_id, 
                dialog.new_name, 
                dialog.new_start_date, 
                dialog.copy_mode
            )
            
            if success:
                # Spezielle Nachricht, wenn Anhänge kopiert wurden
                if attachments_copied:
                    message += "\n\n⚠️ HINWEIS: Es wurden Datei-Anhänge vom Ursprungs-Event übernommen.\nBitte prüfen Sie diese im Reiter 'Anhänge' auf Aktualität!"
                
                QMessageBox.information(self, "Erfolg", message)
                self.load_events_data()
                
                if new_event_id:
                    self.set_current_event(new_event_id)
                    self.event_selection_changed.emit(new_event_id)
            else:
                QMessageBox.critical(self, "Kopieren fehlgeschlagen", f"Es ist ein Fehler aufgetreten:\n\n{message}")

    def add_event(self):
        dialog = EventDialog(self.db_manager, parent=self)
        dialog.data_changed.connect(self.load_events_data)
        dialog.exec_()

    def edit_event(self):
        selected_row = self.events_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Auswahl erforderlich",
                "Bitte wählen Sie zuerst ein Event aus.",
            )
            return
        event_id = self.events_table.item(selected_row, 0).data(Qt.UserRole)
        dialog = EventDialog(self.db_manager, event_id=event_id, parent=self)
        dialog.data_changed.connect(self.load_events_data)
        dialog.exec_()

    def delete_event(self):
        selected_row = self.events_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Auswahl erforderlich",
                "Bitte wählen Sie zuerst ein Event aus.",
            )
            return
        event_id = self.events_table.item(selected_row, 0).data(Qt.UserRole)
        event_name = self.events_table.item(selected_row, 0).text()
        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            f"Sind Sie sicher, dass Sie das Event '{event_name}' löschen möchten?\n"
            "Alle zugehörigen Aufgaben und Schichten werden ebenfalls unwiderruflich entfernt.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db_manager.delete_event(event_id)
            self.load_events_data()