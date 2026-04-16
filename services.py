import os
from models import db, User, Course, Module, QuizQuestion

genai = None
genai_types = None

def _load_gemini():
    """Importiert google-genai lazy – funktioniert auch nach nachträglicher Installation."""
    global genai, genai_types
    if genai is not None:
        return True
    try:
        from google import genai as _genai
        from google.genai import types as _types
        genai = _genai
        genai_types = _types
        return True
    except ImportError:
        return False

LANGUAGE_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1']

# ────────────────────────────────────────────────
# Standardisierter Deutschtest für Pflegeberufe
# Orientiert am GER (Gemeinsamer Europäischer
# Referenzrahmen für Sprachen) – 10 Fragen
# Stufen A1 → C1
# ────────────────────────────────────────────────
LANGUAGE_TEST = [
    # A1 – Grundlegendes Alltagsvokabular
    {
        'question': 'Der Patient liegt im ___.',
        'choices': ['Bett', 'Büro', 'Garten', 'Auto'],
        'answer': 'Bett',
        'level': 'A1'
    },
    {
        'question': 'Wie fragt man höflich nach dem Befinden?',
        'choices': [
            'Wie geht es Ihnen heute?',
            'Wohin gehen Sie?',
            'Was essen Sie gern?',
            'Wann kommen Sie?'
        ],
        'answer': 'Wie geht es Ihnen heute?',
        'level': 'A1'
    },
    # A2 – Einfacher medizinischer Kontext
    {
        'question': 'Der Patient ___ über Schmerzen in der Brust.',
        'choices': ['klagt', 'lacht', 'singt', 'springt'],
        'answer': 'klagt',
        'level': 'A2'
    },
    {
        'question': 'Was ist ein "Fieberthermometer"?',
        'choices': [
            'Ein Gerät zum Messen der Körpertemperatur',
            'Ein Gerät zum Messen des Blutdrucks',
            'Ein Medikament gegen Fieber',
            'Ein Verband für Wunden'
        ],
        'answer': 'Ein Gerät zum Messen der Körpertemperatur',
        'level': 'A2'
    },
    # B1 – Medizinische Fachbegriffe und Grammatik
    {
        'question': 'Welcher Satz ist grammatisch korrekt?',
        'choices': [
            'Ich habe den Patient gewaschen.',
            'Ich habe dem Patienten gewaschen.',
            'Ich habe den Patienten gewaschen.',
            'Ich habe der Patient gewaschen.'
        ],
        'answer': 'Ich habe den Patienten gewaschen.',
        'level': 'B1'
    },
    {
        'question': 'Was bedeutet "Vitalzeichen"?',
        'choices': [
            'Grundlegende Körperfunktionen wie Puls, Blutdruck und Atmung',
            'Anzeichen einer schweren Krankheit',
            'Das Körpergewicht des Patienten',
            'Die Medikamente eines Patienten'
        ],
        'answer': 'Grundlegende Körperfunktionen wie Puls, Blutdruck und Atmung',
        'level': 'B1'
    },
    # B2 – Fachsprachliche Wendungen und Lateinkenntnisse
    {
        'question': '"Subkutan" beschreibt eine Verabreichung …',
        'choices': ['in die Vene', 'in den Muskel', 'unter die Haut', 'auf die Haut'],
        'answer': 'unter die Haut',
        'level': 'B2'
    },
    {
        'question': 'Ergänzen Sie den Pflegebericht korrekt: "Die Patientin wurde ___ Bett mobilisiert."',
        'choices': ['aus dem', 'aus den', 'aus der', 'aus das'],
        'answer': 'aus dem',
        'level': 'B2'
    },
    # C1 – Komplexe Fachterminologie und Textverstehen
    {
        'question': 'Was bedeutet "Dyspnoe"?',
        'choices': ['Schwindel und Gleichgewichtsstörungen', 'Atemnot oder erschwertes Atmen', 'Herzrasen', 'Übelkeit und Erbrechen'],
        'answer': 'Atemnot oder erschwertes Atmen',
        'level': 'C1'
    },
    {
        'question': 'Welche Formulierung ist für einen formellen Pflegebericht korrekt?',
        'choices': [
            'Patient hat schlecht geschlafen, war unruhig die ganze Nacht.',
            'Der Patient schlief schlecht und zeigte nächtliche Unruhe.',
            'Patient schläft schlecht, Nacht war unruhig.',
            'Hat nicht gut geschlafen der Patient, war er unruhig.'
        ],
        'answer': 'Der Patient schlief schlecht und zeigte nächtliche Unruhe.',
        'level': 'C1'
    },
]


