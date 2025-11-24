# -*- coding: utf-8 -*-
"""
utils/resource_path.py

Hilfsfunktion, um den korrekten Pfad zu externen Dateien zu finden,
egal ob die Anwendung als Skript oder als gepackte .exe läuft.
"""
import sys
import os


def resource_path(relative_path):
    """Erhalte den absoluten Pfad zu einer Ressource, funktioniert für Dev und für PyInstaller"""
    try:
        # PyInstaller erstellt einen temporären Ordner und speichert den Pfad in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # _MEIPASS ist nicht gesetzt, wir sind im normalen Entwicklungsmodus
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
