import os
import json as _json
from models import db, User, Course, Module

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


_MODELS = ('gemini-3.1-flash-lite-preview', 'gemini-3-flash-preview', 'gemini-2.5-flash-lite', 'gemini-2.5-flash')
_RETRY_CODES = ('429', '503', 'RESOURCE_EXHAUSTED', 'UNAVAILABLE')


def call_gemini_chat(system_instruction: str, contents_list: list) -> str:
    """Multi-Turn-Gemini-Aufruf für den interaktiven KI-Lehrer."""
    if not _load_gemini():
        return "google-genai ist nicht installiert. Bitte führe pip install google-genai aus."

    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key:
        return "Kein GOOGLE_API_KEY konfiguriert. Bitte .env-Datei prüfen."

    try:
        sdk_contents = [
            genai_types.Content(
                role=turn['role'],
                parts=[genai_types.Part(text=turn['text'])]
            )
            for turn in contents_list
        ]

        client = genai.Client(api_key=api_key)
        config = genai_types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=300,
            temperature=0.8,
        )

        for model in _MODELS:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=sdk_contents,
                    config=config,
                )
                return response.text
            except Exception as e:
                if any(c in str(e) for c in _RETRY_CODES):
                    continue
                raise

        return "Alle KI-Modelle sind gerade überlastet. Bitte in einer Minute erneut versuchen."
    except Exception as e:
        return f"Fehler beim KI-Aufruf: {type(e).__name__}: {e}"


def build_ki_lehrer_system_prompt(first_name: str, language_level: str,
                                   module_title: str, course_title: str,
                                   module_content: str) -> str:
    level_desc = {
        'A1': 'sehr einfaches Deutsch, Sätze max. 8 Wörter, nur Grundvokabular – jeden Fachbegriff sofort erklären',
        'A2': 'einfaches Deutsch mit Alltagsausdrücken, kurze klare Sätze',
        'B1': 'klares Standarddeutsch, Pflegefachbegriffe mit kurzer Erklärung',
        'B2': 'normales Pflegedeutsch, Fachterminologie frei verwendbar',
        'C1': 'gehobenes Pflegefachdeutsch mit vollständiger medizinischer Terminologie',
    }.get(language_level, 'verständliches Deutsch')

    module_section = ''
    if module_content:
        module_section = f"""

## Modulinhalt (Pflichtbasis deiner Erklärungen)
Deine Erklärungen MÜSSEN sich auf diesen offiziellen Inhalt beziehen:

---
{module_content[:2000]}
---
"""

    return f"""Du bist Professor Wagner, ein erfahrener Pflegepädagoge mit 20 Jahren Unterrichtserfahrung.
Du unterrichtest {first_name} im Modul „{module_title}" (Kurs: {course_title}).

## Persönlichkeit
- Freundlich, geduldig, ermutigend – du kennst die Herausforderungen der Pflegeausbildung
- Du nennst dich niemals „KI" – du bist immer Professor Wagner
- Du sprichst {first_name} mit Vornamen an
- Sanfte Korrekturen: „Fast! Lass uns das gemeinsam anschauen…" – niemals harsche Kritik

## Sprachniveau: {language_level}
{level_desc}. Passe JEDE Antwort strikt an dieses Niveau an.

## Unterrichtsmethode (strikte Reihenfolge)
1. BEGRÜSSUNG (nur bei __GREETING__): Herzliche Begrüßung + Thema vorstellen + ersten Kernpunkt erklären
2. ERKLÄREN: Einen Teilaspekt in 2–3 Sätzen erklären
3. FRAGEN: Immer mit einer offenen Verständnisfrage enden (keine Ja/Nein-Fragen)
4. REAGIEREN: Antwort bestätigen/korrigieren, dann nächsten Punkt einführen

## Regeln
- Max. 4–5 Sätze pro Antwort (bei Begrüßung max. 6)
- Jede Antwort endet mit einer Frage (außer bei direkten Faktenfragen)
- Off-topic-Fragen sanft zurück zum Thema lenken
- Immer auf Deutsch antworten{module_section}"""