# ────────────────────────────────────────────────
# Standardisierter Pflegewissen-Test
# Orientiert am Rahmenlehrplan Pflegeausbildung
# 10 Fragen – Niveau Anfänger → Fortgeschritten
# ────────────────────────────────────────────────
NURSING_TEST = [
    # Grundlagen – Vitalzeichen
    {
        'question': 'Welche Pulsfrequenz gilt beim Erwachsenen in Ruhe als normal?',
        'choices': ['40–59 / min', '60–100 / min', '101–140 / min', '> 140 / min'],
        'answer': '60–100 / min'
    },
    {
        'question': 'Ab welchem Wert spricht man von Fieber?',
        'choices': ['Ab 36,5 °C', 'Ab 37,0 °C', 'Ab 38,0 °C', 'Ab 39,0 °C'],
        'answer': 'Ab 38,0 °C'
    },
    # Hygiene
    {
        'question': 'Was ist die korrekte Durchführung der hygienischen Händedesinfektion?',
        'choices': [
            'Hände waschen, abtrocknen, dann Desinfektionsmittel auftragen',
            'Desinfektionsmittel 30 Sekunden in trockene Hände einreiben',
            'Handschuhe anziehen, danach desinfizieren',
            'Hände 1 Minute unter fließendem Wasser halten'
        ],
        'answer': 'Desinfektionsmittel 30 Sekunden in trockene Hände einreiben'
    },
    # Dehydratation
    {
        'question': 'Welche der folgenden Zeichen deuten auf eine Dehydratation hin? (Mehrfachauswahl)',
        'choices': ['Stehende Hautfalten', 'Trockene Mundschleimhaut', 'Blutdruckanstieg', 'Dunkler Urin'],
        'answer': 'Stehende Hautfalten;Trockene Mundschleimhaut;Dunkler Urin',
        'multi': True
    },
    # Lagerung
    {
        'question': 'In welcher Lagerung sollte ein Patient mit Atemnot bevorzugt gelagert werden?',
        'choices': [
            'Flachlagerung (0°)',
            'Oberkörper hochgelagert (30–45°)',
            'Linksseitenlage',
            'Bauchlage'
        ],
        'answer': 'Oberkörper hochgelagert (30–45°)'
    },
    # Dekubitus
    {
        'question': 'Welche Lagerung wird zur Druckentlastung bei bettlägerigen Patienten empfohlen?',
        'choices': [
            '90°-Seitenlagerung',
            '30°-Schieflagerung (Mikrolagerung)',
            'Bauchlagerung',
            'Keine Lagerung notwendig'
        ],
        'answer': '30°-Schieflagerung (Mikrolagerung)'
    },
    # Schmerzerfassung
    {
        'question': 'Was misst die Numerische Rating-Skala (NRS)?',
        'choices': [
            'Die Herzfrequenz des Patienten',
            'Den Bewusstseinszustand',
            'Die Schmerzintensität auf einer Skala von 0–10',
            'Den Blutzuckerspiegel'
        ],
        'answer': 'Die Schmerzintensität auf einer Skala von 0–10'
    },
    # Notfall / ABCDE
    {
        'question': 'Welche Elemente umfasst das ABCDE-Schema der Ersteinschätzung? (Mehrfachauswahl)',
        'choices': ['Airway (Atemweg)', 'Breathing (Atmung)', 'Circulation (Kreislauf)', 'Disability (Bewusstsein)'],
        'answer': 'Airway (Atemweg);Breathing (Atmung);Circulation (Kreislauf);Disability (Bewusstsein)',
        'multi': True
    },
    # Medikamente
    {
        'question': 'Was beschreibt der Begriff "p.o." bei der Medikamentengabe?',
        'choices': [
            'Intravenöse Gabe',
            'Intramuskuläre Gabe',
            'Orale Gabe (per os)',
            'Subkutane Gabe'
        ],
        'answer': 'Orale Gabe (per os)'
    },
    # Dokumentation
    {
        'question': 'Welche Angaben gehören in eine korrekte Pflegedokumentation? (Mehrfachauswahl)',
        'choices': [
            'Datum und Uhrzeit',
            'Name und Handzeichen der dokumentierenden Person',
            'Beobachtungen und durchgeführte Maßnahmen',
            'Persönliche Meinungen über den Patienten'
        ],
        'answer': 'Datum und Uhrzeit;Name und Handzeichen der dokumentierenden Person;Beobachtungen und durchgeführte Maßnahmen',
        'multi': True
    },
]


def calculate_language_level(score: int) -> str:
    """GER-Einstufung anhand von 10 Fragen."""
    if score <= 2:
        return 'A1'
    if score <= 4:
        return 'A2'
    if score <= 6:
        return 'B1'
    if score <= 8:
        return 'B2'
    return 'C1'


