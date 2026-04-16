import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Course, Module, Enrollment, QuizQuestion, QuizAttempt
from services import init_db, calculate_language_level, calculate_nursing_level, LANGUAGE_TEST, NURSING_TEST, get_ai_professor_response

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
    return render_template(
        'dashboard_student.html',
        user=user,
        enrolled=enrolled,
        available=available,
        progress=progress,
        onboarding_done=onboarding_done
    )


# ── Onboarding-Tests ───────────────────────────
@app.route('/language-test', methods=['GET', 'POST'])
@login_required(role='student')
def language_test(user):
    if request.method == 'POST':
        score = 0
        for idx, question in enumerate(LANGUAGE_TEST):
            answer = request.form.get(f'question_{idx}', '')
            if answer == question['answer']:
                score += 1
        user.language_score = score
        user.language_level = calculate_language_level(score)
        db.session.commit()
        flash(f'Sprachtest abgeschlossen – dein Niveau: {user.language_level}', 'success')
        return redirect(url_for('nursing_test'))
    return render_template('language_test.html', questions=LANGUAGE_TEST)


@app.route('/nursing-test', methods=['GET', 'POST'])
@login_required(role='student')
def nursing_test(user):
    if request.method == 'POST':
        score = 0
        for idx, question in enumerate(NURSING_TEST):
            if question.get('multi'):
                selected = set(request.form.getlist(f'question_{idx}'))
                expected = set(question['answer'].split(';'))
                if selected == expected:
                    score += 1
            else:
                if request.form.get(f'question_{idx}') == question['answer']:
                    score += 1
        user.nursing_score = score
        user.nursing_level = calculate_nursing_level(score)
        db.session.commit()
        flash(f'Pflegewissen-Test abgeschlossen – dein Niveau: {user.nursing_level}', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('nursing_test.html', questions=NURSING_TEST)


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


@app.route('/courses/<int:course_id>/module/<int:module_id>/quiz', methods=['GET', 'POST'])
@login_required(role='student')
def course_quiz(user, course_id, module_id):
    module = Module.query.get_or_404(module_id)
    if not module.quiz_questions:
        flash('Dieses Modul hat noch keine Quiz-Fragen.', 'warning')
        return redirect(url_for('course_module', course_id=course_id, module_id=module_id))

    if request.method == 'POST':
        answers = []
        score = 0
        for question in module.quiz_questions:
            selected = request.form.getlist(f'question_{question.id}')
            correct = question.answer.split(';')
            if question.multi_choice:
                if set(selected) == set(correct):
                    score += 1
            else:
                if selected and selected[0] == correct[0]:
                    score += 1
            answers.append({
                'question': question.question,
                'selected': selected,
                'correct': correct,
                'is_correct': set(selected) == set(correct) if question.multi_choice else (selected and selected[0] == correct[0])
            })

        attempt = QuizAttempt(student_id=user.id, module_id=module.id, score=score)
        db.session.add(attempt)

        # Modul-Fortschritt im Enrollment aktualisieren
        enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=module.course_id).first()
        if enrollment:
            done = db.session.query(QuizAttempt.module_id).distinct()\
                .join(Module, QuizAttempt.module_id == Module.id)\
                .filter(Module.course_id == module.course_id, QuizAttempt.student_id == user.id)\
                .count()
            enrollment.completed_modules = done + 1  # +1 weil dieser Versuch noch nicht committed ist

        db.session.commit()

        total = len(module.quiz_questions)
        pct = int(score / total * 100) if total else 0
        return render_template('quiz_result.html', module=module, course_id=course_id, score=score, total=total, pct=pct, answers=answers)

    return render_template('quiz.html', module=module, course_id=course_id)


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
