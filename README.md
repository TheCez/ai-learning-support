# careLearn

Ein Python-Web-App-Prototyp für deutsche Pflegeschulen mit Rollen für Lehrende und Lernende.

## Architektur
- Flask als Web-Framework
- SQLAlchemy + SQLite als Datenbank
- Rollen: `student` und `teacher`
- Funktionen:
  - Registrierung / Login
  - Spracheingangs-Test & Pflegewissen-Test
  - Lehrende laden Kurse und Module hoch
  - Studierende melden sich an und sehen Lernpfade, Quizze und KI-Lehrer
  - Fortschrittsanzeige für Lehrende

## Setup
1. `python -m venv venv`
2. `venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `python app.py`

Die App läuft dann unter `http://127.0.0.1:5000`.