def calculate_nursing_level(score: int) -> str:
    """Pflegewissen-Niveau anhand von 10 Fragen."""
    if score <= 3:
        return 'beginner'
    if score <= 6:
        return 'intermediate'
    return 'advanced'


def get_ai_professor_response(topic: str, student_level: str, course_context: str = '') -> str:
    """Antwortet mit Google Gemini, mit optionalem Kursinhalts-Kontext."""
    if not topic:
        topic = 'Pflegewissen allgemein'

    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key:
        level_tips = {
            'A1': 'Ich werde sehr einfache, kurze Sätze verwenden.',
            'A2': 'Ich erkläre mit bekannten Alltagswörtern.',
            'B1': 'Ich verwende klares Standarddeutsch.',
            'B2': 'Ich erkläre auf normalem Pflegedeutsch.',
            'C1': 'Ich verwende Fachterminologie der Pflege.',
        }
        tip = level_tips.get(student_level, 'Ich passe meine Sprache an dein Niveau an.')
        return (
            f"Professor KI – Demo-Modus (kein API-Key konfiguriert)\n\n"
            f"Thema: {topic} | Dein Niveau: {student_level}\n"
            f"{tip}\n\n"
            f"Um die echte KI-Professorin zu nutzen, setze GOOGLE_API_KEY in der .env-Datei."
        )

    if not _load_gemini():
        return (
            "Professor KI: Das Paket google-genai ist nicht installiert.\n"
            "Bitte führe aus: pip install google-genai"
        )

    try:
        level_desc = {
            'A1': 'sehr einfaches Deutsch, kurze Sätze, Grundvokabular – erkläre jeden Fachbegriff sofort',
            'A2': 'einfaches Deutsch mit bekannten Alltagsausdrücken',
            'B1': 'klares Standarddeutsch, gängige Fachbegriffe mit kurzer Erklärung',
            'B2': 'normales Pflegedeutsch, Fachterminologie darf verwendet werden',
            'C1': 'gehobenes Pflegefachdeutsch mit vollständiger Terminologie',
        }.get(student_level, 'verständliches Deutsch')

        course_section = ''
        if course_context:
            course_section = (
                f"\n\n## Kursinhalte des Schülers\n"
                f"Nutze folgende Kursinhalte als Grundlage deiner Erklärung, "
                f"damit du direkt auf das beziehst, was der Schüler gerade lernt:\n\n"
                f"{course_context}\n"
            )

        system_instruction = (
            f"Du bist Professor KI, ein einfühlsamer und geduldiger Pflegepädagoge. "
            f"Du sprichst auf Sprachniveau {student_level} ({level_desc}). "
            f"Beobachte aktiv den Lernstand: Erkenne Wissenslücken und sprich sie behutsam an. "
            f"Verknüpfe Theorie immer mit konkreten Pflegesituationen aus dem Alltag. "
            f"Halte deine Antwort kompakt (4–6 Sätze). "
            f"Beende mit einer kurzen Reflexionsfrage, die zum Nachdenken anregt."
            f"{course_section}"
        )

        client = genai.Client(api_key=api_key)
        config = genai_types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=600,
            temperature=0.7,
        )
        contents = f"Erkläre mir bitte: {topic}"

        # Versuche Modelle in Reihenfolge (Fallback bei Kontingent-Limit)
        for model in ('gemini-3.1-flash-lite-preview', 'gemini-3-flash-preview', 'gemini-2.5-flash-lite', 'gemini-2.5-flash'):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                return response.text
            except Exception as model_err:
                err_str = str(model_err)
                # Bei Kontingent-Limit oder vorübergehender Überlastung nächstes Modell versuchen
                if any(code in err_str for code in ('429', '503', 'RESOURCE_EXHAUSTED', 'UNAVAILABLE')):
                    continue
                # Anderer Fehler – sofort abbrechen
                raise model_err

        return (
            "Professor KI: Alle Modelle haben aktuell ihr Kontingent erreicht. "
            "Bitte versuche es in einer Minute erneut."
        )
    except Exception as e:
        return (
            f"Professor KI: Leider ist ein Fehler aufgetreten ({type(e).__name__}: {e}). "
            f"Bitte überprüfe den GOOGLE_API_KEY und die Internetverbindung."
        )


