# -*- coding: utf-8 -*-
"""
widgets/duty_types_widget.py

Widget zur Verwaltung der Dienst-Typen.
Implementiert eine Sicherheitslogik, die das Bearbeiten und Löschen
von geschützten System-Diensten (z.B. "Bar", "Kasse") verhindert.
Die ID-Spalte wird für den Benutzer ausgeblendet.
"""

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
)
from PyQt5.QtCore import Qt
from .duty_type_dialog import DutyTypeDialog


class DutyTypesWidget(QWidget):
    """Ein Widget zur Anzeige und Verwaltung von Dienst-Typen."""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._init_ui()
        self.load_duty_types_data()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche für dieses Widget."""
        layout = QVBoxLayout(self)

        title_label = QLabel("Dienst-Typen verwalten")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        self.duty_types_table = QTableWidget()
        self.duty_types_table.setColumnCount(3)
        self.duty_types_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Beschreibung"]
        )
        self.duty_types_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.duty_types_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.duty_types_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.duty_types_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.duty_types_table.verticalHeader().setVisible(False)
        self.duty_types_table.setAlternatingRowColors(True)

        # NEU: Die erste Spalte (ID) ausblenden.
        self.duty_types_table.hideColumn(0)

        layout.addWidget(self.duty_types_table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Neuen Dienst-Typ anlegen")
        self.edit_button = QPushButton("Dienst-Typ bearbeiten")
        self.delete_button = QPushButton("Dienst-Typ löschen")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.add_button.clicked.connect(self.add_duty_type)
        self.edit_button.clicked.connect(self.edit_duty_type)
        self.delete_button.clicked.connect(self.delete_duty_type)

        self.duty_types_table.itemSelectionChanged.connect(
            self.update_button_states
        )
        self.update_button_states()

    def load_duty_types_data(self):
        """Lädt die Dienst-Typen und speichert den Schutzstatus in den Tabellenzellen."""
        duty_types = self.db_manager.get_all_duty_types()
        self.duty_types_table.setRowCount(len(duty_types))

        for row_idx, duty_type in enumerate(duty_types):
            id_item = QTableWidgetItem(str(duty_type["duty_type_id"]))
            id_item.setData(Qt.UserRole, duty_type["is_protected"])
            self.duty_types_table.setItem(row_idx, 0, id_item)

            # NEU: Schloss-Symbol für geschützte Dienste
            name_text = duty_type["name"]
            if duty_type["is_protected"]:
                name_text = "🔒 " + name_text
            
            self.duty_types_table.setItem(row_idx, 1, QTableWidgetItem(name_text))
            
            self.duty_types_table.setItem(
                row_idx, 2, QTableWidgetItem(duty_type["description"])
            )
        self.update_button_states()

    def update_button_states(self):
        has_selection = bool(self.duty_types_table.selectedItems())
        if not has_selection:
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            return

        selected_row = self.duty_types_table.currentRow()
        id_item = self.duty_types_table.item(selected_row, 0)
        if not id_item: return
            
        is_protected = id_item.data(Qt.UserRole)
        
        # NEU: Bearbeiten ist IMMER erlaubt (auch bei geschützten)
        self.edit_button.setEnabled(True)
        
        # Löschen ist nur bei ungeschützten erlaubt
        self.delete_button.setEnabled(not is_protected)

    def add_duty_type(self):
        """Öffnet den Dialog zum Anlegen eines neuen Dienst-Typs."""
        dialog = DutyTypeDialog(self.db_manager, parent=self)
        dialog.data_changed.connect(self.load_duty_types_data)
        dialog.exec_()

    def edit_duty_type(self):
        """Öffnet den Dialog zum Bearbeiten des ausgewählten Dienst-Typs."""
        selected_row = self.duty_types_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Auswahl erforderlich", "Bitte wählen Sie zuerst einen Dienst-Typ aus.")
            return

        # ID aus der (versteckten) ersten Spalte holen
        id_item = self.duty_types_table.item(selected_row, 0)
        if not id_item:
            return # Sicherheitsprüfung

        duty_type_id = int(id_item.text())
        
        # Dialog erstellen und öffnen
        dialog = DutyTypeDialog(self.db_manager, duty_type_id=duty_type_id, parent=self)
        dialog.data_changed.connect(self.load_duty_types_data)
        dialog.exec_()

    def delete_duty_type(self):
        """Löscht den ausgewählten Dienst-Typ nach Bestätigung."""
        selected_row = self.duty_types_table.currentRow()
        if selected_row < 0:
            return

        duty_type_id = int(self.duty_types_table.item(selected_row, 0).text())
        duty_type_name = self.duty_types_table.item(selected_row, 1).text()

        usage = self.db_manager.check_duty_type_usage(duty_type_id)
        if usage["restrictions"] > 0 or usage["tasks"] > 0:
            error_message = (
                f"Der Dienst-Typ '{duty_type_name}' kann nicht gelöscht werden, da er noch verwendet wird:\n\n"
                f"- {usage['restrictions']}x als Einschränkung bei Mitgliedern\n"
                f"- {usage['tasks']}x in Event-Aufgaben\n\n"
                "Bitte entfernen Sie zuerst alle diese Zuweisungen."
            )
            QMessageBox.critical(self, "Löschen nicht möglich", error_message)
            return

        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            f"Sind Sie sicher, dass Sie den Dienst-Typ '{duty_type_name}' endgültig löschen möchten?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.delete_duty_type(duty_type_id)
            self.load_duty_types_data()