def _strip_md_code(text: str) -> str:
    """Strip markdown code fences from AI response."""
    text = text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:])
        if text.rstrip().endswith('```'):
            text = text.rstrip()[:-3]
    return text.strip()


def generate_ai_quiz(module, language_level: str, num_questions: int = 5) -> list:
    """Generate AI quiz questions for a module, adapted to student level."""
    if not _load_gemini():
        return []
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key:
        return []

    content = (module.content or module.description or '')[:2500]
    level_hint = {
        'A1': 'sehr einfaches Deutsch, kurze Sätze',
        'A2': 'einfaches Deutsch, Alltagsvokabular',
        'B1': 'klares Standarddeutsch',
        'B2': 'normales Pflegedeutsch',
        'C1': 'gehobenes Pflegefachdeutsch',
    }.get(language_level, 'klares Deutsch')

    num_ft = max(1, num_questions - 2)
    num_mc = num_questions - num_ft

    prompt = (
        f'Erstelle genau {num_questions} Quizfragen auf Deutsch über "{module.title}".\n'
        f'Grundlage:\n{content}\n\n'
        f'Sprachniveau: {language_level} ({level_hint})\n'
        f'Genau {num_ft} Freitext-Fragen und {num_mc} Multiple-Choice-Fragen.\n\n'
        f'Antworte NUR mit validem JSON (kein Markdown, keine Erklärung):\n'
        f'{{"questions":['
        f'{{"type":"free_text","question":"...","model_answer":"..."}},'
        f'{{"type":"multiple_choice","question":"...","options":["A","B","C","D"],"answer":"A"}}'
        f']}}'
    )

    client = genai.Client(api_key=api_key)
    cfg = genai_types.GenerateContentConfig(max_output_tokens=900, temperature=0.4)

    for model in _MODELS:
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
            data = _json.loads(_strip_md_code(resp.text))
            questions = data.get('questions', [])
            valid = [q for q in questions if 'question' in q and 'type' in q]
            if valid:
                for i, q in enumerate(valid):
                    q['id'] = i
                return valid[:num_questions]
        except Exception as e:
            if any(c in str(e) for c in _RETRY_CODES):
                continue
            break
    return []


def evaluate_ai_answers(questions: list, student_answers: dict, language_level: str) -> list:
    """Evaluate student answers. MC: exact match. Free text: AI batch evaluation."""
    results = [None] * len(questions)
    free_pairs = []  # (original_idx, q_text, model_answer, student_answer)

    for i, q in enumerate(questions):
        sa = student_answers.get(str(i), '').strip()
        if q.get('type') == 'multiple_choice':
            correct = q.get('answer', '')
            ok = sa.strip() == correct.strip()
            results[i] = {
                'question': q['question'],
                'student_answer': sa,
                'correct_answer': correct,
                'is_correct': ok,
                'feedback': 'Richtig!' if ok else f'Richtige Antwort: {correct}',
                'score': 1 if ok else 0,
            }
        else:
            model_ans = q.get('model_answer', q.get('answer', ''))
            free_pairs.append((i, q['question'], model_ans, sa))

    # AI batch evaluation for all free-text questions in one call
    if free_pairs and _load_gemini():
        api_key = os.environ.get('GOOGLE_API_KEY', '')
        if api_key:
            pairs_text = '\n'.join(
                f'{j+1}. Frage: {qt}\n   Musterantwort: {ma}\n   Schülerantwort: "{sa}"'
                for j, (_, qt, ma, sa) in enumerate(free_pairs)
            )
            prompt = (
                f'Bewerte {len(free_pairs)} Pflegeschüler-Antworten (Sprachniveau {language_level}).\n'
                f'Sei großzügig: Inhaltlich korrekte Antworten → score 1, auch bei Rechtschreibfehlern.\n\n'
                f'{pairs_text}\n\n'
                f'Antworte NUR mit validem JSON:\n'
                f'{{"results":[{{"score":1,"feedback":"Sehr gut! ..."}}]}}\n'
                f'Genau {len(free_pairs)} Einträge im Array.'
            )
            client = genai.Client(api_key=api_key)
            cfg = genai_types.GenerateContentConfig(max_output_tokens=600, temperature=0.2)
            for model in _MODELS:
                try:
                    resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
                    er_list = _json.loads(_strip_md_code(resp.text)).get('results', [])
                    for k, (orig_i, qt, ma, sa) in enumerate(free_pairs):
                        er = er_list[k] if k < len(er_list) else {}
                        results[orig_i] = {
                            'question': qt,
                            'student_answer': sa,
                            'correct_answer': ma,
                            'is_correct': er.get('score', 0) == 1,
                            'feedback': er.get('feedback', ''),
                            'score': er.get('score', 0),
                        }
                    break
                except Exception as e:
                    if any(c in str(e) for c in _RETRY_CODES):
                        continue
                    break

    # Fallback for any results that are still None (AI failed)
    for i, r in enumerate(results):
        if r is None:
            q = questions[i]
            ma = q.get('model_answer', q.get('answer', ''))
            sa = student_answers.get(str(i), '')
            results[i] = {
                'question': q['question'],
                'student_answer': sa,
                'correct_answer': ma,
                'is_correct': False,
                'feedback': f'Musterantwort: {ma}',
                'score': 0,
            }
    return results


