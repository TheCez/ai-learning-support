from models import db, User, Course, Module

LANGUAGE_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1']

LANGUAGE_TEST = [
    {
        'question': 'Der Patient ___ über Schmerzen in der Brust.',
        'choices': ['klagt', 'spricht', 'sagt', 'ruft'],
        'answer': 'klagt'
    },
    {
        'question': 'Was bedeutet "Vitalzeichen"?',
        'choices': ['Körpergewicht', 'Grundlegende Körperfunktionen', 'Symptome einer Krankheit', 'Medikamente'],
        'answer': 'Grundlegende Körperfunktionen'
    },
    {
        'question': 'Welcher Satz ist grammatisch korrekt?',
        'choices': [
            'Ich habe den Patient gewaschen.',
            'Ich habe dem Patient gewaschen.',
            'Ich habe den Patienten gewaschen.',
            'Ich habe der Patient gewaschen.'
        ],
        'answer': 'Ich habe den Patienten gewaschen.'
    },
    {
        'question': '"Subkutan" bedeutet die Verabreichung...',
        'choices': ['in die Vene', 'in den Muskel', 'unter die Haut', 'auf die Haut'],
        'answer': 'unter die Haut'
    }
]

NURSING_TEST = [
    {
        'question': 'Welche Puls-Frequenz gilt bei einem erwachsenen Patienten in Ruhe als normal?',
        'choices': ['40–60 pro Minute', '60–100 pro Minute', '100–140 pro Minute', '140–180 pro Minute'],
        'answer': '60–100 pro Minute'
    },
    {
        'question': 'Welche der folgenden sind klassische Anzeichen einer Dehydratation?',
        'choices': ['Stehende Hautfalten', 'Trockene Mundschleimhaut', 'Blutdruckanstieg', 'Dunkler Urin'],
        'answer': 'Stehende Hautfalten;Trockene Mundschleimhaut;Dunkler Urin',
        'multi': True
    },
    {
        'question': 'Was ist die korrekte Reihenfolge der hygienischen Händedesinfektion?',
        'choices': [
            'Einreiben, Trocknen, Waschen',
            'Waschen, Einreiben für 30 Sek., Trocknen lassen',
            'Desinfektionsmittel für 30 Sekunden in trockene Hände einreiben',
            'Handschuhe anziehen, dann desinfizieren'
        ],
        'answer': 'Desinfektionsmittel für 30 Sekunden in trockene Hände einreiben'
    }
]

def calculate_language_level(score: int) -> str:
    if score <= 1:
        return 'A2'
    if score == 2:
        return 'B1'
    if score == 3:
        return 'B2'
    return 'C1'

def calculate_nursing_level(score: int) -> str:
    if score <= 1:
        return 'beginner'
    if score == 2:
        return 'intermediate'
    return 'advanced'


def get_ai_professor_response(topic: str, student_level: str) -> str:
    if not topic:
        topic = 'Pflegewissen'
    return (
        f"Professor KI: "
        f"Ich erkläre dir jetzt das Thema '{topic}' auf dem Niveau {student_level}. "
        "Wir starten mit einer kurzen Übersicht, dann kommen Beispiele aus der Pflegepraxis. "
        "Wenn du bereit bist, frage mich bitte nach einem konkreten Fall."
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
                summary='Ein Einsteigerkurs zu Puls, Blutdruck und Atmung für Pflegefachkräfte.',
                recommended_level='A2',
                owner_id=teacher.id
            )
            db.session.add(course)
            db.session.commit()
            module = Module(
                course_id=course.id,
                title='Puls und Blutdruck verstehen',
                description='Grundlagen der Vitalzeichen und erste Interpretation.',
                module_type='quiz',
                content='Lerne die wichtigsten Vitalwerte kennen und beantworte Fragen dazu.',
                position=1
            )
            db.session.add(module)
            db.session.commit()
