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

<img width="1076" height="567" alt="Schichtplanung" src="https://github.com/user-attachments/assets/5bb742a2-3e71-4804-9df6-a1392954df3d" />
<img width="1076" height="567" alt="Grafische Übersicht" src="https://github.com/user-attachments/assets/46886cb0-28d5-4939-bfae-4fdc07e2ccba" />
<img width="1076" height="567" alt="Auswertungen" src="https://github.com/user-attachments/assets/b0f694db-2888-4e79-b987-1ebb1f0e0a76" />




---

## ⚖️ Haftungsausschluss (Disclaimer)

Die Software "EquiShift" wird "wie besehen" (as is) zur Verfügung gestellt, ohne jegliche Gewährleistung, weder ausdrücklich noch stillschweigend. Die Nutzung erfolgt auf eigenes Risiko. Der Entwickler haftet nicht für Schäden, Datenverluste, fehlerhafte Planungen oder daraus resultierende Folgen (z. B. Einnahmeausfälle oder Verstöße gegen Sicherheitsauflagen). Die Prüfung der erstellten Dienstpläne und der Aktualität angehängter Dokumente obliegt allein dem Anwender.

---

## 📝 Lizenz

Dieses Projekt ist unter der **MIT Lizenz** veröffentlicht. Siehe `LICENSE` Datei für Details.

---

*Entwickelt mit ❤️ und Python.*