def generate_language_test_questions() -> list:
    """AI-generated German language test for nursing context. Falls back to static on error."""
    if not _load_gemini():
        return []
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key:
        return []

    prompt = (
        'Erstelle 10 Deutsch-Testfragen für Pflegepersonal (GER A1–C1, je 2 Fragen pro Niveau).\n'
        'Mix: 6 Freitext-Fragen + 4 Multiple-Choice. Pflegerischer Kontext.\n'
        'Antworte NUR mit validem JSON:\n'
        '{"questions":['
        '{"type":"free_text","level":"A1","question":"...","model_answer":"..."},'
        '{"type":"multiple_choice","level":"B1","question":"...","options":["A","B","C","D"],"answer":"A"}'
        ']}'
    )
    client = genai.Client(api_key=api_key)
    cfg = genai_types.GenerateContentConfig(max_output_tokens=1400, temperature=0.5)
    for model in _MODELS:
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
            questions = _json.loads(_strip_md_code(resp.text)).get('questions', [])
            if len(questions) >= 8:
                return questions[:10]
        except Exception as e:
            if any(c in str(e) for c in _RETRY_CODES):
                continue
            break
    return []


def generate_nursing_test_questions() -> list:
    """AI-generated nursing knowledge test. Falls back to static on error."""
    if not _load_gemini():
        return []
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key:
        return []

    prompt = (
        'Erstelle 10 Pflegewissen-Testfragen für Pflegeschüler (Grundausbildung).\n'
        'Themen: Vitalzeichen, Hygiene, Lagerung, Dekubitus, Medikamente, Dokumentation, Notfall.\n'
        'Mix: 6 Freitext-Fragen + 4 Multiple-Choice.\n'
        'Antworte NUR mit validem JSON:\n'
        '{"questions":['
        '{"type":"free_text","question":"...","model_answer":"..."},'
        '{"type":"multiple_choice","question":"...","options":["A","B","C","D"],"answer":"A"}'
        ']}'
    )
    client = genai.Client(api_key=api_key)
    cfg = genai_types.GenerateContentConfig(max_output_tokens=1400, temperature=0.5)
    for model in _MODELS:
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
            questions = _json.loads(_strip_md_code(resp.text)).get('questions', [])
            if len(questions) >= 8:
                return questions[:10]
        except Exception as e:
            if any(c in str(e) for c in _RETRY_CODES):
                continue
            break
    return []


