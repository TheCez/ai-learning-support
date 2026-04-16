import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Course, Module, Enrollment, QuizQuestion, QuizAttempt
from services import (init_db, calculate_language_level, calculate_nursing_level,
                      LANGUAGE_TEST, NURSING_TEST, get_ai_professor_response,
                      call_gemini_chat, build_ki_lehrer_system_prompt,
                      generate_slide_from_speech,
                      generate_ai_quiz, evaluate_ai_answers,
                      generate_language_test_questions, generate_nursing_test_questions)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carelearn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'carelearn-secret-key')

db.init_app(app)
init_db(app)


# ── Auth-Decorator ─────────────────────────────
def login_required(role=None):
    def wrapper(fn):
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Bitte melde dich zuerst an.', 'warning')
                return redirect(url_for('login'))
            user = User.query.get(session['user_id'])
            if not user or (role and user.role != role):
                flash('Zugriff verweigert.', 'danger')
                return redirect(url_for('index'))
            return fn(user, *args, **kwargs)
        decorated.__name__ = fn.__name__
        return decorated
    return wrapper


@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return {'current_user': user}


# ── Öffentliche Seiten ─────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        email = request.form['email'].strip().lower()
        password = request.form['password']
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        country = request.form.get('country', '').strip()
        language = request.form.get('language', '').strip()
        speciality = request.form.get('speciality', '').strip()

        if User.query.filter_by(email=email).first():
            flash('Diese E-Mail-Adresse ist bereits registriert.', 'danger')
            return redirect(url_for('register'))

        user = User(
            role=role,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            country=country,
            language=language,
            speciality=speciality,
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id

        if role == 'student':
            flash('Willkommen! Bitte absolviere jetzt den Sprachtest, damit wir deinen Kurs anpassen können.', 'success')
            return redirect(url_for('language_test'))
        flash('Registrierung erfolgreich. Willkommen im Lehrerbereich.', 'success')
        return redirect(url_for('teacher_dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash(f'Willkommen zurück, {user.first_name}!', 'success')
            return redirect(url_for('student_dashboard' if user.role == 'student' else 'teacher_dashboard'))
        flash('E-Mail oder Passwort ist falsch.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Du wurdest erfolgreich abgemeldet.', 'info')
    return redirect(url_for('index'))


# ── Schüler-Bereich ────────────────────────────
@app.route('/student')
@login_required(role='student')
def student_dashboard(user):
    enrolled = [e.course for e in user.enrollments]
    enrolled_ids = [c.id for c in enrolled]
    available = Course.query.filter(Course.id.notin_(enrolled_ids)).all() if enrolled_ids else Course.query.all()

    # Fortschritt je Kurs berechnen
    progress = {}
    for course in enrolled:
        total = len(course.modules)
        if total == 0:
            progress[course.id] = 0
        else:
            done = db.session.query(QuizAttempt.module_id).distinct()\
                .join(Module, QuizAttempt.module_id == Module.id)\
                .filter(Module.course_id == course.id, QuizAttempt.student_id == user.id)\
                .count()
            progress[course.id] = int(done / total * 100)

    onboarding_done = user.language_score > 0 and user.nursing_score > 0

    # Spaced repetition: collect modules due for review
    from datetime import datetime as _dt
    now = _dt.utcnow()
    due_reviews = []
    seen_modules = set()
    latest_attempts = db.session.query(QuizAttempt)\
        .filter_by(student_id=user.id)\
        .order_by(QuizAttempt.completed_at.desc()).all()
    for attempt in latest_attempts:
        if attempt.module_id in seen_modules:
            continue
        seen_modules.add(attempt.module_id)
        if attempt.next_review_at and attempt.next_review_at <= now:
            mod = Module.query.get(attempt.module_id)
            if mod:
                delta = now - attempt.next_review_at
                days_overdue = delta.days
                due_label = 'heute' if days_overdue == 0 else f'vor {days_overdue} Tag(en)'
                due_reviews.append({
                    'module_title': mod.title,
                    'course_title': mod.course.title if mod.course else '',
                    'pct': attempt.pct or 0,
                    'due_since': due_label,
                    'quiz_url': f'/courses/{mod.course_id}/module/{mod.id}/quiz' if mod.course_id else '#',
                })

    return render_template(
        'dashboard_student.html',
        user=user,
        enrolled=enrolled,
        available=available,
        progress=progress,
        onboarding_done=onboarding_done,
        due_reviews=due_reviews,
    )


# ── Onboarding-Tests ───────────────────────────
@app.route('/language-test', methods=['GET'])
@login_required(role='student')
def language_test(user):
    return render_template('language_test.html')


@app.route('/api/language-test/generate', methods=['GET'])
@login_required(role='student')
def api_language_test_generate(user):
    from flask import jsonify
    questions = generate_language_test_questions()
    if not questions:
        # Fallback to static questions converted to unified format
        questions = [
            {'type': 'multiple_choice', 'question': q['question'],
             'options': q['choices'], 'answer': q['answer']}
            for q in LANGUAGE_TEST
        ]
    return jsonify({'questions': questions})


@app.route('/api/language-test/submit', methods=['POST'])
@login_required(role='student')
def api_language_test_submit(user):
    from flask import jsonify
    data = request.get_json(silent=True) or {}
    questions = data.get('questions', [])
    answers = {str(k): v for k, v in data.get('answers', {}).items()}

    results = evaluate_ai_answers(questions, answers, user.language_level or 'A1')
    score = sum(r['score'] for r in results)

    user.language_score = score
    user.language_level = calculate_language_level(score)
    db.session.commit()

    return jsonify({'score': score, 'total': len(results),
                    'level': user.language_level, 'results': results})


@app.route('/nursing-test', methods=['GET'])
@login_required(role='student')
def nursing_test(user):
    return render_template('nursing_test.html')


@app.route('/api/nursing-test/generate', methods=['GET'])
@login_required(role='student')
def api_nursing_test_generate(user):
    from flask import jsonify
    questions = generate_nursing_test_questions()
    if not questions:
        questions = [
            {'type': 'multiple_choice' if not q.get('multi') else 'multiple_choice',
             'question': q['question'], 'options': q['choices'], 'answer': q['answer']}
            for q in NURSING_TEST
        ]
    return jsonify({'questions': questions})


@app.route('/api/nursing-test/submit', methods=['POST'])
@login_required(role='student')
def api_nursing_test_submit(user):
    from flask import jsonify
    data = request.get_json(silent=True) or {}
    questions = data.get('questions', [])
    answers = {str(k): v for k, v in data.get('answers', {}).items()}

    results = evaluate_ai_answers(questions, answers, user.language_level or 'A1')
    score = sum(r['score'] for r in results)

    user.nursing_score = score
    user.nursing_level = calculate_nursing_level(score)
    db.session.commit()

    return jsonify({'score': score, 'total': len(results),
                    'level': user.nursing_level, 'results': results})


# ── Kurse ──────────────────────────────────────
@app.route('/courses')
@login_required(role='student')
def courses(user):
    all_courses = Course.query.all()
    enrolled_ids = {e.course_id for e in user.enrollments}
    return render_template('courses.html', courses=all_courses, enrolled_ids=enrolled_ids)


@app.route('/courses/<int:course_id>')
@login_required(role='student')
def course_detail(user, course_id):
    course = Course.query.get_or_404(course_id)
    enrolled = Enrollment.query.filter_by(course_id=course.id, student_id=user.id).first()
    return render_template('course_detail.html', course=course, enrolled=enrolled)


@app.route('/courses/<int:course_id>/enroll')
@login_required(role='student')
def enroll_course(user, course_id):
    course = Course.query.get_or_404(course_id)
    if Enrollment.query.filter_by(student_id=user.id, course_id=course.id).first():
        flash('Du bist bereits in diesem Kurs angemeldet.', 'warning')
        return redirect(url_for('course_detail', course_id=course_id))
    enrollment = Enrollment(student_id=user.id, course_id=course.id)
    db.session.add(enrollment)
    db.session.commit()
    flash(f'Erfolgreich in "{course.title}" eingeschrieben!', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/courses/<int:course_id>/module/<int:module_id>')
@login_required(role='student')
def course_module(user, course_id, module_id):
    course = Course.query.get_or_404(course_id)
    module = Module.query.get_or_404(module_id)
    last_attempt = QuizAttempt.query.filter_by(
        student_id=user.id, module_id=module_id
    ).order_by(QuizAttempt.completed_at.desc()).first()
    return render_template('module_detail.html', course=course, module=module, last_attempt=last_attempt)


@app.route('/courses/<int:course_id>/module/<int:module_id>/quiz', methods=['GET'])
@login_required(role='student')
def course_quiz(user, course_id, module_id):
    module = Module.query.get_or_404(module_id)
    return render_template('quiz.html', module=module, course_id=course_id)


@app.route('/api/quiz/generate/<int:module_id>', methods=['GET'])
@login_required(role='student')
def api_quiz_generate(user, module_id):
    from flask import jsonify
    module = Module.query.get_or_404(module_id)
    questions = generate_ai_quiz(module, user.language_level or 'A2')
    if not questions:
        # Fallback: convert static DB questions if available
        if module.quiz_questions:
            questions = []
            for q in module.quiz_questions:
                opts = q.options.split(';') if q.options else []
                questions.append({
                    'id': q.id, 'type': 'multiple_choice',
                    'question': q.question, 'options': opts,
                    'answer': q.answer.split(';')[0],
                })
        else:
            return jsonify({'error': 'Keine Fragen verfügbar – bitte Seite neu laden.'}), 503
    return jsonify({'questions': questions})


@app.route('/api/quiz/submit', methods=['POST'])
@login_required(role='student')
def api_quiz_submit(user):
    from flask import jsonify
    data = request.get_json(silent=True) or {}
    module_id = data.get('module_id')
    questions = data.get('questions', [])
    answers = {str(k): v for k, v in data.get('answers', {}).items()}

    if not module_id or not questions:
        return jsonify({'error': 'Fehlende Daten'}), 400

    from datetime import datetime, timedelta
    module = Module.query.get_or_404(module_id)
    results = evaluate_ai_answers(questions, answers, user.language_level or 'A2')
    score = sum(r['score'] for r in results)
    total = len(results)
    pct = int(score / total * 100) if total else 0

    # Spaced repetition: schedule next review based on performance
    if pct >= 90:
        review_days = 14       # Almost perfect → 2 weeks
    elif pct >= 70:
        review_days = 7        # Good → 1 week
    elif pct >= 50:
        review_days = 3        # OK → 3 days
    else:
        review_days = 1        # Struggling → tomorrow

    next_review = datetime.utcnow() + timedelta(days=review_days)

    attempt = QuizAttempt(
        student_id=user.id, module_id=module.id,
        score=score, max_score=total, pct=pct,
        next_review_at=next_review
    )
    db.session.add(attempt)

    enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=module.course_id).first()
    if enrollment:
        done = db.session.query(QuizAttempt.module_id).distinct()\
            .join(Module, QuizAttempt.module_id == Module.id)\
            .filter(Module.course_id == module.course_id, QuizAttempt.student_id == user.id)\
            .count()
        enrollment.completed_modules = done + 1

    db.session.commit()
    return jsonify({
        'score': score, 'total': total, 'pct': pct, 'results': results,
        'next_review_days': review_days,
        'next_review_date': next_review.strftime('%d.%m.%Y'),
    })


# ── Lehrer-Bereich ─────────────────────────────
@app.route('/teacher')
@login_required(role='teacher')
def teacher_dashboard(user):
    courses = user.courses
    enrollments = Enrollment.query.join(Course).filter(Course.owner_id == user.id).all()
    return render_template('dashboard_teacher.html', user=user, courses=courses, enrollments=enrollments)


@app.route('/teacher/course/new', methods=['GET', 'POST'])
@login_required(role='teacher')
def create_course(user):
    if request.method == 'POST':
        title = request.form['title'].strip()
        summary = request.form['summary'].strip()
        level = request.form['recommended_level']
        module_title = request.form['module_title'].strip()
        module_description = request.form['module_description'].strip()
        module_type = request.form['module_type']
        content_body = request.form.get('content_body', '').strip()

        course = Course(title=title, summary=summary, recommended_level=level, owner_id=user.id)
        db.session.add(course)
        db.session.flush()
        module = Module(
            course_id=course.id,
            title=module_title,
            description=module_description,
            module_type=module_type,
            content=content_body,
            position=1
        )
        db.session.add(module)
        db.session.commit()
        flash(f'Kurs "{title}" und erstes Modul gespeichert.', 'success')
        return redirect(url_for('teacher_course', course_id=course.id))
    return render_template('upload_course.html')


@app.route('/teacher/course/<int:course_id>')
@login_required(role='teacher')
def teacher_course(user, course_id):
    course = Course.query.get_or_404(course_id)
    if course.owner_id != user.id:
        flash('Zugriff verweigert.', 'danger')
        return redirect(url_for('teacher_dashboard'))
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    return render_template('teacher_course.html', course=course, enrollments=enrollments)


@app.route('/teacher/course/<int:course_id>/set-current-module', methods=['POST'])
@login_required(role='teacher')
def set_current_module(user, course_id):
    course = Course.query.get_or_404(course_id)
    if course.owner_id != user.id:
        flash('Zugriff verweigert.', 'danger')
        return redirect(url_for('teacher_dashboard'))
    module_id = request.form.get('module_id', type=int)
    if module_id:
        module = Module.query.get_or_404(module_id)
        course.current_module_id = module.id
        flash(f'Heutiges Thema gesetzt: "{module.title}"', 'success')
    else:
        course.current_module_id = None
        flash('Heutiges Thema zurückgesetzt.', 'info')
    db.session.commit()
    return redirect(url_for('teacher_course', course_id=course_id))


@app.route('/teacher/course/<int:course_id>/module/new', methods=['POST'])
@login_required(role='teacher')
def add_module(user, course_id):
    course = Course.query.get_or_404(course_id)
    if course.owner_id != user.id:
        flash('Zugriff verweigert.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    title = request.form['module_title'].strip()
    description = request.form['module_description'].strip()
    module_type = request.form['module_type']
    content_body = request.form.get('content_body', '').strip()
    position = len(course.modules) + 1

    module = Module(
        course_id=course.id,
        title=title,
        description=description,
        module_type=module_type,
        content=content_body,
        position=position
    )
    db.session.add(module)
    db.session.commit()
    flash(f'Modul "{title}" hinzugefügt.', 'success')
    return redirect(url_for('teacher_course', course_id=course_id))


@app.route('/teacher/course/<int:course_id>/module/<int:module_id>/add-question', methods=['POST'])
@login_required(role='teacher')
def add_quiz_question(user, course_id, module_id):
    course = Course.query.get_or_404(course_id)
    if course.owner_id != user.id:
        flash('Zugriff verweigert.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    module = Module.query.get_or_404(module_id)
    question_text = request.form['question'].strip()
    # Antwortmöglichkeiten: jede Zeile ist eine Option
    raw_options = request.form['options'].strip()
    options = [o.strip() for o in raw_options.splitlines() if o.strip()]
    answer_raw = request.form['answer'].strip()
    # Mehrere richtige Antworten mit Semikolon trennen
    is_multi = request.form.get('multi_choice') == 'on'

    if not question_text or not options or not answer_raw:
        flash('Bitte alle Felder ausfüllen.', 'danger')
        return redirect(url_for('teacher_course', course_id=course_id))

    q = QuizQuestion(
        module_id=module.id,
        question=question_text,
        options=';'.join(options),
        answer=answer_raw,
        multi_choice=is_multi
    )
    db.session.add(q)
    db.session.commit()
    flash('Quiz-Frage hinzugefügt.', 'success')
    return redirect(url_for('teacher_course', course_id=course_id))


@app.route('/teacher/course/<int:course_id>/module/<int:module_id>/delete-question/<int:question_id>', methods=['POST'])
@login_required(role='teacher')
def delete_quiz_question(user, course_id, module_id, question_id):
    course = Course.query.get_or_404(course_id)
    if course.owner_id != user.id:
        flash('Zugriff verweigert.', 'danger')
        return redirect(url_for('teacher_dashboard'))
    q = QuizQuestion.query.get_or_404(question_id)
    db.session.delete(q)
    db.session.commit()
    flash('Frage gelöscht.', 'info')
    return redirect(url_for('teacher_course', course_id=course_id))


@app.route('/teacher/student-progress')
@login_required(role='teacher')
def student_progress(user):
    enrollments = Enrollment.query.join(Course).filter(Course.owner_id == user.id).all()
    # Fortschrittsdetails je Schüler
    details = []
    for enrollment in enrollments:
        attempts = QuizAttempt.query.filter_by(student_id=enrollment.student_id)\
            .join(Module, QuizAttempt.module_id == Module.id)\
            .filter(Module.course_id == enrollment.course_id)\
            .all()
        best_scores = {}
        for a in attempts:
            if a.module_id not in best_scores or a.score > best_scores[a.module_id]:
                best_scores[a.module_id] = a.score
        details.append({
            'enrollment': enrollment,
            'attempts': len(attempts),
            'modules_done': len(best_scores),
            'total_modules': len(enrollment.course.modules),
        })
    return render_template('student_progress.html', details=details)


# ── KI-Professorin ─────────────────────────────
@app.route('/ai-professor', methods=['GET'])
@login_required(role='student')
def ai_professor(user):
    enrolled_courses = [e.course for e in user.enrollments]
    return render_template(
        'ai_professor.html',
        user=user,
        enrolled_courses=enrolled_courses,
    )


@app.route('/api/ai-professor', methods=['POST'])
@login_required(role='student')
def ai_professor_api(user):
    from flask import jsonify
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', '').strip()
    selected_course_id = data.get('course_id')

    if not topic:
        return jsonify({'error': 'Kein Thema angegeben.'}), 400

    course_context = ''
    if selected_course_id:
        course = Course.query.get(selected_course_id)
        if course and any(e.course_id == selected_course_id for e in user.enrollments):
            parts = [f"Kurs: {course.title}\n{course.summary}"]
            for module in course.modules:
                parts.append(f"Modul: {module.title}\n{module.description}")
                if module.content:
                    parts.append(module.content)
            course_context = '\n\n'.join(parts)

    response_text = get_ai_professor_response(topic, user.language_level, course_context)
    return jsonify({'response': response_text})


# ── KI-Lehrer (interaktiver Avatar-Unterricht) ─
@app.route('/ki-lehrer')
@login_required(role='student')
def ki_lehrer(user):
    from flask import jsonify as _j
    enrolled_courses = [e.course for e in user.enrollments]
    # Pass module content as a dict so Jinja tojson can embed it safely in <script>
    module_data = {}
    for course in enrolled_courses:
        for module in course.modules:
            module_data[str(module.id)] = {
                'title': module.title,
                'course': course.title,
                'level': course.recommended_level,
                'content': module.content or module.description or '',
            }
    return render_template('ki_lehrer.html', user=user,
                           enrolled_courses=enrolled_courses,
                           module_data=module_data)


@app.route('/api/ki-lehrer', methods=['POST'])
@login_required(role='student')
def ki_lehrer_api(user):
    from flask import jsonify
    data = request.get_json(silent=True) or {}
    module_id   = data.get('module_id')
    conversation = data.get('conversation', [])   # [{role:'user'|'model', text:'...'}]
    is_greeting  = data.get('greeting', False)

    module_title = module_content = course_title = ''
    if module_id:
        module = Module.query.get(module_id)
        if module:
            module_title   = module.title
            module_content = module.content or module.description or ''
            course_title   = module.course.title if module.course else ''

    # Today's topic set by the teacher
    today_module_title = today_course_title = ''
    enrolled_courses = [e.course for e in user.enrollments]
    for course in enrolled_courses:
        if course.current_module_id:
            today_mod = Module.query.get(course.current_module_id)
            if today_mod:
                today_module_title = today_mod.title
                today_course_title = course.title
                break

    system = build_ki_lehrer_system_prompt(
        user.first_name, user.language_level,
        module_title, course_title, module_content,
        today_module_title, today_course_title
    )

    # Welcome without module: single short greeting sentence
    if is_greeting and not module_id and not conversation:
        welcome_system = (
            f"Du bist Professor Wagner. Begrüße {user.first_name} mit genau einem einzigen Satz: "
            f"'Hallo {user.first_name}, hier ist Prof. Wagner – bitte wähle oben ein Modul aus, um zu starten.' "
            f"Sage exakt diesen Satz, leicht variiert, auf Deutsch. Kein weiterer Text."
        )
        response_text = call_gemini_chat(welcome_system, [{'role': 'user', 'text': '__WELCOME__'}])
        return jsonify({'response': response_text})

    # Begrüßungs-Trigger: leere History → synthetische User-Nachricht
    if is_greeting and not conversation:
        contents = [{'role': 'user', 'text': '__GREETING__'}]
    else:
        contents = [{'role': c['role'], 'text': c['text']} for c in conversation[-20:]]

    speech = call_gemini_chat(system, contents)

    # Generate slide from the actual speech text (not the greeting)
    slide_title  = ''
    slide_points = []
    slide_source = ''
    if not is_greeting and speech and not speech.startswith('Fehler'):
        slide_title, slide_points = generate_slide_from_speech(speech, module_title)
        # First sentence of speech as source anchor for the slide
        first_sentence = speech.split('.')[0].strip()
        slide_source = first_sentence[:140] + ('…' if len(first_sentence) > 140 else '')

    return jsonify({'response': speech, 'slide_title': slide_title,
                    'slide_points': slide_points, 'slide_source': slide_source})


@app.route('/api/tts-proxy', methods=['POST'])
def tts_proxy():
    """TTS via ElevenLabs for TalkingHead lip sync.

    TalkingHead sends:  { "input": {"ssml": "..."}, "voice": {...}, "audioConfig": {...} }
    We return:          { "audioContent": "<base64 MP3>", "timepoints": [] }
    """
    import re as _re, base64, json as _j, urllib.request, urllib.error

    api_key = os.environ.get('ELEVENLABS_API_KEY', '')
    if not api_key:
        return _j.dumps({'error': 'ELEVENLABS_API_KEY not set'}), 503, {'Content-Type': 'application/json'}

    data = request.get_json(silent=True) or {}
    inp  = data.get('input') or {}
    raw  = inp.get('ssml', '') or inp.get('text', '')
    text = _re.sub(r'<[^>]+>', ' ', raw)
    text = _re.sub(r'\s+', ' ', text).strip()
    if not text:
        return _j.dumps({'error': 'no text'}), 400, {'Content-Type': 'application/json'}

    voice_id = 'Xb7hH8MSUJpSbSDYk0k2'   # ElevenLabs "Alice" – multilingual, good German
    payload  = _j.dumps({
        'text':     text,
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75, 'style': 0.2},
    }).encode('utf-8')

    req = urllib.request.Request(
        f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128',
        data=payload, method='POST'
    )
    req.add_header('xi-api-key', api_key)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            audio_bytes = r.read()
    except urllib.error.HTTPError as e:
        return e.read(), e.code, {'Content-Type': 'application/json'}
    except Exception as e:
        return _j.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}

    encoded = base64.b64encode(audio_bytes).decode('utf-8')
    # TalkingHead requires 'timepoints' key — without it crashes internally, silencing audio
    return _j.dumps({'audioContent': encoded, 'timepoints': []}), 200, {'Content-Type': 'application/json; charset=utf-8'}


@app.route('/api/stt', methods=['POST'])
def stt_proxy():
    """Speech-to-text via ElevenLabs Scribe for user voice input."""
    import json as _j, urllib.request, urllib.error

    api_key = os.environ.get('ELEVENLABS_API_KEY', '')
    if not api_key:
        return _j.dumps({'error': 'ELEVENLABS_API_KEY not set'}), 503, {'Content-Type': 'application/json'}

    audio_data = request.get_data()
    if not audio_data:
        return _j.dumps({'error': 'no audio'}), 400, {'Content-Type': 'application/json'}

    content_type = request.content_type or 'audio/webm'
    ext = 'webm' if 'webm' in content_type else 'mp3' if 'mp3' in content_type else 'webm'

    boundary = 'el11boundary'
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="model_id"\r\n\r\nscribe_v1\r\n'
        f'--{boundary}\r\nContent-Disposition: form-data; name="language_code"\r\n\r\nde\r\n'
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.{ext}"\r\n'
        f'Content-Type: {content_type}\r\n\r\n'
    ).encode('utf-8') + audio_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

    req = urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text', data=body, method='POST')
    req.add_header('xi-api-key', api_key)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = _j.loads(r.read())
            return _j.dumps({'text': result.get('text', '')}), 200, {'Content-Type': 'application/json'}
    except urllib.error.HTTPError as e:
        return e.read(), e.code, {'Content-Type': 'application/json'}
    except Exception as e:
        return _j.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}


@app.route('/debug-env')
def debug_env():
    import sys
    lines = [
        f"Python: {sys.executable}",
        f"GOOGLE_API_KEY gesetzt: {bool(os.environ.get('GOOGLE_API_KEY'))}",
    ]
    try:
        from google import genai
        lines.append(f"google-genai: OK (v{genai.__version__})")
    except Exception as e:
        lines.append(f"google-genai Import-Fehler: {type(e).__name__}: {e}")
    return "<br>".join(lines)


if __name__ == '__main__':
    app.run(debug=True)
