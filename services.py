import os
import requests
from models import db, User, Course, Module

def _llm_base() -> str:
    return os.environ.get('LLM_API_BASE_URL', 'http://localhost:8001').rstrip('/')


def _safe_post(path: str, payload: dict, timeout: int = 30) -> dict:
    try:
        resp = requests.post(f"{_llm_base()}{path}", json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

LANGUAGE_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1']

# ────────────────────────────────────────────────
# Standardisierter Deutschtest für Pflegeberufe
# Orientiert am GER (Gemeinsamer Europäischer
# Referenzrahmen für Sprachen) – 10 Fragen
# Stufen A1 → C1
# ────────────────────────────────────────────────
LANGUAGE_TEST = [
    # A1 – Grundlegendes Alltagsdeutsch
    {
        'question': 'Was bedeutet "Guten Morgen"?',
        'choices': ['Auf Wiedersehen', 'Gute Nacht', 'Hallo am Morgen', 'Danke schön'],
        'answer': 'Hallo am Morgen',
        'level': 'A1'
    },
    {
        'question': 'Welches Wort ist ein Artikel für männliche Nomen (Maskulinum)?',
        'choices': ['die', 'das', 'der', 'ein'],
        'answer': 'der',
        'level': 'A1'
    },
    # A2 – Einfache Grammatik und Wortschatz
    {
        'question': 'Ergänze: "Ich ___ heute müde."',
        'choices': ['bin', 'hat', 'sind', 'haben'],
        'answer': 'bin',
        'level': 'A2'
    },
    {
        'question': 'Welcher Satz ist richtig?',
        'choices': [
            'Er geht nach Hause gestern.',
            'Er ging gestern nach Hause.',
            'Er geht gestern nach Hause.',
            'Gestern er geht nach Hause.'
        ],
        'answer': 'Er ging gestern nach Hause.',
        'level': 'A2'
    },
    # B1 – Grammatik: Kasus und Zeitformen
    {
        'question': 'Welcher Satz verwendet den Akkusativ korrekt?',
        'choices': [
            'Ich helfe dem Mann.',
            'Ich sehe den Mann.',
            'Ich gebe der Mann das Buch.',
            'Ich spreche mit dem Mann.'
        ],
        'answer': 'Ich sehe den Mann.',
        'level': 'B1'
    },
    {
        'question': 'Was ist das Gegenteil von "laut"?',
        'choices': ['langsam', 'leise', 'hell', 'groß'],
        'answer': 'leise',
        'level': 'B1'
    },
    # B2 – Komplexe Grammatik und Stil
    {
        'question': 'Welche Konjunktion leitet einen Kausalsatz ein?',
        'choices': ['obwohl', 'damit', 'weil', 'falls'],
        'answer': 'weil',
        'level': 'B2'
    },
    {
        'question': 'Welche Formulierung ist förmlich und korrekt?',
        'choices': [
            'Ich will das Formular haben.',
            'Könnten Sie mir bitte das Formular geben?',
            'Gib mir das Formular.',
            'Das Formular, ich brauche es.'
        ],
        'answer': 'Könnten Sie mir bitte das Formular geben?',
        'level': 'B2'
    },
    # C1 – Schriftlicher Ausdruck und Textverstehen
    {
        'question': 'Was bedeutet die Redewendung "auf dem Laufenden bleiben"?',
        'choices': [
            'Schnell laufen',
            'Immer informiert sein',
            'Eine Liste führen',
            'Pünktlich sein'
        ],
        'answer': 'Immer informiert sein',
        'level': 'C1'
    },
    {
        'question': 'Welcher Satz ist stilistisch am angemessensten für einen formellen Brief?',
        'choices': [
            'Ich finde Ihren Vorschlag mega gut.',
            'Ihr Vorschlag ist echt interessant.',
            'Ich erachte Ihren Vorschlag als äußerst konstruktiv.',
            'Der Vorschlag von Ihnen ist nicht schlecht.'
        ],
        'answer': 'Ich erachte Ihren Vorschlag als äußerst konstruktiv.',
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


def get_ai_professor_response(topic: str, student_level: str, course_context: str = '', student_context: str = '', course_id: str | None = None) -> str:
    """Antwort über interne llm_api /generate_answer (kein direkter Gemini-Aufruf)."""
    query = (topic or 'Pflegewissen allgemein').strip()
    if course_context:
        query += f"\n\nKurskontext:\n{course_context}"
    if student_context:
        query += f"\n\nSchülerkontext:\n{student_context}"
    payload = {
        'course_id': str(course_id or 'all'),
        'query': query,
        'persona': 'ki_professor',
    }
    result = _safe_post('/generate_answer', payload)
    answer = str(result.get('answer', '') or '').strip()
    return answer or 'Keine Antwort erhalten.'


def call_ki_lehrer_chat(course_id: str, conversation: list, is_greeting: bool = False, user_first_name: str = '') -> dict:
    """Calls llm_api /generate_presentation for KI-Lehrer."""
    query = ''
    for msg in reversed(conversation or []):
        if msg.get('role') == 'user':
            query = str(msg.get('text', '') or '').strip()
            break
    if is_greeting and not query:
        query = f'Hallo {user_first_name}, starte den Unterricht mit einer kurzen Begrüßung und dem ersten Kernpunkt.'
    if not query:
        query = 'Erkläre mir dieses Modul.'

    payload = {
        'course_id': str(course_id or 'all'),
        'query': query,
        'persona': 'ki_professor',
    }
    data = _safe_post('/generate_presentation', payload)
    return data if isinstance(data, dict) else {'slides': []}


def call_fall_blutdruck_turn(course_id: str, student_context: str, prompt: str) -> dict:
    """Calls llm_api /generate_answer for case-study turn responses."""
    payload = {
        'course_id': str(course_id or 'all'),
        'query': prompt,
        'student_context': student_context or '',
        'persona': 'ki_professor',
    }
    return _safe_post('/generate_answer', payload)


def call_gemini_chat(system_instruction: str, contents_list: list) -> str:
    """Compatibility wrapper: routes through llm_api /generate_answer."""
    last_user = ''
    for turn in reversed(contents_list or []):
        if str(turn.get('role', '')).lower() == 'user':
            last_user = str(turn.get('text', '') or '').strip()
            break
    if not last_user:
        last_user = 'Bitte erkläre den nächsten Schritt.'
    payload = {
        'course_id': 'all',
        'query': f"{system_instruction}\n\n{last_user}",
        'persona': 'ki_professor',
    }
    result = _safe_post('/generate_answer', payload)
    return str(result.get('answer', '') or 'Keine Antwort erhalten.').strip()


def build_ki_lehrer_system_prompt(first_name: str, language_level: str,
                                   module_title: str, course_title: str,
                                   module_content: str,
                                   today_module_title: str = '',
                                   today_course_title: str = '',
                                   student_context: str = '') -> str:
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

    today_section = ''
    if today_module_title:
        t_course = today_course_title or course_title
        today_section = (
            f'\n\n## Heutiges Thema (vom Lehrer festgelegt)\n'
            f'Heute behandeln wir: "{today_module_title}" (Kurs: {t_course}). '
            'Erwähne dies bei Bedarf und kehre immer wieder zu diesem Thema zurueck. '
            'Schueler duerfen aber auch nach frueheren Inhalten fragen.'
        )

    greeting_rule = (
        'BEGRUESSING (nur bei __GREETING__): Sage NUR: '
        f'"Hallo {first_name}! Hier ist Prof. Wagner." '
        '- danach sofort den ersten Kernpunkt des Moduls erlaeutern. '
        'Keine langen Einleitungen.'
    )

    prompt_text = f"""Du bist Professor Wagner, ein erfahrener Pflegepädagoge mit 20 Jahren Unterrichtserfahrung.
Du unterrichtest {first_name} im Modul „{module_title}" (Kurs: {course_title}).

## Persönlichkeit
- Freundlich, geduldig, ermutigend – du kennst die Herausforderungen der Pflegeausbildung
- Du nennst dich niemals „KI" – du bist immer Professor Wagner
- Du sprichst {first_name} mit Vornamen an
- Sanfte Korrekturen: „Fast! Lass uns das gemeinsam anschauen…" – niemals harsche Kritik

## Sprachniveau: {language_level}
{level_desc}. Passe JEDE Antwort strikt an dieses Niveau an.

## Unterrichtsmethode (strikte Reihenfolge)
1. {greeting_rule}
2. ERKLÄREN: Einen Teilaspekt in 2–3 Sätzen erklären
3. FRAGEN: Immer mit einer offenen Verständnisfrage enden (keine Ja/Nein-Fragen)
4. REAGIEREN: Antwort bestätigen/korrigieren, dann nächsten Punkt einführen

## Regeln
- Max. 4–5 Sätze pro Antwort (bei Begrüßung: exakt 1 Satz + erster Kernpunkt)
- Jede Antwort endet mit einer Frage (außer bei direkten Faktenfragen)
- Off-topic-Fragen sanft zurück zum Thema lenken
- Immer auf Deutsch antworten{module_section}{today_section}"""

    if student_context:
        prompt_text += f"\n\n## Schülerprofil\n{student_context}\nPasse Erklärungen an diesen Hintergrund an."
    return prompt_text


# ════════════════════════════════════════════════════════════
#  FALLSTUDIE – Killer-Demo: Blutdruckmessung bei Frau Schmidt
# ════════════════════════════════════════════════════════════

FALL_BLUTDRUCK = {
    'slug': 'blutdruck-frau-schmidt',
    'title': 'Blutdruckmessung bei Frau Schmidt',
    'level': 'B1',
    'duration_min': 5,
    'patient': {
        'name': 'Frau Schmidt',
        'age': 78,
        'room': 'Zimmer 214',
        'complaint': 'Schwindel beim Aufstehen',
        'history': 'Bekannte Hypertonie, nimmt Ramipril 5 mg morgens',
        'order': 'Bitte Blutdruck korrekt am rechten Oberarm messen und dokumentieren.',
    },
    'steps': [
        {'key': 'identitaet', 'label': 'Patientin identifizieren',
         'hint': 'Name + Geburtsdatum gegen Armband prüfen',
         'kw': ['identit', 'armband', 'geburt', 'name prüf', 'wer sind', 'überprüf', 'kontrollier', 'wie heißen']},
        {'key': 'aufklaerung', 'label': 'Maßnahme erklären (Aufklärung)',
         'hint': 'Erklären, was passiert, und Einverständnis einholen',
         'kw': ['erklär', 'aufklär', 'einverständnis', 'einverstanden', 'was ich mache', 'darf ich']},
        {'key': 'ruhe', 'label': '5 Minuten Ruhepause',
         'hint': 'Patientin in Ruhe sitzen oder liegen lassen',
         'kw': ['ruhe', '5 minuten', 'fünf minuten', 'entspann', 'warten', 'rast']},
        {'key': 'manschette', 'label': 'Korrekte Manschettengröße wählen',
         'hint': 'Oberarmumfang messen, passende Manschette auswählen',
         'kw': ['manschette', 'größe', 'umfang', 'oberarm', 'breit']},
        {'key': 'herzhoehe', 'label': 'Manschette in Herzhöhe anlegen',
         'hint': 'Arm bequem lagern, Manschette 2-3 cm über der Ellenbeuge',
         'kw': ['herzhöhe', 'herz höhe', 'höhe des herz', 'ellenbeu', 'unterstütz', 'arm lagern', 'arm liegt', 'ablegen']},
        {'key': 'messen', 'label': 'Messung durchführen',
         'hint': 'Manschette aufpumpen, langsam ablassen, Werte ablesen',
         'kw': ['aufpump', 'aufpumpen', 'ablassen', 'ableass', 'stethoskop', 'messen', 'messung', 'ablesen', 'systol', 'diastol']},
        {'key': 'dokumentieren', 'label': 'Werte dokumentieren & melden',
         'hint': 'Werte in der Pflegekurve eintragen, bei Auffälligkeiten Arzt informieren',
         'kw': ['dokument', 'aufschreib', 'notier', 'eintrag', 'kurve', 'arzt informier', 'arzt sagen', 'arzt bescheid', 'meld']},
    ],
    'vocab': [
        ('systolisch',     'oberer Wert beim Blutdruck'),
        ('diastolisch',    'unterer Wert beim Blutdruck'),
        ('Manschette',     'aufblasbare Hülle für die Messung'),
        ('Hypertonie',     'erhöhter Blutdruck'),
        ('Riva-Rocci',     'Erfinder der Blutdruckmessung – Abkürzung „RR"'),
        ('Auskultation',   'Abhören mit dem Stethoskop'),
    ],
}


def detect_fall_steps(case: dict, user_text: str, already_done: list) -> list:
    """Return the keys of newly-completed steps after this user message."""
    text = (user_text or '').lower()
    newly = []
    for step in case['steps']:
        if step['key'] in already_done:
            continue
        if any(kw in text for kw in step['kw']):
            newly.append(step['key'])
    return newly


def build_fall_blutdruck_prompt(first_name: str, language_level: str,
                                completed_keys: list, last_completed: str = '') -> str:
    """System prompt for the Frau-Schmidt blood-pressure case study."""
    case = FALL_BLUTDRUCK
    p = case['patient']
    level_desc = {
        'A1': 'sehr einfaches Deutsch, Sätze max. 8 Wörter, Fachbegriffe sofort erklären',
        'A2': 'einfaches Deutsch, kurze klare Sätze, alltagsnahe Worte',
        'B1': 'klares Standarddeutsch, Pflegefachbegriffe mit kurzer Erklärung',
        'B2': 'normales Pflegedeutsch, Fachterminologie frei',
        'C1': 'vollständige medizinische Terminologie',
    }.get(language_level, 'verständliches Deutsch')

    done_set = set(completed_keys or [])
    steps_lines = []
    next_step = None
    for i, s in enumerate(case['steps'], start=1):
        mark = '[✓]' if s['key'] in done_set else '[ ]'
        steps_lines.append(f"{mark} {i}. {s['label']} — {s['hint']}")
        if next_step is None and s['key'] not in done_set:
            next_step = s
    steps_block = '\n'.join(steps_lines)

    progress_note = ''
    if last_completed:
        last_step = next((s for s in case['steps'] if s['key'] == last_completed), None)
        if last_step:
            progress_note = (
                f'\n\n## SOEBEN KORREKT GENANNT\n'
                f'„{last_step["label"]}" — bestätige das in 1 Satz positiv und konkret '
                f'(z. B. „Genau, du prüfst das Armband — sicher!"), '
                f'dann gehe direkt zum NÄCHSTEN offenen Schritt über.'
            )

    next_block = ''
    if next_step:
        next_block = (
            f'\n\n## NÄCHSTER ZU ERFRAGENDER SCHRITT\n'
            f'{next_step["label"]} — {next_step["hint"]}\n'
            f'Stelle dazu EINE kurze offene Frage. Verrate die Antwort NICHT vorab.'
        )
    else:
        next_block = (
            '\n\n## ALLE SCHRITTE ABGESCHLOSSEN\n'
            f'Fasse den Fall in 2 Sätzen zusammen, lobe {first_name} ehrlich '
            'und beende mit „Damit ist der Fall abgeschlossen."'
        )

    return f"""Du bist Professor Wagner, ein erfahrener Pflegepädagoge.
Du leitest {first_name} (Sprachniveau {language_level}) Schritt für Schritt durch eine reale Pflegesituation.

## Patientin
- {p['name']}, {p['age']} Jahre, {p['room']}
- Beschwerde: {p['complaint']}
- Vorerkrankung: {p['history']}
- Auftrag: {p['order']}

## Sprache
{level_desc}. Halte Antworten KURZ — max. 3 Sätze.

## Persönlichkeit
- Du nennst dich nie „KI" — du bist Prof. Wagner
- Sanft, ermutigend, geduldig
- Sprichst {first_name} mit Vornamen an

## Ablauf-Checkliste (nutze sie als roten Faden)
{steps_block}{progress_note}{next_block}

## Regeln
- Genau EINE Frage pro Antwort
- Niemals mehrere Schritte gleichzeitig abfragen
- Keine Aufzählungen, kein Markdown — nur fließender Text
- Bei „__GREETING__" sage exakt: „{first_name}, wir gehen ins Zimmer 214 zu Frau Schmidt. Sie klagt über Schwindel — was machst du als Erstes?"
"""


def generate_slide_from_speech(speech: str, module_title: str) -> tuple:
    """Slide generation is handled by llm_api /generate_presentation."""
    return '', []


# ── Student context helper for AI prompts ─────────────
def build_student_context(user) -> str:
    """Build a context string describing the student for AI prompts."""
    parts = [f"Schülerprofil: {user.first_name} {user.last_name}"]
    parts.append(f"Sprachniveau: {user.language_level or 'A1'}")
    parts.append(f"Pflegewissen: {user.nursing_level or 'beginner'}")
    if user.country:
        parts.append(f"Herkunftsland: {user.country}")
    if user.language:
        parts.append(f"Muttersprache: {user.language}")
    if user.speciality:
        parts.append(f"Fachbereich: {user.speciality}")
    return '\n'.join(parts)


def generate_flashcards(module, language_level: str, student_context: str = '', num_cards: int = 5) -> list:
    """Generate flashcards via llm_api endpoint."""
    payload = {
        'course_id': str(module.course_id) if hasattr(module, 'course_id') and module.course_id else 'all',
        'num_cards': int(num_cards or 5),
        'level': language_level or 'simple',
        'student_context': student_context or '',
    }
    result = _safe_post('/generate_flashcards', payload)
    cards = result.get('flashcards', []) if isinstance(result, dict) else []
    return cards if isinstance(cards, list) else []


def generate_library_summary(module, language_level: str, student_context: str = '') -> str:
    """Generate library summary via llm_api endpoint."""
    payload = {
        'course_id': str(module.course_id) if hasattr(module, 'course_id') and module.course_id else 'all',
        'level': language_level or 'simple',
        'student_context': student_context or '',
    }
    result = _safe_post('/generate_library_summary', payload)
    return str(result.get('summary', '') or '') if isinstance(result, dict) else ''


def generate_library_cards(module, language_level: str, student_context: str = '') -> list:
    """Generate structured library cards via llm_api endpoint."""
    payload = {
        'course_id': str(module.course_id) if hasattr(module, 'course_id') and module.course_id else 'all',
        'level': language_level or 'simple',
        'student_context': student_context or '',
    }
    result = _safe_post('/generate_library_cards', payload)
    cards = result.get('cards', []) if isinstance(result, dict) else []
    return cards if isinstance(cards, list) else []


def generate_ai_quiz(module, language_level: str, num_questions: int = 5) -> list:
    """Generate quiz via llm_api /generate_quiz endpoint."""
    payload = {
        'course_id': str(module.course_id) if hasattr(module, 'course_id') and module.course_id else 'all'
    }
    result = _safe_post('/generate_quiz', payload)
    quiz_data = result.get('quiz', []) if isinstance(result, dict) else []

    questions = []
    for i, q in enumerate((quiz_data or [])[:num_questions]):
        questions.append({
            'id': i,
            'type': 'multiple_choice',
            'question': q.get('question', ''),
            'options': q.get('options', []),
            'answer': str(q.get('answer_index', 0)),
            'model_answer': str(q.get('answer_index', 0)),
            'explanation': q.get('explanation', ''),
        })
    return questions


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

    # No direct LLM usage here: unresolved free-text answers fall back to model answer display.

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
    """No direct Gemini usage in frontend app; route will use static fallback."""
    return []


def generate_nursing_test_questions() -> list:
    """No direct Gemini usage in frontend app; route will use static fallback."""
    return []


def _seed_demo_courses(teacher_id: int):
    """Seed 3 courses directly based on the PDF materials (blutdruck / herz / menschen)."""
    courses_data = [
        # ── blutdruck.pdf ──────────────────────────────────────────────────
        {
            'title': 'Blutdruckmessung',
            'summary': (
                'Basierend auf dem Kursmaterial „Blutdruck" (Philipp Adrian, 2023). '
                'Grundlagen der Blutdruckmessung nach Riva-Rocci: Physiologie, Messtechniken, '
                'Normalwerte und korrekte Durchführung.'
            ),
            'level': 'B1',
            'modules': [
                {
                    'title': 'Geschichte und Definition des Blutdrucks',
                    'description': 'Erfindung der Blutdruckmessung, Begriffe systolisch/diastolisch, Einheit mmHg.',
                    'content': (
                        'Geschichte\n'
                        'Der Blutdruck wurde erstmals durch den italienischen Arzt Scipione Riva-Rocci '
                        'messbar gemacht (Abkürzung: RR). Gemessen wird der arterielle Blutdruck; '
                        'die Einheit ist Millimeter Quecksilbersäule (mmHg).\n\n'
                        'Definition\n'
                        'Der Blutdruck ist die Kraft, die das zirkulierende Blut auf die Gefäßwände ausübt. '
                        'Er ist abhängig von der Pumpleistung des Herzens und dem Gefäßwiderstand der Arterien.\n\n'
                        'Systolisch und diastolisch\n'
                        'Während der Systole (Auswurfphase) wird Blut in die Arterien gepumpt → '
                        'systolischer Blutdruck (oberer Wert). '
                        'Während der Diastole (Erschlaffungsphase) erholt sich das Herz → '
                        'diastolischer Blutdruck (unterer Wert).'
                    ),
                },
                {
                    'title': 'Physiologische Grundlagen',
                    'description': 'Pumpleistung, Gefäßwiderstand und Windkesselfunktion der Aorta.',
                    'content': (
                        'Pumpleistung\n'
                        'Die Pumpleistung variiert je nach Schlagvolumen (ml) und Herzfrequenz (Schläge/min). '
                        'Bei Hochleistungssportlern ist das Schlagvolumen groß → Herzfrequenz im Ruhezustand niedrig. '
                        'Unter Belastung steigt die Herzfrequenz → Pumpleistung wird gesteigert. '
                        'Bei kleinen Kindern ist der Puls höher, da der Sauerstoffbedarf größer ist.\n\n'
                        'Gefäßwiderstand\n'
                        'Er ist abhängig vom Durchmesser der Gefäße. '
                        'Je kleiner der Durchmesser, desto größer der Widerstand → desto höher der Blutdruck. '
                        'Bei älteren Menschen sind Arterien durch Arteriosklerose verengt → erhöhter Blutdruck.\n\n'
                        'Windkesselfunktion der Aorta\n'
                        'Die elastische Aorta dehnt sich während der Systole aus und nimmt Blut auf. '
                        'In der Diastole zieht sie sich zusammen und sorgt für gleichmäßigen Blutfluss '
                        'in die peripheren Gefäße.'
                    ),
                },
                {
                    'title': 'Methoden der Blutdruckmessung',
                    'description': 'Auskultatorische, palpatorische und oszilloskopische Messmethoden.',
                    'content': (
                        'Indirekte (unblutige) Blutdruckmessung\n'
                        'Der Blutdruck kann mithilfe einer Druckmanschette indirekt gemessen werden: '
                        'auskultatorisch (Abhorchen), palpatorisch (Tasten) oder oszillatorisch '
                        '(elektronisches Gerät).\n\n'
                        'Auskultatorische Methode (Standardverfahren)\n'
                        'Benötigt: Blutdruckmanschette mit Manometer + Stethoskop. '
                        'Manschette aufpumpen bis Puls nicht mehr hörbar, dann langsam ablassen. '
                        'Korotkoff-Geräusche: Erstes Geräusch = systolischer Wert, '
                        'Verschwinden = diastolischer Wert.\n\n'
                        'Palpatorische Methode\n'
                        'Eingesetzt wenn Strömungsgeräusche mit Stethoskop nicht hörbar sind. '
                        'Radialispuls tasten, Manschette aufpumpen, dann ablassen. '
                        'Wenn Puls wieder tastbar: = systolischer Wert. Nur systolischer Wert ermittelbar.\n\n'
                        'Oszilloskopische Methode\n'
                        'Automatische Geräte für Heimgebrauch. Misst Schwingungen der Arterienwand. '
                        'Weniger präzise, aber praktisch für Selbstkontrolle.'
                    ),
                },
                {
                    'title': 'Normalwerte und Blutdruckstörungen',
                    'description': 'Normwerte, Hypertonie, Hypotonie und altersbedingte Unterschiede.',
                    'content': (
                        'Normwerte\n'
                        'Optimaler Blutdruck: 120/80 mmHg. '
                        'Normal: < 130/85 mmHg. '
                        'Hoch-normal: 130–139 / 85–89 mmHg.\n\n'
                        'Hypertonie (zu hoher Blutdruck)\n'
                        'Grad 1 (leicht): 140–159 / 90–99 mmHg. '
                        'Grad 2 (mittel): 160–179 / 100–109 mmHg. '
                        'Grad 3 (schwer): ≥ 180/110 mmHg. '
                        'Hypertensiver Notfall: > 180 mmHg systolisch mit Organschäden.\n\n'
                        'Hypotonie (zu niedriger Blutdruck)\n'
                        'Systolisch < 100 mmHg (Frauen) bzw. < 110 mmHg (Männer). '
                        'Symptome: Schwindel, Benommenheit, Ohnmacht. '
                        'Orthostatische Hypotonie: Blutdruckabfall beim Aufstehen.\n\n'
                        'Altersbedingte Unterschiede\n'
                        'Bei älteren Menschen ist ein höherer Wert physiologisch. '
                        'Kinder haben niedrigere Normwerte als Erwachsene.'
                    ),
                },
                {
                    'title': 'Durchführung und Dokumentation',
                    'description': 'Korrekte Messtechnik, Fehlerquellen und Dokumentationspflichten.',
                    'content': (
                        'Vorbereitung\n'
                        'Patient sitzt oder liegt entspannt, Arm auf Herzhöhe gelagert. '
                        'Keine körperliche Aktivität in den letzten 5 Minuten. '
                        'Richtige Manschettengröße: breite für adipöse Patienten, '
                        'schmale für Kinder.\n\n'
                        'Durchführung\n'
                        'Manschette am Oberarm anlegen (2 cm über Ellenbeuge). '
                        'Auf ca. 30 mmHg über erwartetem Wert aufpumpen. '
                        'Langsam (2 mmHg/s) ablassen, Korotkoff-Geräusche abhören.\n\n'
                        'Häufige Fehlerquellen\n'
                        'Manschette zu locker → falsch niedrige Werte. '
                        'Arm nicht auf Herzhöhe → Abweichungen ±8 mmHg je 10 cm. '
                        'Zu schnelles Ablassen → falsch niedrige systolische Werte. '
                        'Weißkittel-Effekt: Stress erhöht den Blutdruck in der Praxis.\n\n'
                        'Dokumentation\n'
                        'Messwert (systolisch/diastolisch), Arm (links/rechts), '
                        'Körperposition (sitzend/liegend), Uhrzeit, Puls, Besonderheiten.'
                    ),
                },
            ],
        },
        # ── herz.pdf ──────────────────────────────────────────────────────
        {
            'title': 'Anatomie des Herzens',
            'summary': (
                'Basierend auf dem Kursmaterial „Anatomie Herz" (Thomas Kruse, 2023). '
                'Aufbau, Funktion und Kreisläufe des Herzens: Kammern, Klappen, '
                'Erregungsleitung und Herzzyklus.'
            ),
            'level': 'B1',
            'modules': [
                {
                    'title': 'Aufgaben und Lage des Herzens',
                    'description': 'Das Herz als Hohlmuskel – Aufgaben, Lage im Mediastinum und anatomische Grenzen.',
                    'content': (
                        'Aufgaben des Herzens\n'
                        'Das Herz (Cor) treibt als Hohlmuskel alle Transportvorgänge in den Blutgefäßen an '
                        '(„zentrale Pumpe"). Es versorgt den Körper mit Sauerstoff und Nährstoffen, '
                        'transportiert Stoffwechselendprodukte (CO₂) ab und produziert Hormone zur '
                        'Regulation von Kreislauf und Flüssigkeitshaushalt.\n\n'
                        'Lage\n'
                        'Das Herz liegt im Mediastinum (Raum zwischen den Lungen). '
                        'Größe: etwa so groß wie eine geschlossene Faust. Gewicht: ca. 300 g '
                        '(bei Frauen etwas kleiner). '
                        'Herzspitzenstoß spürbar an der Medioklavicularlinie des 5. ICR '
                        '(Interkostalraum) – liegt er weiter außen, ist das Herz möglicherweise vergrößert.\n\n'
                        'Anatomische Grenzen\n'
                        'Vorne: Rückseite des Brustbeins (Sternum). '
                        'Seitlich: rechte und linke Lunge. '
                        'Hinten: Speiseröhre (Ösophagus). '
                        'Oben: große Gefäßstämme. Unten: Zwerchfell.'
                    ),
                },
                {
                    'title': 'Herzaufbau: Vorhöfe, Kammern und Scheidewand',
                    'description': 'Herzscheidewand, vier Innenräume und ihre Funktion.',
                    'content': (
                        'Zwei Herzhälften\n'
                        'Die Herzscheidewand (Septum) teilt das Herz in zwei Hälften:\n'
                        'Rechte Herzhälfte: Nimmt sauerstoffarmes Blut auf, pumpt es in den Lungenkreislauf.\n'
                        'Linke Herzhälfte: Nimmt sauerstoffreiches Blut aus der Lunge auf, '
                        'presst es über die Aorta in den Körperkreislauf.\n\n'
                        'Vier Innenräume\n'
                        'Jede Herzhälfte besteht aus Vorhof (Atrium) + Kammer (Ventrikel):\n'
                        'Vorhof: Klein und muskelschwach, sammelt Blut ein.\n'
                        'Kammer: Nimmt Blut aus dem Vorhof auf, pumpt es in Körper oder Lunge.\n\n'
                        'Herzscheidewand (Septum)\n'
                        'Vorhofseptum: trennt rechten und linken Vorhof.\n'
                        'Kammerseptum: trennt rechte und linke Kammer.\n\n'
                        'Wanddicke\n'
                        'Linke Kammer: sehr dickwandige Muskulatur (hoher Druck für Körperkreislauf).\n'
                        'Rechte Kammer: dünnwandiger (geringerer Druck für Lungenkreislauf).'
                    ),
                },
                {
                    'title': 'Herzklappen',
                    'description': 'Segel- und Taschenklappen: Funktion, Lage und klinische Bedeutung.',
                    'content': (
                        'Funktion der Herzklappen\n'
                        'Herzklappen sitzen an den Ein- und Ausgängen der Kammern. '
                        'Sie sind nur in eine Richtung öffenbar (Ventilmechanismus) – '
                        'bei Gegendruck erfolgt Klappenschluss → verhindert Blutrückfluss.\n\n'
                        'Segelklappen (zwischen Vorhöfen und Kammern)\n'
                        'Mitralklappe: trennt linken Vorhof von linker Kammer, 2 Segel '
                        '(Bikuspidalklappe). '
                        'Trikuspidalklappe: trennt rechten Vorhof von rechter Kammer, 3 Segel. '
                        'Verbunden mit Papillarmuskeln über Sehnenfäden → verhindert Zurückschlagen.\n\n'
                        'Taschenklappen (zwischen Kammern und großen Schlagadern)\n'
                        'Aortenklappe: zwischen linker Kammer und Aorta. '
                        'Pulmonalklappe: zwischen rechter Kammer und A. pulmonalis. '
                        'Taschenförmige Mulden → schließen bei höherem Druck in den Arterien.\n\n'
                        'Klinische Bedeutung\n'
                        'Herzklappenfehler: Stenose (Enge, erschwerter Fluss) oder '
                        'Insuffizienz (undichte Klappe, Blutrückfluss).'
                    ),
                },
                {
                    'title': 'Herzkreisläufe',
                    'description': 'Kleiner (Lungen-) und großer (Körper-) Kreislauf.',
                    'content': (
                        'Kleiner Kreislauf (Lungenkreislauf)\n'
                        'Rechtes Herz → Lunge → linkes Herz.\n'
                        'Rechte Kammer pumpt sauerstoffarmes Blut über die A. pulmonalis in die Lunge. '
                        'In der Lunge wird CO₂ abgegeben, O₂ aufgenommen. '
                        'Sauerstoffreiches Blut fließt über Lungenvenen zum linken Vorhof.\n\n'
                        'Großer Kreislauf (Körperkreislauf)\n'
                        'Linkes Herz → Körper → rechtes Herz.\n'
                        'Linke Kammer pumpt sauerstoffreiches Blut über die Aorta in alle Organe. '
                        'O₂ und Nährstoffe werden abgegeben, CO₂ aufgenommen. '
                        'Sauerstoffarmes Blut kehrt über Hohlvenen (V. cava) zum rechten Vorhof zurück.\n\n'
                        'Herzminutenvolumen (HMV)\n'
                        'HMV = Schlagvolumen × Herzfrequenz. '
                        'Normwert in Ruhe: ca. 5 Liter/min. '
                        'Bei Belastung: bis 25 Liter/min.'
                    ),
                },
                {
                    'title': 'Erregungsleitung und Herzzyklus',
                    'description': 'Sinusknoten, AV-Knoten, HIS-Bündel und die Phasen des Herzzyklusses.',
                    'content': (
                        'Erregungsleitung\n'
                        'Sinusknoten (Schrittmacher, 60–80/min): im rechten Vorhof, '
                        'erzeugt elektrischen Impuls. '
                        'AV-Knoten: verzögert Erregung (Zeit für Ventrikelfüllung). '
                        'HIS-Bündel → Tawara-Schenkel → Purkinje-Fasern: verteilen Erregung in Ventrikel.\n\n'
                        'Herzzyklus\n'
                        'Systole (Anspannungs- + Auswurfphase): '
                        'Kammern kontrahieren → Blut wird ausgeworfen → Herzklappen öffnen/schließen. '
                        'Diastole (Erschlaffungs- + Füllungsphase): '
                        'Kammern entspannen → Blut fließt aus Vorhöfen ein.\n\n'
                        'EKG-Grundlagen\n'
                        'P-Welle: Vorhoferregung. '
                        'QRS-Komplex: Kammererregung (sichtbarer Herzschlag). '
                        'T-Welle: Kammerrückbildung. '
                        'Herzfrequenz: 60–100/min normal; < 60 Bradykardie; > 100 Tachykardie.'
                    ),
                },
            ],
        },
        # ── menschen.pdf ──────────────────────────────────────────────────
        {
            'title': 'Patientenmobilisation',
            'summary': (
                'Basierend auf „Menschen bewegen – sicher und gesund" (BGW, 2023). '
                'Expertenstandard Mobilität in der Pflege, Prävention von Muskel-Skelett-Erkrankungen '
                'und ergonomische Mobilisationstechniken.'
            ),
            'level': 'B2',
            'modules': [
                {
                    'title': 'Grundlagen der Mobilität in der Pflege',
                    'description': 'Bedeutung von Mobilität, Expertenstandard und gesetzliche Grundlagen.',
                    'content': (
                        'Bedeutung der Mobilität\n'
                        'Menschen in ihrer Mobilität zu unterstützen ist wesentliche Aufgabe der Pflege. '
                        'Immobilität erhöht das Risiko für Dekubitus, Pneumonie, Thrombose und '
                        'Muskelabbau. Mobilisierung verbessert Lebensqualität und beschleunigt Genesung.\n\n'
                        'Expertenstandard „Erhaltung und Förderung der Mobilität in der Pflege"\n'
                        'Herausgegeben vom DNQP (Deutsches Netzwerk für Qualitätsentwicklung in der Pflege). '
                        'Ziel: Erhaltung und Förderung der Mobilität pflegebedürftiger Menschen. '
                        'Beinhaltet: Einschätzung, Planung, Durchführung und Evaluation von '
                        'Mobilitätsmaßnahmen.\n\n'
                        'Gesetzliche Grundlagen\n'
                        'Arbeitsschutzgesetz (ArbSchG): Pflicht des Arbeitgebers zur '
                        'Gefährdungsbeurteilung. '
                        'Lastenhandhabungsverordnung (LasthandhabV): Schutz bei manuellem Bewegen. '
                        'SGB XI: Pflegequalität als gesetzliche Anforderung.'
                    ),
                },
                {
                    'title': 'MSE-Prävention: Muskel-Skelett-Erkrankungen',
                    'description': 'Belastungen der Lendenwirbelsäule beim Mobilisieren und Präventionsmaßnahmen.',
                    'content': (
                        'Bedeutung von MSE in der Pflege\n'
                        'Tätigkeiten zur Mobilitätsförderung können das Muskel-Skelett-System '
                        'der Pflegekräfte gefährden. '
                        'MSE (Muskel-Skelett-Erkrankungen) sind häufigste Berufskrankheit in der Pflege, '
                        'insbesondere Schäden an der Lendenwirbelsäule (LWS).\n\n'
                        'Druckbelastungen der LWS\n'
                        'Manuelle Patienten-Transfers erzeugen hohe Druckkräfte auf die LWS '
                        '(bis 3.400 N bei ungünstiger Haltung). '
                        'Besonders risikoreich: Bücken ohne Hilfsmittel, asymmetrische Lasten, '
                        'verdrehte Körperhaltung.\n\n'
                        'Prävention\n'
                        'Rückenschule und ergonomisches Arbeiten. '
                        'Einsatz von Hilfsmitteln (Rutschbrett, Rollstuhl, Hebebühne, Lifter). '
                        'Regelmäßige Schulungen für Pflegepersonal. '
                        'Betriebliches Gesundheitsmanagement (BGM).'
                    ),
                },
                {
                    'title': 'Gefährdungsbeurteilung',
                    'description': 'Schritte der Gefährdungsbeurteilung und tätigkeitsbezogene Analyse.',
                    'content': (
                        'Was ist eine Gefährdungsbeurteilung?\n'
                        'Systematische Analyse von Gefährdungen am Arbeitsplatz. '
                        'Gesetzlich verpflichtend nach ArbSchG §5. '
                        'Ziel: Gefährdungen erkennen → Maßnahmen ableiten → umsetzen → prüfen.\n\n'
                        'Schritte der Gefährdungsbeurteilung\n'
                        '1. Arbeitsbereiche und Tätigkeiten ermitteln.\n'
                        '2. Gefährdungen erkennen.\n'
                        '3. Gefährdungen beurteilen.\n'
                        '4. Schutzmaßnahmen festlegen.\n'
                        '5. Maßnahmen umsetzen.\n'
                        '6. Wirksamkeit prüfen.\n'
                        '7. Dokumentation.\n\n'
                        'Tätigkeitsbezogene Gefährdungsbeurteilung\n'
                        'Unterscheidung: allgemeine Beurteilung (Tätigkeitsgruppen) vs. '
                        'Einzelfallbeurteilung (patientenindividuell). '
                        'Im Pflegeprozess: Mobilitätsstatus des Patienten → '
                        'geeignete Transfermethode → Hilfsmittelbedarf bestimmen.'
                    ),
                },
                {
                    'title': 'Expertenstandard Mobilität: Einschätzungshilfe',
                    'description': 'Einschätzungshilfe beim Bewegen von Menschen: Formular und Anwendung.',
                    'content': (
                        'Einschätzungshilfe beim Bewegen von Menschen\n'
                        'Standardisiertes Instrument zur Beurteilung des Unterstützungsbedarfs '
                        'bei der Mobilisation. Verknüpft Expertenstandard mit Arbeitsschutz.\n\n'
                        'Beurteilungskriterien\n'
                        'Körpergewicht und -größe des Patienten. '
                        'Kooperationsfähigkeit (Verständnis, Mitarbeit). '
                        'Restmobilität (Kraft, Gleichgewicht, Beweglichkeit). '
                        'Schmerzen oder Kontrakturen. '
                        'Vorhandene Hilfsmittel.\n\n'
                        'Integration in den Pflegeprozess\n'
                        'Einschätzung bei Aufnahme und bei Veränderungen des Zustands. '
                        'Ergebnis fließt in Pflegeplanung ein: '
                        'welche Transfermethode, welche Hilfsmittel, wie viele Pflegepersonen?\n\n'
                        'Dokumentation\n'
                        'Formular im Pflegebericht → Transparenz für gesamtes Team → '
                        'Schutz vor Haftung bei Unfällen.'
                    ),
                },
                {
                    'title': 'Praktische Mobilisationstechniken',
                    'description': 'Ergonomische Transfer- und Mobilisationsmethoden im Pflegealltag.',
                    'content': (
                        'Grundprinzipien ergonomischen Arbeitens\n'
                        'Aufrechte Körperhaltung, Rücken nicht bücken. '
                        'Kniend oder hockend arbeiten statt gebückt. '
                        'Patient so nah wie möglich heranziehen (kurze Hebelarme). '
                        'Hilfsmittel bevorzugen vor manuellem Heben.\n\n'
                        'Häufige Transfersituationen\n'
                        'Bett → Rollstuhl: Rutschbrett, Dreh-/Transferhilfen nutzen. '
                        'Aufsetzen im Bett: Patient an Bettkante begleiten, Rollbewegung nutzen. '
                        'Aufstehtraining: Stand am Bett, Gleichgewicht üben, Gehstützen. '
                        'Positionswechsel: 30°-Schieflagerung, Mikrolagerung.\n\n'
                        'Hilfsmittel\n'
                        'Rutschbrett/-folie: erleichtert sitzende Transfers. '
                        'Patientenlifter (aktiv/passiv): bei schwerer Pflegebedürftigkeit. '
                        'Stehlifter: für Patienten mit Reststandfähigkeit. '
                        'Rollstühle, Rollatoren: Förderung der Eigenständigkeit.\n\n'
                        'Zielkonflikte\n'
                        'Patientenautonomie vs. Arbeitsschutz: '
                        'Abwägung zwischen Patientenwunsch (ohne Lifter) und Personalgesundheit. '
                        'Lösung: Kommunikation, gemeinsame Entscheidung, Dokumentation.'
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


_DEMO_STUDENTS = [
    # (first, last, country, language, speciality, level, nursing, xp)
    ('Aylin',   'Yılmaz',     'Türkei',     'Türkisch',         'Krankenpflege',         'B2', 'fortgeschritten', 1840),
    ('Mateusz', 'Kowalski',   'Polen',      'Polnisch',         'Altenpflege',           'B1', 'fortgeschritten', 1520),
    ('Maria',   'Santos',     'Philippinen','Filipino / Tagalog','Intensivpflege',       'B2', 'fortgeschritten', 1380),
    ('Andrei',  'Popescu',    'Rumänien',   'Rumänisch',        'Krankenpflege',         'B1', 'mittel',          1100),
    ('Fatima',  'El Amrani',  'Marokko',    'Arabisch',         'Geriatrie',             'A2', 'mittel',           880),
    ('Linh',    'Nguyen',     'Vietnam',    'Vietnamesisch',    'Kinderkrankenpflege',   'B1', 'mittel',           720),
    ('Olena',   'Shevchenko', 'Ukraine',    'Ukrainisch',       'Notfallpflege',         'A2', 'mittel',           560),
    ('Carlos',  'Ferreira',   'Portugal',   'Portugiesisch',    'Palliativpflege',       'B1', 'mittel',           430),
    ('Amara',   'Okafor',     'Sonstiges',  'Englisch',         'Allgemeine Pflege',     'A2', 'beginner',         260),
    ('Goran',   'Petrović',   'Serbien',    'Serbisch',         'OP-Pflege',             'A2', 'beginner',         140),
]


def _seed_demo_students():
    """Seed demo students once so the leaderboard is populated on a fresh DB."""
    from werkzeug.security import generate_password_hash
    from datetime import date as _date, timedelta
    from models import DailyGoal

    today = _date.today()
    for first, last, country, language, speciality, level, nursing, xp in _DEMO_STUDENTS:
        email = f'demo.{first.lower()}@cura.local'
        if User.query.filter_by(email=email).first():
            continue
        student = User(
            role='student',
            email=email,
            password_hash=generate_password_hash('demo'),
            first_name=first,
            last_name=last,
            country=country,
            language=language,
            speciality=speciality,
            language_level=level,
            nursing_level=nursing,
            language_score=8 if level in ('B1', 'B2') else 5,
            nursing_score=8 if nursing == 'fortgeschritten' else (6 if nursing == 'mittel' else 3),
            xp=xp,
        )
        db.session.add(student)
        db.session.flush()
        # Give them a recent daily-goal record so streak/leaderboard look natural
        db.session.add(DailyGoal(
            student_id=student.id,
            date=today - timedelta(days=1),
            target_xp=50,
            earned_xp=60,
        ))
    db.session.commit()


def init_db(app):
    with app.app_context():
        db.create_all()

        # Migrations: add columns + indexes if missing (safe for existing DBs)
        _migrations = [
            'ALTER TABLE course ADD COLUMN current_module_id INTEGER REFERENCES module(id)',
            'ALTER TABLE quiz_attempt ADD COLUMN max_score INTEGER DEFAULT 5',
            'ALTER TABLE quiz_attempt ADD COLUMN pct INTEGER DEFAULT 0',
            'ALTER TABLE quiz_attempt ADD COLUMN next_review_at DATETIME',
            'ALTER TABLE user ADD COLUMN xp INTEGER DEFAULT 0',
            'CREATE INDEX IF NOT EXISTS ix_user_email ON user(email)',
            'CREATE INDEX IF NOT EXISTS ix_enrollment_student_id ON enrollment(student_id)',
            'CREATE INDEX IF NOT EXISTS ix_enrollment_course_id ON enrollment(course_id)',
            'CREATE UNIQUE INDEX IF NOT EXISTS uq_enrollment_student_course ON enrollment(student_id, course_id)',
            'CREATE INDEX IF NOT EXISTS ix_quiz_attempt_student_id ON quiz_attempt(student_id)',
            'CREATE INDEX IF NOT EXISTS ix_quiz_attempt_module_id ON quiz_attempt(module_id)',
            'CREATE INDEX IF NOT EXISTS ix_quiz_attempt_completed_at ON quiz_attempt(completed_at)',
            'CREATE INDEX IF NOT EXISTS ix_module_course_id ON module(course_id)',
            'CREATE INDEX IF NOT EXISTS ix_quiz_question_module_id ON quiz_question(module_id)',
            'CREATE INDEX IF NOT EXISTS ix_flashcard_module_id ON flashcard(module_id)',
            'CREATE INDEX IF NOT EXISTS ix_flashcard_progress_student_id ON flashcard_progress(student_id)',
            'CREATE UNIQUE INDEX IF NOT EXISTS uq_daily_goal_student_date ON daily_goal(student_id, date)',
            'CREATE UNIQUE INDEX IF NOT EXISTS uq_lotto_week_position ON lotto_winner(week_date, position)',
        ]
        for stmt in _migrations:
            try:
                db.session.execute(db.text(stmt))
                db.session.commit()
            except Exception:
                db.session.rollback()

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

        # All known demo title sets (old and new) for cleanup
        OLD_DEMO_TITLES = {'Vitalzeichen und Monitoring', 'Hygiene und Infektionsschutz', 'Wundversorgung und Dekubitus'}
        NEW_DEMO_TITLES = {'Blutdruckmessung', 'Anatomie des Herzens', 'Patientenmobilisation'}
        ALL_DEMO_TITLES = OLD_DEMO_TITLES | NEW_DEMO_TITLES

        # Determine the target owner for demo courses (real teacher if exists, otherwise system teacher)
        real_teacher = User.query.filter(
            User.role == 'teacher',
            User.email != 'lehrer@carelearn.de'
        ).order_by(User.id).first()
        demo_owner = real_teacher if real_teacher else teacher

        # Remove all duplicate demo courses (keep the lowest id per title across all teachers)
        seen = set()
        all_demo_courses = Course.query.filter(Course.title.in_(ALL_DEMO_TITLES)).order_by(Course.id).all()
        for c in all_demo_courses:
            if c.title in seen:
                db.session.delete(c)
            else:
                seen.add(c.title)
        db.session.commit()

        # Check whether the 3 current demo courses already exist (under any teacher)
        existing_new = {c.title for c in Course.query.filter(Course.title.in_(NEW_DEMO_TITLES)).all()}

        # Remove old-style demo courses and seed new ones if not already present
        has_new = NEW_DEMO_TITLES.issubset(existing_new)
        if not has_new:
            for c in Course.query.filter(Course.title.in_(ALL_DEMO_TITLES)).all():
                db.session.delete(c)
            db.session.commit()
            _seed_demo_courses(demo_owner.id)
        else:
            # Ensure all existing new demo courses are owned by demo_owner
            for c in Course.query.filter(Course.title.in_(NEW_DEMO_TITLES)).all():
                if c.owner_id != demo_owner.id:
                    c.owner_id = demo_owner.id
            db.session.commit()

        _seed_demo_students()
