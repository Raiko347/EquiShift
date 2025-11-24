# -*- coding: utf-8 -*-
"""
database_manager.py

Verwaltet alle Interaktionen mit der SQLite-Datenbank für den EquiShift.
Enthält die Logik für Mitglieder, Events, Schichten, Anhänge, automatische Planung
und das Migrations-System für zukünftige Updates.
"""
import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import random

class DatabaseManager:
    def __init__(self, db_path="EquiShift.db"):
        self.db_path = db_path
        self.conn = None
        self._connect()
        
        # 1. Basis-Struktur sicherstellen (für Neuinstallationen)
        self._create_tables()
        
        # 2. Updates/Migrationen prüfen (für bestehende Nutzer bei Updates)
        self._check_and_run_migrations()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print(f"Erfolgreich mit der Datenbank verbunden: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Fehler beim Verbinden mit der Datenbank: {e}")
            raise

    def _create_tables(self):
        """Erstellt die Grundstruktur der Datenbank (Version 1)."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            person_id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
            display_name TEXT NOT NULL UNIQUE, birth_date TEXT, street TEXT, postal_code TEXT, city TEXT,
            email TEXT, phone1 TEXT, phone2 TEXT, status TEXT NOT NULL DEFAULT 'Aktiv',
            entry_date TEXT, exit_date TEXT, notes TEXT
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS duty_types (
            duty_type_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
            description TEXT, is_protected INTEGER NOT NULL DEFAULT 0
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS person_duty_restrictions (
            person_id INTEGER NOT NULL, duty_type_id INTEGER NOT NULL,
            PRIMARY KEY (person_id, duty_type_id),
            FOREIGN KEY (person_id) REFERENCES persons (person_id) ON DELETE CASCADE,
            FOREIGN KEY (duty_type_id) REFERENCES duty_types (duty_type_id) ON DELETE CASCADE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS person_competencies (
            person_id INTEGER NOT NULL, duty_type_id INTEGER NOT NULL,
            is_team_leader INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (person_id, duty_type_id),
            FOREIGN KEY (person_id) REFERENCES persons (person_id) ON DELETE CASCADE,
            FOREIGN KEY (duty_type_id) REFERENCES duty_types (duty_type_id) ON DELETE CASCADE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, start_date TEXT NOT NULL,
            end_date TEXT, status TEXT NOT NULL DEFAULT 'In Planung'
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL,
            duty_type_id INTEGER NOT NULL, name TEXT NOT NULL, description TEXT,
            FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE,
            FOREIGN KEY (duty_type_id) REFERENCES duty_types (duty_type_id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            shift_id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER NOT NULL,
            shift_date TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL,
            required_people INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id) ON DELETE CASCADE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT, shift_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL, substitute_person_id INTEGER,
            attendance_status TEXT NOT NULL DEFAULT 'Geplant',
            FOREIGN KEY (shift_id) REFERENCES shifts (shift_id) ON DELETE CASCADE,
            FOREIGN KEY (person_id) REFERENCES persons (person_id),
            FOREIGN KEY (substitute_person_id) REFERENCES persons (person_id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_attachments (
            attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE
        );
        """)

        protected_duties = [
            ("Bar", "Ausschank und Kassieren an der Bar", 1),
            ("Kasse", "Zentrale Kasse für Wertmarken etc.", 1),
        ]
        seed_query = "INSERT OR IGNORE INTO duty_types (name, description, is_protected) VALUES (?, ?, ?)"
        cursor.executemany(seed_query, protected_duties)

        self.conn.commit()
        print("Tabellen und geschützte Dienste überprüft/erstellt.")

    # --- Migrations-Manager ---
    def _check_and_run_migrations(self):
        """
        Prüft die Datenbank-Version und führt notwendige Updates (Migrationen) durch.
        """
        cursor = self.conn.cursor()
        
        # 1. Aktuelle Version aus der DB lesen (Standard ist 0)
        cursor.execute("PRAGMA user_version")
        current_db_version = cursor.fetchone()[0]
        
        # Ziel-Version: Das ist die Version DIESES Codes (V1.0)
        TARGET_VERSION = 1 
        
        if current_db_version >= TARGET_VERSION:
            return # Alles aktuell

        print(f"Führe Datenbank-Migration durch: v{current_db_version} -> v{TARGET_VERSION}")

        try:
            cursor.execute("BEGIN TRANSACTION")

            # --- MIGRATIONEN (Platzhalter für die Zukunft) ---
            
            # BEISPIEL FÜR SPÄTER (Version 2 - Lagerverwaltung):
            # if current_db_version < 2:
            #     print("Migriere auf Version 2: Erstelle Lager-Tabellen...")
            #     cursor.execute("CREATE TABLE IF NOT EXISTS products (...)")
            
            # BEISPIEL FÜR SPÄTER (Version 3 - Abrechnung):
            # if current_db_version < 3:
            #     print("Migriere auf Version 3: Füge IBAN hinzu...")
            #     try:
            #         cursor.execute("ALTER TABLE persons ADD COLUMN iban TEXT")
            #     except sqlite3.OperationalError: pass

            # -------------------------------------------------

            # Neue Version setzen
            cursor.execute(f"PRAGMA user_version = {TARGET_VERSION}")
            cursor.execute("COMMIT")
            print("Migration erfolgreich abgeschlossen.")
            
        except sqlite3.Error as e:
            cursor.execute("ROLLBACK")
            print(f"KRITISCHER FEHLER bei der Migration: {e}")
            raise RuntimeError("Datenbank-Update fehlgeschlagen. Bitte Entwickler kontaktieren.")
    # -------------------------------

    def execute_query(self, query, params=(), fetch=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            if fetch == "one":
                return cursor.fetchone()
            if fetch == "all":
                return cursor.fetchall()
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Fehler bei der Abfrage: {e}\nQuery: {query}")
            self.conn.rollback()
            return None

    # --- Methoden für Personen ---
    def add_person(self, **kwargs):
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join("?" * len(kwargs))
        query = f"INSERT INTO persons ({cols}) VALUES ({placeholders})"
        return self.execute_query(query, tuple(kwargs.values()))

    def update_person(self, person_id, **kwargs):
        if "status" in kwargs:
            old_status_row = self.execute_query(
                "SELECT status FROM persons WHERE person_id = ?",
                (person_id,),
                fetch="one",
            )
            if old_status_row:
                old_status = old_status_row["status"]
                new_status = kwargs["status"]
                is_reactivated = (
                    old_status in ("Ruht", "Austritt")
                    and new_status == "Aktiv"
                )
                if is_reactivated:
                    self.execute_query(
                        "DELETE FROM assignments WHERE person_id = ? OR substitute_person_id = ?",
                        (person_id, person_id),
                    )
        updates = ", ".join([f"{key} = ?" for key in kwargs])
        query = f"UPDATE persons SET {updates} WHERE person_id = ?"
        return self.execute_query(query, tuple(kwargs.values()) + (person_id,))

    def delete_person(self, person_id):
        query = "DELETE FROM persons WHERE person_id = ?"
        return self.execute_query(query, (person_id,))

    def get_person_by_id(self, person_id):
        query = "SELECT * FROM persons WHERE person_id = ?"
        return self.execute_query(query, (person_id,), fetch="one")

    def get_all_persons(self):
        return self.execute_query(
            "SELECT * FROM persons ORDER BY last_name, first_name", fetch="all"
        )

    def import_members(self, members_data):
        added_count = 0
        skipped_count = 0
        existing_members_query = "SELECT lower(first_name), lower(last_name), lower(display_name) FROM persons"
        existing_rows = self.execute_query(existing_members_query, fetch="all")
        existing_names = {(row[0], row[1]) for row in existing_rows}
        existing_display_names = {row[2] for row in existing_rows}

        for member in members_data:
            processed_member = {}
            for k, v in member.items():
                if isinstance(v, (datetime, pd.Timestamp)):
                    processed_member[k] = v
                else:
                    processed_member[k] = str(v) if pd.notna(v) else ""
            member = processed_member

            first_name = member.get("first_name", "").strip()
            last_name = member.get("last_name", "").strip()

            if not first_name or not last_name:
                skipped_count += 1
                continue

            if (first_name.lower(), last_name.lower()) in existing_names:
                skipped_count += 1
                continue

            valid_cols = ["first_name", "last_name", "display_name", "birth_date", "street", "postal_code", "city", "email", "phone1", "phone2", "status", "entry_date", "notes"]
            person_data = {key: member.get(key) for key in valid_cols if member.get(key)}

            date_columns = ["birth_date", "entry_date"]
            for col in date_columns:
                if col in person_data and person_data[col]:
                    date_val = person_data[col]
                    try:
                        if isinstance(date_val, (datetime, pd.Timestamp)):
                            person_data[col] = date_val.strftime("%Y-%m-%d")
                        else:
                            date_obj = datetime.strptime(str(date_val), "%d.%m.%Y")
                            person_data[col] = date_obj.strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        person_data[col] = None

            display_name = person_data.get("display_name", "").strip()
            if not display_name:
                display_name = f"{first_name} {last_name[:1]}."
                i = 2
                while display_name.lower() in existing_display_names and i <= len(last_name):
                    display_name = f"{first_name} {last_name[:i]}."
                    i += 1
                original_display_name = display_name
                counter = 2
                while display_name.lower() in existing_display_names:
                    display_name = f"{original_display_name}{counter}"
                    counter += 1

            person_data["display_name"] = display_name
            if display_name.lower() in existing_display_names:
                skipped_count += 1
                continue

            existing_display_names.add(display_name.lower())
            self.add_person(**person_data)
            added_count += 1

        return added_count, skipped_count

    # --- Methoden für Dienst-Typen ---
    def add_duty_type(self, name, description=""):
        query = "INSERT INTO duty_types (name, description) VALUES (?, ?)"
        return self.execute_query(query, (name, description))

    def update_duty_type(self, duty_type_id, name, description):
        check_query = "SELECT is_protected FROM duty_types WHERE duty_type_id = ?"
        is_protected = self.execute_query(check_query, (duty_type_id,), fetch="one")[0]
        if is_protected:
            return None
        query = "UPDATE duty_types SET name = ?, description = ? WHERE duty_type_id = ?"
        return self.execute_query(query, (name, description, duty_type_id))

    def delete_duty_type(self, duty_type_id):
        check_query = "SELECT is_protected FROM duty_types WHERE duty_type_id = ?"
        is_protected = self.execute_query(check_query, (duty_type_id,), fetch="one")[0]
        if is_protected:
            return None
        query = "DELETE FROM duty_types WHERE duty_type_id = ?"
        return self.execute_query(query, (duty_type_id,))

    def get_duty_type_by_id(self, duty_type_id):
        query = "SELECT * FROM duty_types WHERE duty_type_id = ?"
        return self.execute_query(query, (duty_type_id,), fetch="one")

    def get_duty_type_by_name(self, name):
        query = "SELECT * FROM duty_types WHERE name = ?"
        return self.execute_query(query, (name,), fetch="one")

    def get_all_duty_types(self):
        return self.execute_query("SELECT * FROM duty_types ORDER BY name", fetch="all")

    def check_duty_type_usage(self, duty_type_id):
        restrictions_query = "SELECT COUNT(*) FROM person_duty_restrictions WHERE duty_type_id = ?"
        tasks_query = "SELECT COUNT(*) FROM tasks WHERE duty_type_id = ?"
        restrictions_count = self.execute_query(restrictions_query, (duty_type_id,), fetch="one")[0]
        tasks_count = self.execute_query(tasks_query, (duty_type_id,), fetch="one")[0]
        return {"restrictions": restrictions_count, "tasks": tasks_count}

    def get_person_restrictions(self, person_id):
        query = "SELECT duty_type_id FROM person_duty_restrictions WHERE person_id = ?"
        rows = self.execute_query(query, (person_id,), fetch="all")
        return [row["duty_type_id"] for row in rows] if rows else []

    def set_person_restrictions(self, person_id, duty_type_ids):
        if len(duty_type_ids) > 3:
            return
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("DELETE FROM person_duty_restrictions WHERE person_id = ?", (person_id,))
            for duty_id in duty_type_ids:
                cursor.execute("INSERT INTO person_duty_restrictions (person_id, duty_type_id) VALUES (?, ?)", (person_id, duty_id))
            cursor.execute("COMMIT")
        except sqlite3.Error:
            cursor.execute("ROLLBACK")

    def get_person_competencies(self, person_id):
        query = "SELECT duty_type_id, is_team_leader FROM person_competencies WHERE person_id = ?"
        rows = self.execute_query(query, (person_id,), fetch="all")
        return {row["duty_type_id"]: row["is_team_leader"] for row in rows} if rows else {}

    def set_person_competencies(self, person_id, competencies):
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("DELETE FROM person_competencies WHERE person_id = ?", (person_id,))
            for duty_id, is_tl in competencies.items():
                cursor.execute("INSERT INTO person_competencies (person_id, duty_type_id, is_team_leader) VALUES (?, ?, ?)", (person_id, duty_id, is_tl))
            cursor.execute("COMMIT")
        except sqlite3.Error:
            cursor.execute("ROLLBACK")

    # --- Events & Shifts ---
    def get_all_events(self):
        return self.execute_query("SELECT * FROM events ORDER BY start_date DESC", fetch="all")

    def get_event_by_id(self, event_id):
        return self.execute_query("SELECT * FROM events WHERE event_id = ?", (event_id,), fetch="one")

    def add_event(self, name, start_date, end_date=None, status="In Planung"):
        query = "INSERT INTO events (name, start_date, end_date, status) VALUES (?, ?, ?, ?)"
        return self.execute_query(query, (name, start_date, end_date, status))

    def update_event(self, event_id, **kwargs):
        updates = ", ".join([f"{key} = ?" for key in kwargs])
        query = f"UPDATE events SET {updates} WHERE event_id = ?"
        return self.execute_query(query, tuple(kwargs.values()) + (event_id,))

    def delete_event(self, event_id):
        return self.execute_query("DELETE FROM events WHERE event_id = ?", (event_id,))

    def get_tasks_for_event(self, event_id):
        return self.execute_query("SELECT * FROM tasks WHERE event_id = ? ORDER BY name", (event_id,), fetch="all")

    def get_shifts_for_task(self, task_id):
        query = """
            SELECT s.*, COUNT(a.assignment_id) as assigned_count
            FROM shifts s
            LEFT JOIN assignments a ON s.shift_id = a.shift_id
            WHERE s.task_id = ?
            GROUP BY s.shift_id
            ORDER BY s.shift_date, s.start_time
        """
        return self.execute_query(query, (task_id,), fetch="all")

    def add_shift(self, task_id, shift_date, start_time, end_time, required_people=1):
        query = "INSERT INTO shifts (task_id, shift_date, start_time, end_time, required_people) VALUES (?, ?, ?, ?, ?)"
        return self.execute_query(query, (task_id, shift_date, start_time, end_time, required_people))

    def add_task(self, event_id, duty_type_id, name, description=""):
        query = "INSERT INTO tasks (event_id, duty_type_id, name, description) VALUES (?, ?, ?, ?)"
        return self.execute_query(query, (event_id, duty_type_id, name, description))

    def get_task_by_id(self, task_id):
        return self.execute_query("SELECT * FROM tasks WHERE task_id = ?", (task_id,), fetch="one")

    def update_task(self, task_id, **kwargs):
        updates = ", ".join([f"{key} = ?" for key in kwargs])
        query = f"UPDATE tasks SET {updates} WHERE task_id = ?"
        return self.execute_query(query, tuple(kwargs.values()) + (task_id,))

    def delete_task(self, task_id):
        return self.execute_query("DELETE FROM tasks WHERE task_id = ?", (task_id,))

    def get_shift_by_id(self, shift_id):
        return self.execute_query("SELECT * FROM shifts WHERE shift_id = ?", (shift_id,), fetch="one")

    def update_shift(self, shift_id, **kwargs):
        updates = ", ".join([f"{key} = ?" for key in kwargs])
        query = f"UPDATE shifts SET {updates} WHERE shift_id = ?"
        return self.execute_query(query, tuple(kwargs.values()) + (shift_id,))

    def delete_shift(self, shift_id):
        return self.execute_query("DELETE FROM shifts WHERE shift_id = ?", (shift_id,))

    def assign_person_to_shift(self, person_id, shift_id):
        return self.execute_query("INSERT INTO assignments (person_id, shift_id) VALUES (?, ?)", (person_id, shift_id))

    def get_assigned_persons_for_shift(self, shift_id):
        query = """
            SELECT
                p.person_id,
                p.display_name,
                COALESCE(pc.is_team_leader, 0) AS is_team_leader,
                CASE WHEN pc.person_id IS NOT NULL THEN 1 ELSE 0 END AS has_competence
            FROM assignments a
            JOIN persons p ON a.person_id = p.person_id
            JOIN shifts s ON a.shift_id = s.shift_id
            JOIN tasks t ON s.task_id = t.task_id
            LEFT JOIN person_competencies pc ON p.person_id = pc.person_id AND t.duty_type_id = pc.duty_type_id
            WHERE a.shift_id = ?
            ORDER BY p.display_name;
        """
        return self.execute_query(query, (shift_id,), fetch='all')

    def remove_person_from_shift(self, person_id, shift_id):
        return self.execute_query("DELETE FROM assignments WHERE person_id = ? AND shift_id = ?", (person_id, shift_id))

    def get_available_helpers_for_shift(self, shift_id):
        shift_info = self.execute_query("SELECT s.shift_date, s.start_time, s.end_time, t.duty_type_id, t.event_id FROM shifts s JOIN tasks t ON s.task_id = t.task_id WHERE s.shift_id = ?", (shift_id,), fetch='one')
        if not shift_info: return []
        
        shift_date, start_time, end_time, duty_type_id, event_id = shift_info['shift_date'], shift_info['start_time'], shift_info['end_time'], shift_info['duty_type_id'], shift_info['event_id']
        
        new_start = datetime.strptime(f"{shift_date} {start_time}", "%Y-%m-%d %H:%M")
        new_end = datetime.strptime(f"{shift_date} {end_time}", "%Y-%m-%d %H:%M")
        if new_end <= new_start: new_end += timedelta(days=1)

        potential_helpers = self.execute_query("""
            SELECT p.person_id, p.display_name, p.status 
            FROM persons p 
            WHERE p.status IN ('Aktiv', 'Passiv') 
              AND NOT EXISTS (SELECT 1 FROM person_duty_restrictions WHERE person_id = p.person_id AND duty_type_id = ?) 
              AND NOT EXISTS (SELECT 1 FROM assignments WHERE person_id = p.person_id AND shift_id = ?)
        """, (duty_type_id, shift_id), fetch='all')
        
        if not potential_helpers: return []

        all_assignments = self.execute_query("""
            SELECT a.person_id, s.shift_date, s.start_time, s.end_time 
            FROM assignments a 
            JOIN shifts s ON a.shift_id = s.shift_id 
            JOIN tasks t ON s.task_id = t.task_id 
            WHERE t.event_id = ?
        """, (event_id,), fetch='all')
        
        person_schedule = defaultdict(list)
        duties_count = defaultdict(int)
        
        for row in all_assignments:
            s_start = datetime.strptime(f"{row['shift_date']} {row['start_time']}", "%Y-%m-%d %H:%M")
            s_end = datetime.strptime(f"{row['shift_date']} {row['end_time']}", "%Y-%m-%d %H:%M")
            if s_end <= s_start: s_end += timedelta(days=1)
            
            person_schedule[row['person_id']].append((s_start, s_end))
            duties_count[row['person_id']] += 1

        final_list = []
        for helper in potential_helpers:
            pid = helper['person_id']
            has_overlap = False
            consecutive_warning = False
            
            for s_start, s_end in person_schedule.get(pid, []):
                if new_start < s_end and new_end > s_start:
                    has_overlap = True
                    break
                if new_start == s_end or new_end == s_start:
                    consecutive_warning = True
            
            if has_overlap: continue

            warnings = []
            if consecutive_warning:
                warnings.append("Keine Pause")
            if duties_count[pid] >= 2:
                warnings.append(f"{duties_count[pid]} Dienste")

            competence = self.execute_query("SELECT is_team_leader FROM person_competencies WHERE person_id = ? AND duty_type_id = ?", (pid, duty_type_id), fetch='one')
            
            final_list.append({
                'person_id': pid,
                'display_name': helper['display_name'],
                'status': helper['status'],
                'has_competence': 1 if competence else 0,
                'is_team_leader': competence['is_team_leader'] if competence else 0,
                'warnings': ", ".join(warnings)
            })
        
        final_list.sort(key=lambda x: (x['is_team_leader'], x['has_competence'], len(x['warnings']) == 0, x['display_name']), reverse=True)
        return final_list

    def update_assignment_status(self, assignment_id, status, substitute_id=None):
        valid_stati = ["Geplant", "Erledigt", "Erledigt (durch Vertreter)", "Nicht Erschienen", "Entschuldigt"]
        if status not in valid_stati:
            return None
        query = "UPDATE assignments SET attendance_status = ?, substitute_person_id = ? WHERE assignment_id = ?"
        return self.execute_query(query, (status, substitute_id, assignment_id))

    def calculate_scores(self, include_inactive=False, limit=None):
        query = """
            SELECT p.person_id, p.display_name, p.status,
                   a.attendance_status, a.substitute_person_id,
                   e.start_date
            FROM persons p
            LEFT JOIN assignments a ON p.person_id = a.person_id OR p.person_id = a.substitute_person_id
            LEFT JOIN shifts s ON a.shift_id = s.shift_id
            LEFT JOIN tasks t ON s.task_id = t.task_id
            LEFT JOIN events e ON t.event_id = e.event_id
            ORDER BY p.person_id, e.start_date DESC
        """
        all_assignments = self.execute_query(query, fetch="all")
        if not all_assignments:
            return []

        scores = {}
        person_duties_count = {}

        for row in all_assignments:
            person_id = row["person_id"]
            if person_id not in scores:
                scores[person_id] = {"name": row["display_name"], "status": row["status"], "total_score": 0}
                person_duties_count[person_id] = 0

            if row["attendance_status"]:
                person_duties_count[person_id] += 1
                if limit and person_duties_count[person_id] > limit:
                    continue

                score_change = 0
                if row["substitute_person_id"] == person_id:
                    score_change = 1
                elif row["person_id"] == person_id:
                    if row["attendance_status"] == "Erledigt":
                        score_change = 1
                    elif row["attendance_status"] == "Nicht Erschienen":
                        score_change = -2
                scores[person_id]["total_score"] += score_change

        final_scores = []
        for person_id, data in scores.items():
            if include_inactive or data["status"] in ("Aktiv", "Passiv"):
                final_scores.append(data)
        final_scores.sort(key=lambda x: x["total_score"], reverse=True)
        return final_scores

    def calculate_worked_hours(self, time_filter='all'):
        query = """
            WITH worked_shifts AS (
                SELECT a.person_id, s.start_time, s.end_time, e.start_date
                FROM assignments a JOIN shifts s ON a.shift_id = s.shift_id JOIN tasks t ON s.task_id = t.task_id JOIN events e ON t.event_id = e.event_id
                WHERE a.attendance_status = 'Erledigt'
                UNION ALL
                SELECT a.substitute_person_id AS person_id, s.start_time, s.end_time, e.start_date
                FROM assignments a JOIN shifts s ON a.shift_id = s.shift_id JOIN tasks t ON s.task_id = t.task_id JOIN events e ON t.event_id = e.event_id
                WHERE a.attendance_status = 'Erledigt (durch Vertreter)'
            )
            SELECT p.display_name AS name,
                   SUM(
                       CASE
                           WHEN ws.end_time < ws.start_time THEN
                               (strftime('%s', '2000-01-02 ' || ws.end_time || ':00') - strftime('%s', '2000-01-01 ' || ws.start_time || ':00')) / 3600.0
                           ELSE
                               (strftime('%s', '2000-01-01 ' || ws.end_time || ':00') - strftime('%s', '2000-01-01 ' || ws.start_time || ':00')) / 3600.0
                       END
                   ) AS total_hours
            FROM persons p JOIN worked_shifts ws ON p.person_id = ws.person_id
            {where_clause}
            GROUP BY p.person_id HAVING total_hours > 0
            ORDER BY total_hours DESC, name ASC;
        """
        where_clause = ""
        if time_filter == 'current_year':
            where_clause = "WHERE strftime('%Y', ws.start_date) = strftime('%Y', 'now')"
        final_query = query.format(where_clause=where_clause)
        return self.execute_query(final_query, fetch='all')

    def get_detailed_member_summary(self, time_filter='all'):
        query = """
            WITH assignments_with_hours AS (
                SELECT
                    a.person_id, a.substitute_person_id, a.attendance_status, e.start_date,
                    CASE
                        WHEN s.end_time < s.start_time THEN
                            (strftime('%s', '2000-01-02 ' || s.end_time || ':00') - strftime('%s', '2000-01-01 ' || s.start_time || ':00')) / 3600.0
                        ELSE
                            (strftime('%s', '2000-01-01 ' || s.end_time || ':00') - strftime('%s', '2000-01-01 ' || s.start_time || ':00')) / 3600.0
                    END AS hours
                FROM assignments a
                JOIN shifts s ON a.shift_id = s.shift_id
                JOIN tasks t ON s.task_id = t.task_id
                JOIN events e ON t.event_id = e.event_id
                {where_clause}
            ),
            person_rollup AS (
                SELECT person_id, 'original' as type, attendance_status, hours FROM assignments_with_hours
                UNION ALL
                SELECT substitute_person_id, 'substitute' as type, attendance_status, hours FROM assignments_with_hours WHERE substitute_person_id IS NOT NULL
            )
            SELECT
                p.display_name AS name,
                COALESCE(SUM(CASE WHEN pr.type = 'original' AND pr.attendance_status = 'Erledigt' THEN pr.hours ELSE 0 END) +
                         SUM(CASE WHEN pr.type = 'substitute' AND pr.attendance_status = 'Erledigt (durch Vertreter)' THEN pr.hours ELSE 0 END), 0) AS total_hours,
                COALESCE(SUM(CASE WHEN pr.type = 'original' AND pr.attendance_status = 'Erledigt' THEN 1 ELSE 0 END), 0) AS total_done,
                COALESCE(SUM(CASE WHEN pr.type = 'substitute' AND pr.attendance_status = 'Erledigt (durch Vertreter)' THEN 1 ELSE 0 END), 0) AS total_substitute,
                COALESCE(SUM(CASE WHEN pr.type = 'original' AND pr.attendance_status = 'Entschuldigt' THEN 1 ELSE 0 END), 0) AS total_excused,
                COALESCE(SUM(CASE WHEN pr.type = 'original' AND pr.attendance_status = 'Nicht Erschienen' THEN 1 ELSE 0 END), 0) AS total_absent
            FROM persons p
            LEFT JOIN person_rollup pr ON p.person_id = pr.person_id
            WHERE p.status IN ('Aktiv', 'Passiv')
            GROUP BY p.person_id
            ORDER BY total_hours DESC, name ASC;
        """
        where_clause = ""
        if time_filter == 'current_year':
            where_clause = "WHERE strftime('%Y', start_date) = strftime('%Y', 'now')"
        final_query = query.format(where_clause=where_clause)
        rows = self.execute_query(final_query, fetch='all')
        return [dict(row) for row in rows] if rows else []

    def get_event_staffing_summary(self, event_id):
        query = """
            SELECT
                (SELECT COALESCE(SUM(s.required_people), 0) FROM shifts s JOIN tasks t ON s.task_id = t.task_id WHERE t.event_id = ?) AS total_required,
                (SELECT COALESCE(COUNT(a.assignment_id), 0) FROM assignments a JOIN shifts s ON a.shift_id = s.shift_id JOIN tasks t ON s.task_id = t.task_id WHERE t.event_id = ?) AS total_assigned
        """
        summary = self.execute_query(query, (event_id, event_id), fetch="one")
        if summary:
            return summary["total_required"], summary["total_assigned"]
        return 0, 0

    def check_team_leader_compliance(self, event_id):
        query = """
            SELECT s.shift_id
            FROM shifts s JOIN tasks t ON s.task_id = t.task_id
            WHERE t.event_id = ?
              AND (SELECT COUNT(a.assignment_id) FROM assignments a WHERE a.shift_id = s.shift_id) > 0
              AND NOT EXISTS (
                  SELECT 1 FROM assignments a
                  JOIN persons p ON a.person_id = p.person_id
                  JOIN person_competencies pc ON p.person_id = pc.person_id
                  WHERE a.shift_id = s.shift_id
                    AND pc.duty_type_id = t.duty_type_id
                    AND pc.is_team_leader = 1
              )
        """
        rows = self.execute_query(query, (event_id,), fetch="all")
        return [row["shift_id"] for row in rows]

    def clear_assignments_for_event(self, event_id):
        query = "DELETE FROM assignments WHERE shift_id IN (SELECT s.shift_id FROM shifts s JOIN tasks t ON s.task_id = t.task_id WHERE t.event_id = ?)"
        self.execute_query(query, (event_id,))

    # --- Methoden für Anhänge ---
    def add_attachment(self, event_id, file_path):
        count_query = "SELECT COUNT(*) FROM event_attachments WHERE event_id = ?"
        count = self.execute_query(count_query, (event_id,), fetch="one")[0]
        query = "INSERT INTO event_attachments (event_id, file_path, position) VALUES (?, ?, ?)"
        return self.execute_query(query, (event_id, file_path, count))

    def get_attachments_for_event(self, event_id):
        query = "SELECT * FROM event_attachments WHERE event_id = ? ORDER BY position"
        return self.execute_query(query, (event_id,), fetch="all")

    def delete_attachment(self, attachment_id):
        return self.execute_query("DELETE FROM event_attachments WHERE attachment_id = ?", (attachment_id,))
        
    def update_attachment_order(self, attachment_id, new_position):
        return self.execute_query("UPDATE event_attachments SET position = ? WHERE attachment_id = ?", (new_position, attachment_id))

    # --- Event Kopieren (Mit Anhängen & ID-Rückgabe) ---
    def copy_event(self, source_event_id, new_name, new_start_date_str, mode):
        """
        Kopiert ein Event.
        Rückgabe: (success: bool, message: str, new_event_id: int|None, attachments_copied: bool)
        """
        source_event = self.get_event_by_id(source_event_id)
        if not source_event: 
            return False, "Quell-Event nicht gefunden.", None, False

        try:
            old_start = datetime.strptime(source_event['start_date'], "%Y-%m-%d")
            new_start = datetime.strptime(new_start_date_str, "%Y-%m-%d")
            delta = new_start - old_start

            new_end_date_str = None
            if source_event['end_date']:
                old_end = datetime.strptime(source_event['end_date'], "%Y-%m-%d")
                new_end = old_end + delta
                new_end_date_str = new_end.strftime("%Y-%m-%d")

            cursor = self.conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            cursor.execute(
                "INSERT INTO events (name, start_date, end_date, status) VALUES (?, ?, ?, 'In Planung')",
                (new_name, new_start_date_str, new_end_date_str)
            )
            new_event_id = cursor.lastrowid

            cursor.execute("SELECT * FROM event_attachments WHERE event_id = ? ORDER BY position", (source_event_id,))
            attachments = cursor.fetchall()
            attachments_copied = False
            
            if attachments:
                for att in attachments:
                    cursor.execute(
                        "INSERT INTO event_attachments (event_id, file_path, position) VALUES (?, ?, ?)",
                        (new_event_id, att['file_path'], att['position'])
                    )
                attachments_copied = True

            cursor.execute("SELECT * FROM tasks WHERE event_id = ?", (source_event_id,))
            tasks = cursor.fetchall()

            for task in tasks:
                cursor.execute(
                    "INSERT INTO tasks (event_id, duty_type_id, name, description) VALUES (?, ?, ?, ?)",
                    (new_event_id, task['duty_type_id'], task['name'], task['description'])
                )
                new_task_id = cursor.lastrowid

                if mode == 'structure': continue

                cursor.execute("SELECT * FROM shifts WHERE task_id = ?", (task['task_id'],))
                shifts = cursor.fetchall()

                for shift in shifts:
                    old_shift_date = datetime.strptime(shift['shift_date'], "%Y-%m-%d")
                    new_shift_date = old_shift_date + delta
                    new_shift_date_str = new_shift_date.strftime("%Y-%m-%d")

                    cursor.execute(
                        """INSERT INTO shifts (task_id, shift_date, start_time, end_time, required_people) 
                           VALUES (?, ?, ?, ?, ?)""",
                        (new_task_id, new_shift_date_str, shift['start_time'], shift['end_time'], shift['required_people'])
                    )
                    new_shift_id = cursor.lastrowid

                    if mode != 'full': continue

                    cursor.execute("SELECT * FROM assignments WHERE shift_id = ?", (shift['shift_id'],))
                    assignments = cursor.fetchall()

                    for assign in assignments:
                        cursor.execute(
                            "INSERT INTO assignments (shift_id, person_id, attendance_status) VALUES (?, ?, 'Geplant')",
                            (new_shift_id, assign['person_id'])
                        )

            cursor.execute("COMMIT")
            print(f"Event ID {source_event_id} erfolgreich kopiert nach ID {new_event_id}")
            
            return True, f"Event erfolgreich als '{new_name}' kopiert.", new_event_id, attachments_copied

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"Fehler beim Kopieren: {e}")
            return False, str(e), None, False

    def generate_planning_proposal(self, event_id, limit=None):
        all_scores = self.calculate_scores(include_inactive=True, limit=limit)
        score_map = {score['name']: score['total_score'] for score in all_scores}
        
        duties_per_person = defaultdict(int)
        person_shift_times = defaultdict(list) 

        all_shifts_query = "SELECT s.shift_id, s.shift_date, s.start_time, s.end_time FROM shifts s JOIN tasks t ON s.task_id = t.task_id WHERE t.event_id = ? ORDER BY s.shift_date, s.start_time"
        all_shifts = self.execute_query(all_shifts_query, (event_id,), fetch='all')

        def get_datetime_range(date_str, start_str, end_str):
            start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            return start_dt, end_dt

        def calculate_candidate_score(candidate, current_start, current_end, is_tl_search=False):
            person_id = candidate['person_id']
            historical_score = score_map.get(candidate['display_name'], 0)
            base_points = historical_score * -1 * 10 
            current_event_duties = duties_per_person[person_id]
            fairness_malus = current_event_duties * 25
            if current_event_duties >= 2:
                fairness_malus += 10000 
            consecutive_malus = 0
            for s_start, s_end in person_shift_times[person_id]:
                if current_start == s_end or current_end == s_start:
                    consecutive_malus += 10000
            status_bonus = 5 if candidate['status'] == 'Aktiv' else 0
            competence_bonus = 0
            if not is_tl_search and candidate['has_competence']:
                competence_bonus = 3
            tl_waste_malus = 0
            if not is_tl_search and candidate['is_team_leader']:
                tl_waste_malus = 500
            final_score = base_points - fairness_malus - consecutive_malus + status_bonus + competence_bonus - tl_waste_malus
            return final_score

        for shift_row in all_shifts:
            shift_id = shift_row['shift_id']
            current_start, current_end = get_datetime_range(shift_row['shift_date'], shift_row['start_time'], shift_row['end_time'])
            assigned_persons = self.get_assigned_persons_for_shift(shift_id)
            has_tl = any(p['is_team_leader'] for p in assigned_persons)
            shift_details = self.get_shift_by_id(shift_id)
            is_full = len(assigned_persons) >= shift_details['required_people']
            if has_tl or is_full: continue
            available_helpers = self.get_available_helpers_for_shift(shift_id)
            tl_candidates = [h for h in available_helpers if h['is_team_leader']]
            if not tl_candidates: continue
            scored_candidates = []
            for candidate in tl_candidates:
                score = calculate_candidate_score(candidate, current_start, current_end, is_tl_search=True)
                scored_candidates.append((score, candidate))
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            if scored_candidates:
                best_score = scored_candidates[0][0]
                if best_score < -5000: continue 
                top_tier = [c for s, c in scored_candidates if s >= best_score - 5]
                chosen_one = random.choice(top_tier)
                person_id = chosen_one['person_id']
                self.assign_person_to_shift(person_id, shift_id)
                duties_per_person[person_id] += 1
                person_shift_times[person_id].append((current_start, current_end))

        for shift_row in all_shifts:
            shift_id = shift_row['shift_id']
            current_start, current_end = get_datetime_range(shift_row['shift_date'], shift_row['start_time'], shift_row['end_time'])
            shift_details = self.get_shift_by_id(shift_id)
            assigned_count = len(self.get_assigned_persons_for_shift(shift_id))
            num_open = shift_details['required_people'] - assigned_count
            if num_open <= 0: continue
            for _ in range(num_open):
                available_helpers = self.get_available_helpers_for_shift(shift_id)
                if not available_helpers: break
                scored_candidates = []
                for helper in available_helpers:
                    score = calculate_candidate_score(helper, current_start, current_end, is_tl_search=False)
                    scored_candidates.append((score, helper))
                scored_candidates.sort(key=lambda x: x[0], reverse=True)
                if scored_candidates:
                    best_score = scored_candidates[0][0]
                    if best_score < -5000: break
                    top_tier = [c for s, c in scored_candidates if s >= best_score - 8]
                    chosen_one = random.choice(top_tier)
                    person_id = chosen_one['person_id']
                    self.assign_person_to_shift(person_id, shift_id)
                    duties_per_person[person_id] += 1
                    person_shift_times[person_id].append((current_start, current_end))

        total_required, total_assigned = self.get_event_staffing_summary(event_id)
        return total_assigned, total_required

    def validate_event_plan(self, event_id):
        warnings = []
        query_occupancy = """
            SELECT 
                t.name AS task_name, 
                s.shift_date, s.start_time, s.required_people,
                (SELECT COUNT(*) FROM assignments a WHERE a.shift_id = s.shift_id) AS current_count
            FROM shifts s
            JOIN tasks t ON s.task_id = t.task_id
            WHERE t.event_id = ?
            ORDER BY s.shift_date, s.start_time
        """
        shifts_status = self.execute_query(query_occupancy, (event_id,), fetch='all')
        for shift in shifts_status:
            if shift['current_count'] == 0:
                warnings.append(f"🔴 Schicht '{shift['task_name']}' ({shift['start_time']}) ist komplett leer.")
            elif shift['current_count'] < shift['required_people']:
                warnings.append(f"⚠️ Schicht '{shift['task_name']}' ({shift['start_time']}) ist unterbesetzt ({shift['current_count']}/{shift['required_people']}).")

        query_assignments = """
            SELECT 
                p.person_id, p.display_name, 
                s.shift_date, s.start_time, s.end_time, 
                t.name as task_name, t.duty_type_id,
                s.shift_id
            FROM assignments a
            JOIN persons p ON a.person_id = p.person_id
            JOIN shifts s ON a.shift_id = s.shift_id
            JOIN tasks t ON s.task_id = t.task_id
            WHERE t.event_id = ?
            ORDER BY p.display_name, s.shift_date, s.start_time
        """
        assignments = self.execute_query(query_assignments, (event_id,), fetch='all')
        person_shifts = defaultdict(list)
        for row in assignments:
            start_dt = datetime.strptime(f"{row['shift_date']} {row['start_time']}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{row['shift_date']} {row['end_time']}", "%Y-%m-%d %H:%M")
            if end_dt <= start_dt: end_dt += timedelta(days=1)
            shift_data = {'start': start_dt, 'end': end_dt, 'task': row['task_name'], 'duty_id': row['duty_type_id'], 'shift_id': row['shift_id']}
            person_shifts[row['person_id']].append(shift_data)
            restrictions = self.get_person_restrictions(row['person_id'])
            if row['duty_type_id'] in restrictions:
                warnings.append(f"🔴 {row['display_name']} ist für '{row['task_name']}' eingeteilt, obwohl eine Einschränkung vorliegt.")

        for person_id, shifts in person_shifts.items():
            name = next(x['display_name'] for x in assignments if x['person_id'] == person_id)
            shifts.sort(key=lambda x: x['start'])
            for i in range(len(shifts)):
                current = shifts[i]
                for j in range(i + 1, len(shifts)):
                    other = shifts[j]
                    if current['start'] < other['end'] and current['end'] > other['start']:
                        warnings.append(f"🔴 {name} hat zeitgleiche Schichten: '{current['task']}' und '{other['task']}'.")
                    if current['end'] == other['start']:
                        warnings.append(f"⚠️ {name} arbeitet durchgehend (ohne Pause): '{current['task']}' -> '{other['task']}'.")
            if len(shifts) > 2:
                warnings.append(f"⚠️ {name} ist für {len(shifts)} Schichten eingeteilt (Empfohlen: Max 2).")

        missing_tl_shifts = self.check_team_leader_compliance(event_id)
        for shift_id in missing_tl_shifts:
            details = self.execute_query("SELECT t.name, s.shift_date, s.start_time FROM shifts s JOIN tasks t ON s.task_id = t.task_id WHERE s.shift_id = ?", (shift_id,), fetch='one')
            warnings.append(f"⚠️ Schicht '{details['name']}' ({details['start_time']}) hat keinen zugewiesenen Teamleiter.")

        return warnings

    def get_plan_matrix_data(self, event_id):
        return self.execute_query("SELECT t.name AS task_name, s.shift_date, s.start_time, s.end_time, s.required_people, p.display_name AS helper_name, COALESCE(pc.is_team_leader, 0) AS is_team_leader, CASE WHEN pc.person_id IS NOT NULL THEN 1 ELSE 0 END AS has_competence FROM tasks t JOIN shifts s ON t.task_id = s.task_id LEFT JOIN assignments a ON s.shift_id = a.shift_id LEFT JOIN persons p ON a.person_id = p.person_id LEFT JOIN person_competencies pc ON p.person_id = pc.person_id AND t.duty_type_id = pc.duty_type_id WHERE t.event_id = ? ORDER BY t.name, s.shift_date, s.start_time;", (event_id,), fetch='all')

    def get_export_data_for_event(self, event_id, filter_date=None, filter_task_id=None):
        q = "SELECT t.name AS aufgabe, s.shift_date, s.start_time, s.end_time, s.required_people, p.display_name AS helfer, p.phone1 AS telefon FROM tasks t JOIN shifts s ON t.task_id = s.task_id LEFT JOIN assignments a ON s.shift_id = a.shift_id LEFT JOIN persons p ON a.person_id = p.person_id WHERE t.event_id = ?"; p = [event_id]
        if filter_date: q += " AND s.shift_date = ?"; p.append(filter_date)
        if filter_task_id: q += " AND t.task_id = ?"; p.append(filter_task_id)
        q += " ORDER BY s.shift_date, s.start_time, t.name, p.display_name;"
        return self.execute_query(q, tuple(p), fetch='all')

    def get_gantt_data_for_event(self, event_id):
        return self.execute_query("SELECT t.name AS task_name, s.shift_date, s.start_time, s.end_time, GROUP_CONCAT(p.display_name, ', ') AS assigned_helpers FROM tasks t JOIN shifts s ON t.task_id = s.task_id LEFT JOIN assignments a ON s.shift_id = a.shift_id LEFT JOIN persons p ON a.person_id = p.person_id WHERE t.event_id = ? GROUP BY s.shift_id ORDER BY t.name, s.shift_date, s.start_time;", (event_id,), fetch="all")

    def get_assignments_for_event(self, event_id):
        return self.execute_query("SELECT a.assignment_id, t.name AS task_name, s.shift_date, s.start_time, s.end_time, p.display_name AS person_name, a.attendance_status, sub_p.display_name AS substitute_name FROM assignments a JOIN shifts s ON a.shift_id = s.shift_id JOIN tasks t ON s.task_id = t.task_id JOIN persons p ON a.person_id = p.person_id LEFT JOIN persons sub_p ON a.substitute_person_id = sub_p.person_id WHERE t.event_id = ? ORDER BY s.shift_date, s.start_time, t.name, p.display_name;", (event_id,), fetch="all")

    def get_post_event_data(self, event_id, filter_task_id=None):
        q = "SELECT t.name AS task_name, s.shift_date, s.start_time, s.end_time, p.display_name AS helper_name FROM assignments a JOIN persons p ON a.person_id = p.person_id JOIN shifts s ON a.shift_id = s.shift_id JOIN tasks t ON s.task_id = t.task_id WHERE t.event_id = ?"; p = [event_id]
        if filter_task_id: q += " AND t.task_id = ?"; p.append(filter_task_id)
        q += " ORDER BY t.name, s.shift_date, s.start_time, p.display_name;"
        return self.execute_query(q, tuple(p), fetch='all')

    def get_all_members_with_details(self):
        members = self.get_all_persons()
        duty_types = self.get_all_duty_types()
        members_list = [dict(m) for m in members]
        for member in members_list:
            restrictions = self.get_person_restrictions(member['person_id'])
            competencies = self.get_person_competencies(member['person_id'])
            for dt in duty_types:
                member[dt['name']] = ''
            for dt in duty_types:
                if dt['duty_type_id'] in restrictions:
                    member[dt['name']] = 'Eingeschränkt'
            for dt_id, is_tl in competencies.items():
                dt_name = next((dt['name'] for dt in duty_types if dt['duty_type_id'] == dt_id), None)
                if dt_name:
                    if is_tl:
                        member[dt_name] = 'Teamleiter'
                    else:
                        member[dt_name] = 'Kompetenz'
        return members_list, [dt['name'] for dt in duty_types]

    def get_completed_events(self):
        return self.execute_query("SELECT * FROM events WHERE status IN ('Abgeschlossen', 'Aktiv') ORDER BY start_date DESC", fetch='all')

    def get_hours_and_duties_summary(self, time_filter='all'):
        q = "WITH worked_shifts AS (SELECT a.person_id, s.start_time, s.end_time, e.start_date FROM assignments a JOIN shifts s ON a.shift_id = s.shift_id JOIN tasks t ON s.task_id = t.task_id JOIN events e ON t.event_id = e.event_id WHERE a.attendance_status = 'Erledigt' UNION ALL SELECT a.substitute_person_id AS person_id, s.start_time, s.end_time, e.start_date FROM assignments a JOIN shifts s ON a.shift_id = s.shift_id JOIN tasks t ON s.task_id = t.task_id JOIN events e ON t.event_id = e.event_id WHERE a.attendance_status = 'Erledigt (durch Vertreter)') SELECT p.display_name AS name, COUNT(*) as duty_count, SUM(CASE WHEN ws.end_time < ws.start_time THEN (strftime('%s', '2000-01-02 ' || ws.end_time || ':00') - strftime('%s', '2000-01-01 ' || ws.start_time || ':00')) / 3600.0 ELSE (strftime('%s', '2000-01-01 ' || ws.end_time || ':00') - strftime('%s', '2000-01-01 ' || ws.start_time || ':00')) / 3600.0 END) AS total_hours FROM persons p JOIN worked_shifts ws ON p.person_id = ws.person_id {where} GROUP BY p.person_id ORDER BY total_hours DESC, name ASC;"
        w = "WHERE strftime('%Y', ws.start_date) = strftime('%Y', 'now')" if time_filter == 'current_year' else ""
        rows = self.execute_query(q.format(where=w), fetch='all')
        return [dict(row) for row in rows] if rows else []
    
    def get_database_version(self):
        """Liest die aktuelle Version der Datenbank-Struktur aus."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA user_version")
            return cursor.fetchone()[0]
        except Exception:
            return "Unbekannt"

    def close(self):
        if self.conn:
            self.conn.close()
            print("Datenbankverbindung geschlossen.")