def _seed_demo_courses(teacher_id: int):
    """Seed 3 demo nursing courses with rich module content."""
    courses_data = [
        {
            'title': 'Vitalzeichen und Monitoring',
            'summary': 'Grundlagen der Vitalzeichenmessung: Puls, Blutdruck, Atmung, Temperatur und Sauerstoffsättigung sicher erfassen und dokumentieren.',
            'level': 'A2',
            'modules': [
                {
                    'title': 'Puls und Herzfrequenz messen',
                    'description': 'Pulsfrequenz, -rhythmus und -qualität korrekt erfassen.',
                    'content': (
                        'Der Puls ist die fühlbare Druckwelle des Herzschlags in den Arterien. '
                        'Beim Erwachsenen liegt der normale Ruhepuls zwischen 60 und 100 Schlägen pro Minute. '
                        'Ein Puls unter 60/min heißt Bradykardie, über 100/min Tachykardie.\n\n'
                        'Messstellen\n'
                        'Gemessen wird der Puls meist an der A. radialis (Handgelenk), A. carotis (Hals) '
                        'oder A. femoralis. Bei der Pulsmessung werden Frequenz, Rhythmus, Qualität '
                        '(kräftig/schwach) und Gleichmäßigkeit beurteilt.\n\n'
                        'Durchführung\n'
                        'Die Messdauer beträgt mindestens 30 Sekunden (×2) oder bei Unregelmäßigkeiten '
                        'eine volle Minute. Einflussfaktoren: körperliche Aktivität, Fieber, Schmerzen, '
                        'Medikamente, emotionaler Stress.\n\n'
                        'Dokumentation\n'
                        'Uhrzeit, Messwert, Messpunkt und Besonderheiten (z.B. Unregelmäßigkeiten) '
                        'werden im Pflegebericht festgehalten.'
                    ),
                },
                {
                    'title': 'Blutdruckmessung nach Riva-Rocci',
                    'description': 'Blutdruck korrekt messen, interpretieren und dokumentieren.',
                    'content': (
                        'Der Blutdruck beschreibt den Druck des Blutes in den Arterien (Angabe in mmHg). '
                        'Der systolische Wert (oben) entsteht bei Herzkontraktion, '
                        'der diastolische (unten) bei Herzerschlaffung. '
                        'Normwert: 120/80 mmHg. Hypertonie: ≥ 140/90 mmHg. Hypotonie: < 90/60 mmHg.\n\n'
                        'Messtechnik\n'
                        'Patient sitzt entspannt, Manschette am Oberarm auf Herzhöhe. '
                        'Manschette ca. 30 mmHg über dem erwarteten Wert aufpumpen, dann langsam ablassen. '
                        'Korotkoff-Geräusche: Beginn = systolisch, Verschwinden = diastolisch.\n\n'
                        'Häufige Fehler\n'
                        'Falsche Manschettengröße, falsche Armposition, Weißkittel-Effekt, volle Blase. '
                        'Manschette darf nicht zu locker sitzen (falscher Wert).\n\n'
                        'Dokumentation\n'
                        'Messwert, Arm (links/rechts), Körperposition, Uhrzeit und Besonderheiten.'
                    ),
                },
                {
                    'title': 'Atemfrequenz und Sauerstoffsättigung',
                    'description': 'Atmung beurteilen und SpO₂ korrekt messen.',
                    'content': (
                        'Die Atemfrequenz (AF) ist die Anzahl der Atemzüge pro Minute. '
                        'Normwert Erwachsene: 12–20/min. Tachypnoe: > 20/min. Bradypnoe: < 12/min.\n\n'
                        'Messung\n'
                        'Die AF sollte möglichst unbemerkt gemessen werden (z.B. nach Pulsmessung, '
                        'Finger noch am Handgelenk). Beurteilung: Frequenz, Tiefe, Rhythmus, Geräusche.\n\n'
                        'Sauerstoffsättigung (SpO₂)\n'
                        'Normwert: 95–100 %. Unter 90 % → kritische Hypoxie, sofort handeln! '
                        'Messung mit Pulsoximeter an Finger oder Ohrläppchen. '
                        'Störfaktoren: Nagellack, Kälte, Bewegung, periphere Durchblutungsstörungen.\n\n'
                        'Wichtig\n'
                        'SpO₂ immer zusammen mit dem klinischen Gesamtbild bewerten.'
                    ),
                },
                {
                    'title': 'Körpertemperatur messen',
                    'description': 'Temperaturmessung, Normalwerte und Fieberphasen kennen.',
                    'content': (
                        'Die Körpertemperatur zeigt Entzündungsprozesse und Stoffwechselzustand an.\n\n'
                        'Normwerte je nach Messstelle\n'
                        'Rektal (goldener Standard): 36,8–37,8 °C. Oral: 0,3–0,5 °C niedriger. '
                        'Axillär (Achsel): 0,5–1,0 °C niedriger. Tympanal (Ohr): entspricht rektal.\n\n'
                        'Bewertung\n'
                        'Fieber: ≥ 38,0 °C. Subfebrile Temperatur: 37,5–37,9 °C. '
                        'Hypothermie: < 36,0 °C.\n\n'
                        'Fieberphasen\n'
                        '1. Anstieg: Kältegefühl, Schüttelfrost. '
                        '2. Höhepunkt: Hitze, Hautrötung. '
                        '3. Abfall: Schwitzen.\n\n'
                        'Pflegemaßnahmen bei Fieber\n'
                        'Fieberkurve führen, ausreichend Flüssigkeit anbieten, kühle Umgebung, '
                        'Wadenwickel auf Wunsch, ärztlich verordnete Antipyretika verabreichen.'
                    ),
                },
            ],
        },
        {
            'title': 'Hygiene und Infektionsschutz',
            'summary': 'Grundlagen der Krankenhaushygiene: Händedesinfektion, Schutzausrüstung und Isolationsmaßnahmen zur Prävention nosokomialer Infektionen.',
            'level': 'B1',
            'modules': [
                {
                    'title': 'Hygienische Händedesinfektion – 5 Momente',
                    'description': 'Die 5 WHO-Momente der Händehygiene sicher anwenden.',
                    'content': (
                        'Die Händedesinfektion ist die wirksamste Einzelmaßnahme zur Prävention '
                        'nosokomialer Infektionen.\n\n'
                        'Die 5 WHO-Momente der Händehygiene\n'
                        '1. VOR Patientenkontakt\n'
                        '2. VOR aseptischer Tätigkeit (z.B. Verbandwechsel, Injektion)\n'
                        '3. NACH Kontakt mit potenziell infektiösem Material\n'
                        '4. NACH Patientenkontakt\n'
                        '5. NACH Kontakt mit der Patientenumgebung\n\n'
                        'Durchführung\n'
                        '3–5 ml alkoholisches Händedesinfektionsmittel in TROCKENE Hände geben, '
                        'mindestens 30 Sekunden einreiben. Alle Flächen bearbeiten: '
                        'Handflächen, Handrücken, Fingerzwischenräume, Fingerkuppen, Daumen.\n\n'
                        'Wichtig\n'
                        'Feuchte Hände reduzieren die Wirksamkeit! Handschuhe ersetzen NICHT die '
                        'Händedesinfektion – auch vor und nach dem Tragen desinfizieren.'
                    ),
                },
                {
                    'title': 'Persönliche Schutzausrüstung (PSA)',
                    'description': 'PSA korrekt anlegen, tragen und ausziehen.',
                    'content': (
                        'PSA schützt Pflegepersonal und Patienten vor Infektionsübertragung.\n\n'
                        'Einmalhandschuhe\n'
                        'Bei Kontakt mit Körperflüssigkeiten, Schleimhäuten oder nicht-intakter Haut. '
                        'Anlegen nach Händedesinfektion. Ausziehen: Außenseite nicht berühren, sofort entsorgen.\n\n'
                        'Masken\n'
                        'Mund-Nasen-Schutz (MNS): Schutz vor Tröpfchenübertragung, bedeckt Mund und Nase eng. '
                        'FFP2/FFP3: bei aerogener Übertragung (z.B. Tuberkulose, COVID-19).\n\n'
                        'Schutzkittel und Schutzbrille\n'
                        'Kittel bei Kontaktprecautions und Spritzgefahr. '
                        'Brille als Spritzschutz für Augen.\n\n'
                        'Reihenfolge Anlegen (GOWN)\n'
                        '1. Kittel → 2. Maske → 3. Brille → 4. Handschuhe\n\n'
                        'Reihenfolge Ausziehen\n'
                        '1. Handschuhe (kontaminierteste Fläche) → 2. Brille → 3. Kittel → 4. Maske. '
                        'Nach jedem Schritt Händedesinfektion!'
                    ),
                },
                {
                    'title': 'Isolationsmaßnahmen',
                    'description': 'Kontakt-, Tröpfchen- und Aerogenisolation korrekt anwenden.',
                    'content': (
                        'Isolationsmaßnahmen verhindern die Ausbreitung von Infektionserregern.\n\n'
                        'Kontaktisolation (z.B. MRSA, VRE, Durchfall)\n'
                        'Einzel- oder Kohortenzimmer. PSA (Handschuhe + Kittel) vor Betreten anlegen. '
                        'Patientenbezogenes Material verwenden. Desinfektion vor dem Verlassen.\n\n'
                        'Tröpfchenisolation (z.B. Influenza, Meningitis, Keuchhusten)\n'
                        'MNS für Personal im Abstand < 1 m. Patient trägt MNS beim Transport.\n\n'
                        'Aerogenisolation (z.B. Tuberkulose, Masern, Windpocken)\n'
                        'Unterdruckzimmer erforderlich. FFP2/3 für Personal. '
                        'Patient verlässt Zimmer nur mit MNS.\n\n'
                        'Standard-Precautions (gelten für ALLE Patienten)\n'
                        'Händehygiene, PSA bei Kontaminationsrisiko, sichere Entsorgung von Sharps '
                        '(Spritzen NIEMALS recappen!). Isolationsmaßnahmen im Pflegebericht dokumentieren.'
                    ),
                },
            ],
        },
        {
            'title': 'Wundversorgung und Dekubitus',
            'summary': 'Wunden fachgerecht beurteilen, versorgen und Dekubitus systematisch verhüten. Grundlagen des TIME-Konzepts und der Druckgeschwürprävention.',
            'level': 'B2',
            'modules': [
                {
                    'title': 'Wundbeurteilung nach TIME',
                    'description': 'Das TIME-Konzept zur systematischen Wundbeurteilung anwenden.',
                    'content': (
                        'Das TIME-Konzept ist ein standardisiertes Framework zur Wundbeurteilung.\n\n'
                        'T – Tissue (Wundgrund)\n'
                        'Beurteilung des Gewebezustands: nekrotisch (schwarz), belegt (gelb), '
                        'granulierend (rot) oder epithelisierend (rosa). '
                        'Débridement bei Nekrose und Belag notwendig.\n\n'
                        'I – Infection/Inflammation (Infektion/Entzündung)\n'
                        'Lokalzeichen: Rötung, Überwärmung, Schwellung, Schmerz, purulentes Exsudat, Geruch. '
                        'Systemzeichen: Fieber, erhöhte Entzündungswerte. '
                        'Wundabstrich bei Infektionsverdacht.\n\n'
                        'M – Moisture (Feuchtigkeit)\n'
                        'Optimales Wundmilieu = feucht, nicht nass. '
                        'Übermäßiges Exsudat → Mazeration des Wundrandes. '
                        'Zu trockene Wunde → Heilungsverzögerung.\n\n'
                        'E – Edge (Wundrand)\n'
                        'Intakte, fortschreitende Epithelisierung = Heilungszeichen. '
                        'Unterminierter oder mazerierter Wundrand → Behandlung erforderlich. '
                        'Wundgröße dokumentieren: Länge × Breite × Tiefe in cm, Fotodokumentation.'
                    ),
                },
                {
                    'title': 'Verbandtechniken und Wundauflagen',
                    'description': 'Aseptischen Verbandwechsel durchführen und Wundauflagen indikationsgerecht auswählen.',
                    'content': (
                        'Der Verbandwechsel muss aseptisch erfolgen, um Infektionen zu vermeiden.\n\n'
                        'Vorbereitung\n'
                        'Händedesinfektion, sterile Materialien bereitlegen, ausreichend Licht, '
                        'Patientenposition optimieren.\n\n'
                        'Durchführung\n'
                        'Alten Verband mit unsterilen Handschuhen entfernen (Wunde nicht berühren). '
                        'Wundbeurteilung. Handschuhe wechseln, Händedesinfektion. '
                        'Wundreinigung mit steriler NaCl 0,9 %: von innen nach außen wischen.\n\n'
                        'Wundauflagen nach Indikation\n'
                        'Hydrokolloide: leicht bis mittel exsudierend, schützend. '
                        'Alginate: stark exsudierend, blutstillend. '
                        'Schaumstoffverbände: mittleres bis starkes Exsudat. '
                        'Silberverbände: infizierte Wunden. '
                        'Hydrogele: trockene, nekrotische Wunden.\n\n'
                        'Dokumentation\n'
                        'Wundzustand, verwendetes Material, Datum des nächsten Verbandwechsels.'
                    ),
                },
                {
                    'title': 'Dekubitus: Klassifikation und Prävention',
                    'description': 'Dekubitus klassifizieren, Risikofaktoren erkennen und Prophylaxe umsetzen.',
                    'content': (
                        'Dekubitus ist eine lokale Schädigung der Haut durch Druck oder Scherkräfte.\n\n'
                        'Klassifikation (NPUAP/EPUAP)\n'
                        'Grad 1: Nicht wegdrückbare Rötung bei intakter Haut.\n'
                        'Grad 2: Teilverlust der Haut (flaches offenes Ulkus).\n'
                        'Grad 3: Vollständiger Hautverlust, subkutanes Fettgewebe sichtbar.\n'
                        'Grad 4: Vollständiger Hautverlust mit Exposition von Knochen, Sehnen oder Muskeln.\n\n'
                        'Risikofaktoren\n'
                        'Immobilität, Mangelernährung, Inkontinenz, Sensibilitätsstörungen, '
                        'Durchblutungsstörungen. Risikoerfassung mit Braden-Skala (≤ 18 Punkte = Risiko).\n\n'
                        'Prophylaxe\n'
                        'Regelmäßige Umlagerung im 2-Stunden-Rhythmus (30°-Schieflagerung). '
                        'Druckentlastende Matratzen (Wechseldruck, Schaumstoff). '
                        'Hautpflege: kein Reiben, feuchtigkeitserhaltend. '
                        'Ernährungsoptimierung, Inkontinenzversorgung. '
                        'Mikrolagerungen alle 15–30 min zwischen größeren Umlagerungen.'
                    ),
                },
            ],
        },
    ]

    for cd in courses_data:
        course = Course(
            title=cd['title'],
            summary=cd['summary'],
            recommended_level=cd['level'],
            owner_id=teacher_id
        )
        db.session.add(course)
        db.session.flush()
        for pos, md in enumerate(cd['modules'], start=1):
            module = Module(
                course_id=course.id,
                title=md['title'],
                description=md['description'],
                module_type='quiz',
                content=md['content'],
                position=pos
            )
            db.session.add(module)
    db.session.commit()


def init_db(app):
    with app.app_context():
        db.create_all()

        from werkzeug.security import generate_password_hash
        teacher = User.query.filter_by(email='lehrer@carelearn.de').first()
        if not teacher:
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

        # Seed demo courses if the canonical first course doesn't exist yet
        DEMO_TITLES = {'Vitalzeichen und Monitoring', 'Hygiene und Infektionsschutz', 'Wundversorgung und Dekubitus'}
        existing_titles = {c.title for c in Course.query.filter_by(owner_id=teacher.id).all()}

        # Remove duplicates (can happen when debug reloader fires init_db twice)
        seen = set()
        for c in Course.query.filter_by(owner_id=teacher.id).all():
            if c.title in seen:
                db.session.delete(c)
            else:
                seen.add(c.title)
        db.session.commit()

        # Add any missing demo courses
        if not DEMO_TITLES.issubset(existing_titles):
            # Remove only demo stubs, keep teacher-created courses
            for c in Course.query.filter_by(owner_id=teacher.id).all():
                if c.title in DEMO_TITLES:
                    db.session.delete(c)
            db.session.commit()
            _seed_demo_courses(teacher.id)
