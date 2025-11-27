# 🚀 EquiShift - Der intelligente Vereinsplaner

**EquiShift** ist eine leistungsstarke Desktop-Anwendung zur Verwaltung von Vereinsmitgliedern, Events und zur fairen, automatisierten Schichtplanung. 

Entwickelt, um die Organisation komplexer Vereinsfeste (wie Sommerfeste, Turniere oder Narrentreffen) drastisch zu vereinfachen und gleichzeitig die Belastung der ehrenamtlichen Helfer fair zu verteilen.

---

## ✨ Features

### 👥 Mitgliederverwaltung
*   **Stammdaten:** Verwaltung aller relevanten Kontaktdaten.
*   **Kompetenzen:** Zuweisung von Spezialfähigkeiten (z.B. "Darf Kasse bedienen") und **Teamleiter-Status**.
*   **Einschränkungen:** Definition von Diensten, die ein Mitglied *nicht* übernehmen kann (z.B. gesundheitliche Gründe).
*   **Import/Export:** Massenimport via Excel/CSV und Export der Mitgliederlisten.

### 📅 Event-Management
*   **Status-Workflow:** Events durchlaufen Phasen (In Planung -> Aktiv -> Abgeschlossen -> Abgesagt).
*   **Smart Copy (Cloning):** Kopieren kompletter Events (z.B. vom Vorjahr) inklusive Struktur, Schichten und Helfern. Das Datum wird dabei automatisch intelligent verschoben.
*   **Dokumenten-Management:** Hinterlegen von PDF-Anhängen (z.B. Hygieneverordnungen, Lagepläne) direkt am Event.

### 🧠 Intelligente Schichtplanung
Das Herzstück der Anwendung. Der Planungs-Algorithmus sorgt für Fairness und Gesundheitsschutz:
*   **Fairness-Score:** Bevorzugt Mitglieder, die bisher wenig geleistet haben (Bonus/Malus-System).
*   **Ressourcen-Schonung:** Teamleiter werden gezielt eingesetzt und nicht für einfache Tätigkeiten "verschwendet", solange andere Helfer verfügbar sind.
*   **Gesundheitsschutz:** Erzwingt Pausen zwischen Schichten (keine Doppelschichten).
*   **Lastenverteilung:** Versucht, eine maximale Anzahl an Schichten pro Person (Standard: 2) nicht zu überschreiten.

### 🛡️ Qualitätssicherung ("Der Wächter")
Ein integriertes Validierungs-Modul prüft den Dienstplan in Echtzeit auf:
*   Unterbesetzte oder leere Schichten.
*   Fehlende Teamleiter in kritischen Bereichen.
*   Verstöße gegen Ruhezeiten oder Einschränkungen.

### 🖨️ Reporting & Export
*   **Profi-PDF-Export:** Erstellt übersichtliche Dienstpläne (Matrix-Ansicht) und **fügt automatisch alle hinterlegten Event-Anhänge** (Sicherheitsvorschriften etc.) zu einer einzigen, druckfertigen Datei zusammen.
*   **Excel-Export:** Detaillierte Stundenübersichten und Nachweise.
*   **Nachbereitung:** Erfassung der tatsächlich geleisteten Stunden inkl. Vertretungs-Management.

### 💾 Technik
*   **Datenbank:** SQLite mit automatischem **Migrations-System** (Updatesicher auch bei zukünftigen Erweiterungen).
*   **GUI:** Moderne Oberfläche basierend auf PyQt5.

---

## 🛠️ Installation & Start

### Voraussetzungen
*   Python 3.10 oder höher

### Einrichtung

1.  **Repository klonen:**
    ```bash
    git clone https://github.com/DeinUsername/EquiShift.git
    cd EquiShift
    ```

2.  **Abhängigkeiten installieren:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Benötigte Pakete: `PyQt5`, `pandas`, `openpyxl`, `reportlab`, `pypdf`)*

3.  **Starten:**
    ```bash
    python main.py
    ```

---

## 📸 Screenshots

<img width="1126" height="737" alt="05-Auswertungen" src="https://github.com/user-attachments/assets/39a1f119-cbd6-4909-9b81-b6d698b59af6" />
<img width="1127" height="737" alt="04-Nachbereitung" src="https://github.com/user-attachments/assets/a212aba8-5fca-4c85-82f6-3baa257de9eb" />
<img width="1127" height="737" alt="03-Schichtplanung" src="https://github.com/user-attachments/assets/390f81c0-550a-4dbb-8a29-52fb3c76af5d" />
<img width="1126" height="736" alt="02-Events verwalten" src="https://github.com/user-attachments/assets/68d908f4-8eb5-4b1b-b3ac-ddc650c25953" />
<img width="1126" height="736" alt="01-Dienst-Typen verwalten" src="https://github.com/user-attachments/assets/1008b4b2-081c-4525-8f42-ea2c63e86ce4" />

---

## ⚖️ Haftungsausschluss (Disclaimer)

Die Software "EquiShift" wird "wie besehen" (as is) zur Verfügung gestellt, ohne jegliche Gewährleistung, weder ausdrücklich noch stillschweigend. Die Nutzung erfolgt auf eigenes Risiko. Der Entwickler haftet nicht für Schäden, Datenverluste, fehlerhafte Planungen oder daraus resultierende Folgen (z. B. Einnahmeausfälle oder Verstöße gegen Sicherheitsauflagen). Die Prüfung der erstellten Dienstpläne und der Aktualität angehängter Dokumente obliegt allein dem Anwender.

---

## 📝 Lizenz

Dieses Projekt ist unter der **MIT Lizenz** veröffentlicht. Siehe `LICENSE` Datei für Details.

---

*Entwickelt mit ❤️ und Python.*
