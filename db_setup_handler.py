# -*- coding: utf-8 -*-
"""
db_setup_handler.py

Ein Werkzeug-Skript, um die Datenbank für EquiShift zu initialisieren
oder zurückzusetzen und mit Demodaten für ein Mehrtages-Event zu befüllen.
"""
import os
from database_manager import DatabaseManager

DB_FILE = "EquiShift.db"


def setup_demo_data(db):
    """Füllt die Datenbank mit einem Satz von Beispieldaten."""
    print("\n--- Lege Stammdaten der Mitglieder an ---")
    p1 = db.add_person(
        first_name="Anna",
        last_name="Schmidt",
        display_name="Anna S.",
        birth_date="1990-05-15",
        street="Hauptstr. 1",
        postal_code="12345",
        city="Musterstadt",
        email="anna@verein.de",
        phone1="0123-456789",
        status="Aktiv",
        entry_date="2015-03-01",
    )
    p2 = db.add_person(
        first_name="Ben",
        last_name="Müller",
        display_name="Ben M.",
        birth_date="1985-11-20",
        street="Nebenweg 2",
        postal_code="12345",
        city="Musterstadt",
        email="ben@verein.de",
        phone1="0987-654321",
        status="Aktiv",
        entry_date="2018-07-20",
        notes="Ist Elektriker, kann bei Bedarf helfen.",
    )
    p3 = db.add_person(
        first_name="Carla",
        last_name="Weber",
        display_name="Carla W.",
        birth_date="1995-02-10",
        street="Am Park 3",
        postal_code="54321",
        city="Beispielburg",
        email="carla@verein.de",
        phone1="0111-223344",
        status="Passiv",
        entry_date="2020-01-10",
    )
    p4 = db.add_person(
        first_name="David",
        last_name="Klein",
        display_name="David K.",
        birth_date="2000-08-30",
        street="Schulallee 4",
        postal_code="54321",
        city="Beispielburg",
        email="david@verein.de",
        phone1="0222-334455",
        status="Aktiv",
        entry_date="2021-05-15",
    )
    p5 = db.add_person(
        first_name="Eva",
        last_name="Fischer",
        display_name="Eva F.",
        status="Aktiv",
        entry_date="2022-02-01",
    )
    p6 = db.add_person(
        first_name="Frank",
        last_name="Huber",
        display_name="Frank H.",
        status="Aktiv",
        entry_date="2022-03-15",
    )
    p7 = db.add_person(
        first_name="Gerd",
        last_name="Lehmann",
        display_name="Gerd L.",
        status="Aktiv",
        entry_date="2022-05-20",
    )
    p8 = db.add_person(
        first_name="Hanna",
        last_name="Bauer",
        display_name="Hanna B.",
        status="Ruht",
        entry_date="2021-11-11",
    )
    p9 = db.add_person(
        first_name="Ingo",
        last_name="Wolf",
        display_name="Ingo W.",
        status="Aktiv",
        entry_date="2022-08-01",
    )
    print("9 Personen angelegt.")

    print("\n--- Lege zusätzliche, ungeschützte Dienst-Typen an ---")
    db.add_duty_type("Aufbau", "Alle Tätigkeiten vor dem Event")
    db.add_duty_type("Abbau & Deko", "Alle Tätigkeiten nach dem Event")
    db.add_duty_type("Grillstation", "Zubereitung und Verkauf von Speisen")
    db.add_duty_type("Service", "Tische abräumen, für Ordnung sorgen")
    print("Zusätzliche Dienst-Typen angelegt.")

    print("\n--- Setze Demo-Einschränkungen ---")
    kasse_duty = db.get_duty_type_by_name("Kasse")
    aufbau_duty = db.get_duty_type_by_name("Aufbau")
    abbau_duty = db.get_duty_type_by_name("Abbau & Deko")
    if kasse_duty:
        db.set_person_restrictions(p3, [kasse_duty["duty_type_id"]])
        print(f"Einschränkung für Carla Weber (ID {p3}) auf 'Kasse' gesetzt.")
    if aufbau_duty and abbau_duty:
        db.set_person_restrictions(
            p2, [aufbau_duty["duty_type_id"], abbau_duty["duty_type_id"]]
        )
        print(
            f"Einschränkungen für Ben Müller (ID {p2}) auf 'Aufbau' und 'Abbau & Deko' gesetzt."
        )

    print("\n--- Setze Demo-Kompetenzen ---")
    bar_duty = db.get_duty_type_by_name("Bar")
    grill_duty = db.get_duty_type_by_name("Grillstation")
    if bar_duty and grill_duty:
        db.set_person_competencies(
            p1, {bar_duty["duty_type_id"]: 1}
        )  # Anna ist TL für Bar
        db.set_person_competencies(
            p4, {grill_duty["duty_type_id"]: 0}
        )  # David hat Kompetenz am Grill
        print("Kompetenzen für Mitglieder gesetzt.")

    print("\n--- Lege Demo-Event mit Planungsdaten an ---")
    e1 = db.add_event(
        name="Halloweenparty 2025",
        start_date="2025-10-30",
        end_date="2025-11-01",
        status="Aktiv",
    )
    print(f"Event angelegt: Halloweenparty 2025 (ID {e1})")

    t_aufbau = db.add_task(e1, aufbau_duty["duty_type_id"], "Aufbau Festzelt")
    t_bar = db.add_task(e1, bar_duty["duty_type_id"], "Bardienst")
    t_abbau = db.add_task(e1, abbau_duty["duty_type_id"], "Abbau & Deko")
    print("Aufgaben für das Demo-Event angelegt.")

    s_aufbau = db.add_shift(t_aufbau, "2025-10-30", "17:00", "20:00", 4)
    s_bar1 = db.add_shift(t_bar, "2025-10-31", "18:00", "21:00", 2)
    s_bar2 = db.add_shift(t_bar, "2025-10-31", "21:00", "00:00", 2)
    s_abbau = db.add_shift(t_abbau, "2025-11-01", "15:00", "18:00", 6)
    print("Leere Schichten für das Demo-Event angelegt.")

    print("\n--- Lege Demo-Zuweisungen an (Status 'Geplant') ---")
    db.assign_person_to_shift(p1, s_aufbau)  # Anna
    db.assign_person_to_shift(p4, s_aufbau)  # David
    db.assign_person_to_shift(p5, s_aufbau)  # Eva
    db.assign_person_to_shift(p6, s_aufbau)  # Frank

    db.assign_person_to_shift(p1, s_bar1)  # Anna (TL)
    db.assign_person_to_shift(p2, s_bar1)  # Ben

    db.assign_person_to_shift(p3, s_bar2)  # Carla
    db.assign_person_to_shift(p4, s_bar2)  # David

    db.assign_person_to_shift(p1, s_abbau)  # Anna
    db.assign_person_to_shift(p2, s_abbau)  # Ben
    db.assign_person_to_shift(p3, s_abbau)  # Carla
    db.assign_person_to_shift(p4, s_abbau)  # David
    print("Mitglieder den Schichten zugewiesen.")


if __name__ == "__main__":
    print("Dieses Skript wird die Datenbank 'EquiShift.db' zurücksetzen.")
    if os.path.exists(DB_FILE):
        choice = input(
            "WARNUNG: Die Datenbank existiert bereits. Soll sie gelöscht und neu erstellt werden? (j/n): "
        )
        if choice.lower() != "j":
            print("Aktion abgebrochen.")
            exit()
        os.remove(DB_FILE)
        print(f"Alte Datenbank '{DB_FILE}' wurde gelöscht.")

    db_manager = DatabaseManager(DB_FILE)
    setup_demo_data(db_manager)
    print("\nDatenbank wurde erfolgreich mit Demodaten initialisiert.")
    db_manager.close()
