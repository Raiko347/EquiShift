# -*- coding: utf-8 -*-
"""
widgets/shift_details_widget.py

Zeigt Details zur ausgewählten Schicht an und ermöglicht manuelle Zuweisungen.
"""
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QMessageBox,
    QDialog,
)
from PyQt5.QtCore import pyqtSignal, Qt
from .assign_helper_dialog import AssignHelperDialog
from PyQt5.QtGui import QFont


class ShiftDetailsWidget(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, db_manager, planning_widget, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.planning_widget = planning_widget
        self.current_shift_id = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(QLabel("<b>Zugewiesene Helfer:</b>"))
        self.assigned_list = QListWidget()
        main_layout.addWidget(self.assigned_list)
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Helfer zuweisen")
        self.remove_button = QPushButton("Zuweisung entfernen")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        main_layout.addLayout(button_layout)

        self.assigned_list.itemSelectionChanged.connect(
            self._update_button_states
        )
        self.remove_button.clicked.connect(self._remove_helper)
        self.add_button.clicked.connect(self._add_helper)

        self.clear_view()

    def clear_view(self):
        self.current_shift_id = None
        self.assigned_list.clear()
        self.setEnabled(False)

    def load_shift_data(self, shift_id):
        """Lädt die Daten für eine Schicht und zeigt Kompetenz/TL-Status an."""
        self.current_shift_id = shift_id
        self.assigned_list.clear()
        self.setEnabled(True)

        assigned_persons = self.db_manager.get_assigned_persons_for_shift(shift_id)
        
        bold_font = QFont()
        bold_font.setBold(True)
        
        italic_font = QFont()
        italic_font.setItalic(True)

        if assigned_persons:
            # Sortiere die Personen: TLs zuerst, dann Kompetente, dann alphabetisch
            sorted_persons = sorted(assigned_persons, key=lambda p: (p['is_team_leader'], p['has_competence']), reverse=True)

            for person in sorted_persons:
                display_text = person['display_name']
                
                item = QListWidgetItem()
                
                if person['is_team_leader']:
                    display_text += " (TL)"
                    item.setFont(bold_font)
                elif person['has_competence']:
                    display_text += " (*)"
                    item.setFont(italic_font)
                
                item.setText(display_text)
                item.setData(Qt.UserRole, person['person_id'])
                self.assigned_list.addItem(item)
        
        self._update_button_states()

    def set_editable(self, editable):
        """Aktiviert oder deaktiviert die Bearbeitungs-Buttons."""
        self.add_button.setEnabled(editable)
        if editable:
            self._update_button_states()
        else:
            self.remove_button.setEnabled(False)

    def _update_button_states(self):
        """Aktiviert/Deaktiviert den Entfernen-Button."""
        can_edit = self.add_button.isEnabled()
        has_selection = len(self.assigned_list.selectedItems()) > 0
        self.remove_button.setEnabled(has_selection and can_edit)

    def _add_helper(self):
        """Öffnet den Dialog zur Auswahl eines neuen Helfers."""
        if self.current_shift_id is None:
            return
        
        dialog = AssignHelperDialog(self.db_manager, self.current_shift_id, self)
        if dialog.exec_() == QDialog.Accepted:
            # NEU: Liste verarbeiten
            person_ids = dialog.selected_person_ids
            if person_ids:
                for pid in person_ids:
                    self.db_manager.assign_person_to_shift(pid, self.current_shift_id)
                
                self.load_shift_data(self.current_shift_id)
                self.data_changed.emit()

    def _remove_helper(self):
        """Entfernt den ausgewählten Helfer aus der Schicht."""
        selected_item = self.assigned_list.currentItem()
        if not selected_item or self.current_shift_id is None:
            return

        person_id = selected_item.data(Qt.UserRole)
        person_name = selected_item.text()

        reply = QMessageBox.question(
            self,
            "Zuweisung entfernen",
            f"Möchten Sie '{person_name}' wirklich aus dieser Schicht entfernen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.remove_person_from_shift(
                person_id, self.current_shift_id
            )
            self.load_shift_data(self.current_shift_id)
            self.data_changed.emit()