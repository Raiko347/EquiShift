# -*- coding: utf-8 -*-
"""
widgets/help_dialog.py

Ein Dialogfenster, das strukturierte Hilfe-Inhalte anzeigt.
"""
import os
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QTextBrowser,
    QListWidgetItem,
)
from PyQt5.QtCore import QUrl
from utils.resource_path import resource_path


class HelpDialog(QDialog):
    """Dialog zur Anzeige der Hilfe."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EquiShift Hilfe")
        self.setMinimumSize(800, 600)

        # Pfad zum Hilfe-Verzeichnis
        # self.help_path = "help_files"
        self.help_path = resource_path("help_files")

        self._init_ui()
        self._populate_topics()

    def _init_ui(self):
        """Erstellt die Benutzeroberfläche."""
        main_layout = QHBoxLayout(self)

        # Linke Seite: Themenliste
        self.topic_list = QListWidget()
        self.topic_list.setFixedWidth(200)
        main_layout.addWidget(self.topic_list)

        # Rechte Seite: Inhaltsanzeige
        self.content_browser = QTextBrowser()
        main_layout.addWidget(self.content_browser)

        # Signal verbinden
        self.topic_list.currentItemChanged.connect(self.display_topic)

    def _populate_topics(self):
        """Füllt die Themenliste mit den verfügbaren HTML-Dateien."""
        if not os.path.isdir(self.help_path):
            self.content_browser.setText("Fehler: Hilfe-Verzeichnis nicht gefunden.")
            return

        # Finde alle HTML-Dateien und sortiere sie nach Namen (01_, 02_, etc.)
        html_files = sorted([f for f in os.listdir(self.help_path) if f.endswith(".html")])
        
        for file_name in html_files:
            # Entferne die Nummerierung und die Endung für den Titel
            topic_name = os.path.splitext(file_name)[0][3:].replace("_", " ").title()
            item = QListWidgetItem(topic_name)
            item.setData(1, file_name)
            self.topic_list.addItem(item)
        
        if self.topic_list.count() > 0:
            self.topic_list.setCurrentRow(0)
            self.topic_list.setCurrentRow(0)

    def display_topic(self, current_item, previous_item):
        """Zeigt den Inhalt des ausgewählten Themas an."""
        if not current_item:
            return
        
        file_name = current_item.data(1)
        file_path = os.path.join(self.help_path, file_name)

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
                # NEU: Globale Schriftgröße aus den Einstellungen holen
                # Wir greifen über das parent-Fenster auf die Einstellungen zu
                main_window = self.parent()
                if main_window and hasattr(main_window, 'settings'):
                    font_size = main_window.settings.get_font_size()
                    
                    # Schriftgröße in den HTML-Style "injizieren"
                    style_tag = f"<style>body {{ font-size: {font_size}pt; }}</style>"
                    # Ersetze den alten Style-Tag oder füge ihn hinzu
                    if "<style>" in html_content:
                         html_content = html_content.replace("<style>", f"<style>body {{ font-size: {font_size}pt; }}")
                    elif "</head>" in html_content:
                        html_content = html_content.replace("</head>", f"{style_tag}</head>")
                    else:
                        html_content = style_tag + html_content

                self.content_browser.setHtml(html_content)
        else:
            self.content_browser.setText(f"Fehler: Datei {file_name} nicht gefunden.")

    def set_topic(self, topic_filename):
        """Wählt ein bestimmtes Thema in der Liste aus."""
        for i in range(self.topic_list.count()):
            item = self.topic_list.item(i)
            if item.data(1) == topic_filename:
                self.topic_list.setCurrentItem(item)
                break
