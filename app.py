import os
import requests
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Course, Module, Enrollment, QuizQuestion, QuizAttempt
from services import (init_db, calculate_language_level, calculate_nursing_level,
                      LANGUAGE_TEST, NURSING_TEST, get_ai_professor_response,
                      call_ki_lehrer_chat, build_ki_lehrer_system_prompt,
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
@app.route('/favicon.ico')
def favicon():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#1a5c8a"/><path d="M16 25C16 25 7 18.5 7 13.5C7 10.46 9.46 8 12.5 8C14.24 8 15.91 8.9 17 10.18C18.09 8.9 19.76 8 21.5 8C24.54 8 27 10.46 27 13.5C27 18.5 16 25 16 25Z" fill="white" opacity="0.9"/><line x1="16" y1="12" x2="16" y2="18" stroke="#1a5c8a" stroke-width="1.8" stroke-linecap="round"/><line x1="13" y1="15" x2="19" y2="15" stroke="#1a5c8a" stroke-width="1.8" stroke-linecap="round"/></svg>'
    return svg, 200, {'Content-Type': 'image/svg+xml', 'Cache-Control': 'max-age=86400'}

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
    try:
        questions = generate_language_test_questions()
        if questions:
            return jsonify({'questions': questions, 'source': 'llm_api'})

        # Fallback to static questions converted to unified format
        fallback_questions = [
            {'type': 'multiple_choice', 'question': q['question'],
             'options': q['choices'], 'answer': q['answer']}
            for q in LANGUAGE_TEST
        ]
        return jsonify({
            'questions': fallback_questions,
            'source': 'static_fallback',
            'warning': 'LLM API returned no questions. Using fallback set.',
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'language_test_generation_failed',
            'message': 'Sprachtest-Fragen konnten vom LLM-Backend nicht geladen werden.',
            'details': str(e),
            'questions': [],
        }), 502
    except Exception as e:
        return jsonify({
            'error': 'language_test_unexpected_error',
            'message': 'Unerwarteter Fehler bei der Generierung des Sprachtests.',
            'details': str(e),
            'questions': [],
        }), 500


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
        uploaded_pdf = request.files.get('course_pdf')

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

        # Optional: forward uploaded PDF to RAG backend using the newly created course id
        doc_id = None
        if uploaded_pdf and uploaded_pdf.filename:
            if not uploaded_pdf.filename.lower().endswith('.pdf'):
                flash('Kurs gespeichert, aber die Datei war kein PDF und wurde nicht hochgeladen.', 'warning')
            else:
                try:
                    rag_base = os.environ.get('RAG_API_BASE_URL', 'http://localhost:8000/api/v1')
                    upload_url = f"{rag_base}/courses/{course.id}/documents"
                    files = {'file': (uploaded_pdf.filename, uploaded_pdf.stream, 'application/pdf')}
                    data = {'week': 1}
                    upload_resp = requests.post(upload_url, files=files, data=data, timeout=30)
                    upload_resp.raise_for_status()
                    upload_data = upload_resp.json() if upload_resp.content else {}
                    doc_id = (upload_data.get('metadata') or {}).get('doc_id')
                    if doc_id:
                        flash('Kurs gespeichert. PDF wurde hochgeladen und wird nun indexiert.', 'success')
                    else:
                        flash('Kurs gespeichert. PDF wurde hochgeladen, aber ohne doc_id-Antwort.', 'warning')
                except requests.exceptions.RequestException as e:
                    flash(f'Kurs gespeichert, aber PDF-Upload zur RAG-API fehlgeschlagen: {e}', 'warning')

        if not doc_id:
            flash(f'Kurs "{title}" und erstes Modul gespeichert.', 'success')

        return redirect(url_for('teacher_course', course_id=course.id, doc_id=doc_id) if doc_id
                        else url_for('teacher_course', course_id=course.id))
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


# ── RAG Upload & Polling ───────────────────────
@app.route('/api/upload', methods=['POST'])
@login_required(role='teacher')
def api_upload_document(user):
    """Upload PDF to RAG API for ingestion and indexing."""
    if 'file' not in request.files:
        return jsonify({'error': 'Keine Datei hochgeladen'}), 400
    
    file = request.files['file']
    course_id = request.form.get('course_id', type=int)
    week = request.form.get('week', type=int, default=1)
    
    if not file or file.filename == '':
        return jsonify({'error': 'Datei ungültig'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Nur PDF-Dateien erlaubt'}), 400
    
    if not course_id:
        return jsonify({'error': 'course_id erforderlich'}), 400
    
    # Verify user owns the course
    course = Course.query.get(course_id)
    if not course or course.owner_id != user.id:
        return jsonify({'error': 'Zugriff verweigert'}), 403
    
    try:
        rag_base = os.environ.get('RAG_API_BASE_URL', 'http://localhost:8000/api/v1')
        upload_url = f"{rag_base}/courses/{course_id}/documents"
        
        # Prepare multipart form data
        files = {'file': (file.filename, file.stream, 'application/pdf')}
        data = {'week': week}
        
        # POST to RAG API
        response = requests.post(upload_url, files=files, data=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        doc_id = result.get('metadata', {}).get('doc_id', '')
        
        return jsonify({
            'success': True,
            'doc_id': doc_id,
            'message': f'Datei "{file.filename}" erfolgreich hochgeladen'
        }), 200
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout beim Upload. Versuche es später.'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Upload fehlgeschlagen: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Fehler: {str(e)}'}), 500


@app.route('/api/upload/ready/<int:course_id>/<doc_id>', methods=['GET'])
@login_required(role='teacher')
def api_check_upload_ready(user, course_id, doc_id):
    """Poll the RAG API to check if document is ready for use."""
    # Verify user owns the course
    course = Course.query.get(course_id)
    if not course or course.owner_id != user.id:
        return jsonify({'error': 'Zugriff verweigert'}), 403
    
    try:
        rag_base = os.environ.get('RAG_API_BASE_URL', 'http://localhost:8000/api/v1')
        ready_url = f"{rag_base}/courses/{course_id}/documents/{doc_id}/ready"
        
        response = requests.get(ready_url, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return jsonify(result), 200
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Abfrage fehlgeschlagen: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Fehler: {str(e)}'}), 500


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

    validated_course_id = None
    if selected_course_id not in (None, ''):
        try:
            selected_course_id_int = int(selected_course_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'Ungültige course_id.'}), 400

        # Only allow courses the student is enrolled in.
        if not any(e.course_id == selected_course_id_int for e in user.enrollments):
            return jsonify({'error': 'Kurs-Kontext nicht erlaubt.'}), 403

        validated_course_id = str(selected_course_id_int)

    response_text = get_ai_professor_response(topic, user.language_level, validated_course_id)
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
    data = request.get_json(silent=True) or {}
    module_id = data.get('module_id')
    requested_course_id = data.get('course_id')
    conversation = data.get('conversation', [])   # [{role:'user'|'model', text:'...'}]
    is_greeting  = data.get('greeting', False)

    # Resolve course_id pipeline: frontend-provided course_id, else derive from module, else 'all'.
    resolved_course_id = None
    if requested_course_id not in (None, '', 'null', 'undefined'):
        resolved_course_id = str(requested_course_id)
    elif module_id not in (None, ''):
        try:
            module = Module.query.get(int(module_id))
            if module and module.course_id:
                resolved_course_id = str(module.course_id)
        except (TypeError, ValueError):
            pass

    if not resolved_course_id:
        resolved_course_id = 'all'

    print(f"DEBUG: KI-Lehrer route resolved course_id: {resolved_course_id}")

    # Call the external LLM API for KI-Lehrer generation
    result = call_ki_lehrer_chat(
        course_id=resolved_course_id,
        conversation=conversation,
        is_greeting=is_greeting,
        user_first_name=user.first_name
    )

    return jsonify(result)


@app.route('/api/tts-proxy', methods=['POST'])
def tts_proxy():
    """TTS proxy for TalkingHead lip sync.

    Primary:  ElevenLabs Alice voice (best quality, requires API key + credits)
    Fallback: edge-tts Microsoft neural voice (free, no key needed)

    TalkingHead sends:  { "input": {"ssml": "..."}, "voice": {...}, "audioConfig": {...} }
    We return:          { "audioContent": "<base64 MP3>", "timepoints": [] }
    """
    import re as _re, base64, json as _j, asyncio, io

    data = request.get_json(silent=True) or {}
    inp  = data.get('input') or {}
    raw  = inp.get('ssml') or inp.get('text') or ''
    text = _re.sub(r'<[^>]+>', ' ', raw)
    text = _re.sub(r'\s+', ' ', text).strip()
    if not text:
        return _j.dumps({'error': 'no text'}), 400, {'Content-Type': 'application/json'}

    # ── 1. Try ElevenLabs if API key present ──────────────────────
    api_key = os.getenv('ELEVENLABS_API_KEY', '')
    if api_key:
        voice_id = 'Xb7hH8MSUJpSbSDYk0k2'
        payload = {
            'text':     text,
            'model_id': 'eleven_multilingual_v2',
            'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75, 'style': 0.2},
        }
        try:
            resp = requests.post(
                f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128',
                headers={
                    'xi-api-key': api_key,
                    'Content-Type': 'application/json',
                    'Accept': 'audio/mpeg',
                },
                json=payload,
                timeout=20,
            )
            if resp.ok:
                audio_bytes = resp.content
                encoded = base64.b64encode(audio_bytes).decode('utf-8')
                return _j.dumps({'audioContent': encoded, 'timepoints': []}), 200, \
                       {'Content-Type': 'application/json; charset=utf-8'}

            print(f"DEBUG: ElevenLabs TTS failed status={resp.status_code} body={resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: ElevenLabs TTS request failed: {type(e).__name__}: {e}")
        except Exception as e:
            print(f"DEBUG: ElevenLabs TTS unexpected error: {type(e).__name__}: {e}")
        
        # any ElevenLabs failure → fall through to edge-tts

    # ── 2. Fallback: edge-tts (Microsoft neural, free) ────────────
    try:
        import edge_tts

        def _split_text_for_tts(t: str, max_len: int = 280):
            # Keep chunks short so edge-tts is less likely to return empty audio.
            parts = []
            current = []
            current_len = 0
            for token in t.split():
                add_len = len(token) + (1 if current else 0)
                if current_len + add_len > max_len:
                    parts.append(' '.join(current))
                    current = [token]
                    current_len = len(token)
                else:
                    current.append(token)
                    current_len += add_len
            if current:
                parts.append(' '.join(current))
            return [p for p in parts if p.strip()]

        async def _synth_chunk(chunk_text, voice):
            buf = io.BytesIO()
            async for chunk in edge_tts.Communicate(chunk_text, voice=voice).stream():
                if chunk.get('type') == 'audio':
                    buf.write(chunk.get('data', b''))
            return buf.getvalue()

        async def _synth_with_retries(full_text):
            voices = ['de-DE-KatjaNeural', 'de-DE-SeraphinaMultilingualNeural', 'de-DE-ConradNeural']
            chunks = _split_text_for_tts(full_text)
            if not chunks:
                return b''

            final_buf = io.BytesIO()
            for part in chunks:
                chunk_audio = b''
                for voice in voices:
                    try:
                        chunk_audio = await _synth_chunk(part, voice)
                    except Exception:
                        chunk_audio = b''
                    if chunk_audio:
                        break
                if chunk_audio:
                    final_buf.write(chunk_audio)

            return final_buf.getvalue()

        audio_bytes = asyncio.run(_synth_with_retries(text))
        if not audio_bytes:
            raise RuntimeError('No audio was received. Please verify that your parameters are correct.')

        encoded = base64.b64encode(audio_bytes).decode('utf-8')
        return _j.dumps({'audioContent': encoded, 'timepoints': []}), 200, \
               {'Content-Type': 'application/json; charset=utf-8'}
    except Exception as e:
        return _j.dumps({'error': f'edge-tts failed: {e}'}), 500, {'Content-Type': 'application/json'}


@app.route('/api/stt', methods=['POST'])
def stt_proxy():
    """Speech-to-text proxy.

    Priority:
      1. OpenAI Whisper  – best German accuracy, handles accents well (free tier)
      2. ElevenLabs Scribe – if Whisper unavailable
      3. Returns {'error': 'stt_unavailable'} → frontend falls back to Web Speech API
    """
    import json as _j, io

    audio_data = request.get_data()
    # Gracefully handle empty audio without crashing
    if not audio_data:
        return _j.dumps({'error': 'no_audio', 'text': ''}), 200, {'Content-Type': 'application/json'}

    content_type = request.content_type or 'audio/webm'
    ext = 'webm' if 'webm' in content_type else 'mp3' if 'mp3' in content_type else 'webm'

    # ── 1. OpenAI Whisper ────────────────────────────────────────
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if openai_key:
        try:
            import openai as _oai
            client = _oai.OpenAI(api_key=openai_key)
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f'audio.{ext}'
            result = client.audio.transcriptions.create(
                model='whisper-1',
                file=audio_file,
                language='de',
                response_format='text',
            )
            text = result.strip() if isinstance(result, str) else (result.text or '').strip()
            return _j.dumps({'text': text}), 200, {'Content-Type': 'application/json'}
        except Exception:
            pass  # fall through to ElevenLabs

    # ── 2. ElevenLabs Scribe ─────────────────────────────────────
    import urllib.request, urllib.error
    el_key = os.environ.get('ELEVENLABS_API_KEY', '')
    if el_key:
        boundary = 'el11boundary'
        body = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="model_id"\r\n\r\nscribe_v1\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="language_code"\r\n\r\nde\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.{ext}"\r\n'
            f'Content-Type: {content_type}\r\n\r\n'
        ).encode('utf-8') + audio_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
        req = urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text', data=body, method='POST')
        req.add_header('xi-api-key', el_key)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                result = _j.loads(r.read())
                return _j.dumps({'text': result.get('text', '')}), 200, {'Content-Type': 'application/json'}
        except Exception:
            pass  # fall through

    # ── 3. No STT available → browser Web Speech API fallback ────
    return _j.dumps({'error': 'stt_unavailable'}), 200, {'Content-Type': 'application/json'}


@app.route('/debug-env')
def debug_env():
    import sys
    lines = [
        f"Python: {sys.executable}",
        f"GOOGLE_API_KEY gesetzt: {bool(os.environ.get('GOOGLE_API_KEY'))}",
        f"ELEVENLABS_API_KEY gesetzt: {bool(os.environ.get('ELEVENLABS_API_KEY'))}",
        f"OPENAI_API_KEY gesetzt: {bool(os.environ.get('OPENAI_API_KEY'))}",
    ]
    try:
        from google import genai
        lines.append(f"google-genai: OK (v{genai.__version__})")
    except Exception as e:
        lines.append(f"google-genai Import-Fehler: {type(e).__name__}: {e}")
    try:
        import openai as _oai
        lines.append(f"openai: OK (v{_oai.__version__})")
    except Exception as e:
        lines.append(f"openai Import-Fehler: {type(e).__name__}: {e}")
    return "<br>".join(lines)


if __name__ == '__main__':
    app.run(
        host=os.environ.get('FLASK_RUN_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_RUN_PORT', '5000')),
        debug=os.environ.get('FLASK_DEBUG', 'true').lower() == 'true',
    )