def init_db(app):
    with app.app_context():
        db.create_all()

        teacher = User.query.filter_by(email='lehrer@carelearn.de').first()
        if not teacher:
            from werkzeug.security import generate_password_hash
            teacher = User(
                role='teacher',
                email='lehrer@carelearn.de',
                password_hash=generate_password_hash('pflege123'),
                first_name='Simone',
                last_name='Müller',
                country='Deutschland',
                language='Deutsch',
                speciality='Pflegepädagogik'
            )
            db.session.add(teacher)
            db.session.commit()

            course = Course(
                title='Vitalzeichen sicher messen',
                summary='Ein Einsteigerkurs zu Puls, Blutdruck und Atmung für Pflegefachkräfte im ersten Ausbildungsjahr.',
                recommended_level='A2',
                owner_id=teacher.id
            )
            db.session.add(course)
            db.session.commit()

            module = Module(
                course_id=course.id,
                title='Puls und Blutdruck – Grundlagen',
                description='Lerne die wichtigsten Vitalwerte kennen und wie du sie korrekt misst.',
                module_type='quiz',
                content=(
                    'Vitalzeichen sind grundlegende Körperfunktionen, die Auskunft über den '
                    'Gesundheitszustand eines Patienten geben. Dazu gehören Puls, Blutdruck, '
                    'Atemfrequenz und Körpertemperatur. Ein normaler Puls liegt zwischen '
                    '60–100 Schlägen pro Minute. Der Normblutdruck liegt bei ca. 120/80 mmHg.'
                ),
                position=1
            )
            db.session.add(module)
            db.session.commit()

            # Quiz-Fragen für das Demo-Modul anlegen
            quiz_questions = [
                QuizQuestion(
                    module_id=module.id,
                    question='Welcher Pulswert gilt beim Erwachsenen als Bradykardie (zu langsam)?',
                    options='Über 100 / min;Unter 60 / min;60–80 / min;80–100 / min',
                    answer='Unter 60 / min',
                    multi_choice=False
                ),
                QuizQuestion(
                    module_id=module.id,
                    question='Welcher Blutdruckwert wird als hypertensiv (zu hoch) eingestuft?',
                    options='Unter 90/60 mmHg;90–119/60–79 mmHg;120–129/< 80 mmHg;≥ 140/90 mmHg',
                    answer='≥ 140/90 mmHg',
                    multi_choice=False
                ),
                QuizQuestion(
                    module_id=module.id,
                    question='Welche der folgenden gehören zu den klassischen Vitalzeichen? (Mehrfachauswahl)',
                    options='Puls;Blutdruck;Körpertemperatur;Körpergröße',
                    answer='Puls;Blutdruck;Körpertemperatur',
                    multi_choice=True
                ),
                QuizQuestion(
                    module_id=module.id,
                    question='Was bedeutet eine Sauerstoffsättigung (SpO₂) von unter 90 %?',
                    options='Normalwert;Leichte Abweichung;Kritische Hypoxie – sofort handeln;Zu hoch – gefährlich',
                    answer='Kritische Hypoxie – sofort handeln',
                    multi_choice=False
                ),
            ]
            for q in quiz_questions:
                db.session.add(q)
            db.session.commit()

        # Falls der Demokurs vorhanden, aber noch keine Quiz-Fragen → nachrüsten
        else:
            course = Course.query.filter_by(owner_id=teacher.id).first()
            if course:
                module = Module.query.filter_by(course_id=course.id).first()
                if module and not module.quiz_questions:
                    quiz_questions = [
                        QuizQuestion(
                            module_id=module.id,
                            question='Welcher Pulswert gilt beim Erwachsenen als Bradykardie (zu langsam)?',
                            options='Über 100 / min;Unter 60 / min;60–80 / min;80–100 / min',
                            answer='Unter 60 / min',
                            multi_choice=False
                        ),
                        QuizQuestion(
                            module_id=module.id,
                            question='Welcher Blutdruckwert wird als hypertensiv (zu hoch) eingestuft?',
                            options='Unter 90/60 mmHg;90–119/60–79 mmHg;120–129/< 80 mmHg;≥ 140/90 mmHg',
                            answer='≥ 140/90 mmHg',
                            multi_choice=False
                        ),
                        QuizQuestion(
                            module_id=module.id,
                            question='Welche der folgenden gehören zu den klassischen Vitalzeichen? (Mehrfachauswahl)',
                            options='Puls;Blutdruck;Körpertemperatur;Körpergröße',
                            answer='Puls;Blutdruck;Körpertemperatur',
                            multi_choice=True
                        ),
                        QuizQuestion(
                            module_id=module.id,
                            question='Was bedeutet eine Sauerstoffsättigung (SpO₂) von unter 90 %?',
                            options='Normalwert;Leichte Abweichung;Kritische Hypoxie – sofort handeln;Zu hoch – gefährlich',
                            answer='Kritische Hypoxie – sofort handeln',
                            multi_choice=False
                        ),
                    ]
                    for q in quiz_questions:
                        db.session.add(q)
                    db.session.commit()
