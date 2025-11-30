# -*- coding: utf-8 -*-
"""
main.py

Startpunkt der Anwendung. Verwaltet den Anwendungs-Loop und Neustarts.
"""
import sys
import os

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from database_manager import DatabaseManager
from main_window import MainWindow
from utils.settings_manager import SettingsManager
from widgets.db_setup_dialog import DbSetupDialog

# NEU: Import für die Demodaten-Erzeugung
# (Stelle sicher, dass db_setup_handler.py im gleichen Verzeichnis liegt)
try:
    from db_setup_handler import setup_demo_data
except ImportError:
    setup_demo_data = None


def run_app(db_path, settings):
    """Initialisiert und startet die Hauptanwendung."""
    db_manager = None
    try:
        db_manager = DatabaseManager(db_path)
        main_win = MainWindow(db_manager, settings)

        main_win.restart_requested.connect(
            lambda new_path: restart_app(main_win, new_path, settings)
        )
        main_win.full_restart_requested.connect(
            lambda: restart_app(main_win, db_path, settings, full_restart=True)
        )

        main_win.show()
        return app.exec_()
    except Exception as e:
        QMessageBox.critical(
            None,
            "Kritischer Fehler",
            f"Ein unerwarteter Fehler ist aufgetreten: {e}",
        )
    finally:
        if db_manager:
            db_manager.close()
    return 1


def restart_app(main_win, new_path, settings, full_restart=False):
    """Schließt das Fenster und bereitet den Neustart vor."""
    main_win.close()
    if full_restart:
        app.setProperty("full_restart", True)
    else:
        settings.set_db_path(new_path)
    app.exit(2)


def main():
    """Hauptfunktion, die den Anwendungs-Loop steuert."""
    global app
    app = QApplication(sys.argv)
    settings = SettingsManager()

    font_size = settings.get_font_size()
    app.setStyleSheet(f"""
        /* Basis für alle Widgets */
        QWidget {{
            font-size: {font_size}pt;
        }}
        
        /* Speziell für Menüs (wie gehabt) */
        QMenuBar {{
            font-size: {font_size}pt;
        }}
        QMenu {{
            font-size: {font_size}pt;
        }}
        QMenu::item {{
            font-size: {font_size}pt;
            padding: 5px 20px;
        }}
        
        /* Speziell für Tabellen und deren Kopfzeilen */
        QTableWidget {{
            font-size: {font_size}pt;
        }}
        QHeaderView::section {{
            font-size: {font_size}pt;
            font-weight: bold; /* Optional: Überschriften fett */
        }}
        QTreeWidget {{
            font-size: {font_size}pt;
        }}
    """)

    while True:
        db_path = settings.get_db_path()

        if not db_path or not os.path.exists(db_path):
            setup_dialog = DbSetupDialog()
            if setup_dialog.exec_() == QDialog.Accepted and setup_dialog.db_path:
                db_path = setup_dialog.db_path
                settings.set_db_path(db_path)
                
                # NEU: Demodaten generieren, falls gewünscht ---
                if setup_dialog.create_demo:
                    if setup_demo_data:
                        try:
                            # Kurzzeitig DB öffnen, füllen, schließen
                            temp_db = DatabaseManager(db_path)
                            setup_demo_data(temp_db)
                            temp_db.close()
                            print("Demodaten erfolgreich angelegt.")
                        except Exception as e:
                            QMessageBox.warning(None, "Fehler", f"Konnte Demodaten nicht anlegen: {e}")
                    else:
                        QMessageBox.warning(None, "Fehler", "Das Modul 'db_setup_handler.py' wurde nicht gefunden.")
                # --------------------------------------------------
            else:
                sys.exit(0)

        exit_code = run_app(db_path, settings)

        if exit_code == 2:
            if app.property("full_restart"):
                print("Anwendung wird nach Einstellungsänderung neu gestartet...")
                app.setProperty("full_restart", False)
            else:
                print("Anwendung wird mit neuer Datenbank neu gestartet...")
            continue
        else:
            break


if __name__ == "__main__":
    main()