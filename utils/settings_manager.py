# -*- coding: utf-8 -*-
"""
utils/settings_manager.py

Verwaltet das Lesen und Schreiben der Konfigurationsdatei (config.ini).
"""
import configparser
import os
from utils.resource_path import resource_path

CONFIG_FILE = resource_path("config.ini")


class SettingsManager:
    """Eine Klasse zur Verwaltung der Anwendungseinstellungen."""

    def __init__(self):
        self.config = configparser.ConfigParser()
        if not os.path.exists(CONFIG_FILE):
            self._create_default_config()
        else:
            self.config.read(CONFIG_FILE, encoding="utf-8")
            if not self.config.has_section("UI"):
                self.config.add_section("UI")
            if not self.config.has_option("UI", "font_size"):
                self.config.set("UI", "font_size", "10")
            if not self.config.has_option("UI", "start_fullscreen"):
                self.config.set("UI", "start_fullscreen", "false")
            if not self.config.has_option("UI", "window_width"):
                self.config.set("UI", "window_width", "1280")
            if not self.config.has_option("UI", "window_height"):
                self.config.set("UI", "window_height", "800")

            if not self.config.has_section("PDF"):
                self.config.add_section("PDF")
            if not self.config.has_option("PDF", "club_name"):
                self.config.set("PDF", "club_name", "Mein Verein e.V.")
            if not self.config.has_option("PDF", "footer_text"):
                self.config.set("PDF", "footer_text", "Allgemeine Informationen: ...")
            if not self.config.has_option("PDF", "logo_path"):
                self.config.set("PDF", "logo_path", "logo.png")

            if not self.config.has_section("Paths"):
                self.config.add_section("Paths")
            if not self.config.has_option("Paths", "last_export_path"):
                self.config.set("Paths", "last_export_path", "")

            self.save_settings()

    def _create_default_config(self):
        """Erstellt eine Konfigurationsdatei mit Standardwerten."""
        self.config["Database"] = {"path": ""}
        self.config["UI"] = {
            "font_size": "10",
            "start_fullscreen": "false",
            "window_width": "1280",
            "window_height": "800",
        }
        
        footer_text = (
            "Ein Tausch von Diensten unter den Mitgliedern ist jederzeit möglich. "
            "Kann ein zugewiesener Dienst nicht durchgeführt werden, ist die eigenständige Suche und Organisation von Ersatz durch die betroffene Person erforderlich. "
            "In jedem Fall (Tausch oder Ersatzgestellung) muss die Vorstandschaft umgehend informiert werden, damit eine korrekte Aktualisierung des Dienstplans erfolgen kann. "
            "WICHTIG: Bitte beachten Sie auch wichtige Dokumente (z.B. Sicherheits- oder Hygienevorschriften), die diesem Dienstplan angefügt sein können!"
        )

        self.config["PDF"] = {
            "club_name": "Mein Verein e.V.",
            "footer_text": footer_text,
            "logo_path": "logo.png",
        }
        self.config["Paths"] = {"last_export_path": ""}
        self.save_settings()

    def save_settings(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as configfile:
            self.config.write(configfile)

    def get_db_path(self):
        return self.config.get("Database", "path", fallback="")

    def set_db_path(self, path):
        self.config.set("Database", "path", path)
        self.save_settings()

    # --- UI-Einstellungen ---
    def get_font_size(self):
        return self.config.getint("UI", "font_size", fallback=10)

    def set_font_size(self, size):
        self.config.set("UI", "font_size", str(size))

    def get_start_fullscreen(self):
        return self.config.getboolean("UI", "start_fullscreen", fallback=False)

    def set_start_fullscreen(self, is_fullscreen):
        self.config.set("UI", "start_fullscreen", "true" if is_fullscreen else "false")

    def get_window_size(self):
        width = self.config.getint("UI", "window_width", fallback=1280)
        height = self.config.getint("UI", "window_height", fallback=800)
        return width, height

    def set_window_size(self, width, height):
        self.config.set("UI", "window_width", str(width))
        self.config.set("UI", "window_height", str(height))

    # --- PDF-Einstellungen ---
    def get_pdf_club_name(self):
        return self.config.get("PDF", "club_name", fallback="Mein Verein e.V.")

    def set_pdf_club_name(self, name):
        self.config.set("PDF", "club_name", name)

    def get_pdf_footer_text(self):
        return self.config.get("PDF", "footer_text", fallback="")

    def set_pdf_footer_text(self, text):
        self.config.set("PDF", "footer_text", text)

    def get_pdf_logo_path(self):
        return self.config.get("PDF", "logo_path", fallback="logo.png")

    def set_pdf_logo_path(self, path):
        self.config.set("PDF", "logo_path", path)

    def get_last_export_path(self):
        return self.config.get("Paths", "last_export_path", fallback="")

    def set_last_export_path(self, path):
        self.config.set("Paths", "last_export_path", path)
        self.save_settings()