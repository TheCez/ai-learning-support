import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Course, Module, Enrollment, QuizQuestion, QuizAttempt, ContentUpload
from services import init_db, calculate_language_level, calculate_nursing_level, LANGUAGE_TEST, NURSING_TEST, get_ai_professor_response

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carelearn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'carelearn-secret-key')

db.init_app(app)
init_db(app)


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
            flash('Die E-Mail-Adresse ist bereits registriert.', 'danger')
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

        flash('Registrierung erfolgreich. Bitte mache zuerst den Sprachtest.', 'success')
        if role == 'student':
            return redirect(url_for('language_test'))
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
            flash('Willkommen zurück.', 'success')
            return redirect(url_for('student_dashboard' if user.role == 'student' else 'teacher_dashboard'))
        flash('E-Mail oder Passwort ist falsch.', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Du wurdest abgemeldet.', 'info')
    return redirect(url_for('index'))


@app.route('/student')
@login_required(role='student')
def student_dashboard(user):
    enrolled = [enrollment.course for enrollment in user.enrollments]
    available = Course.query.filter(~Course.enrollments.any(student_id=user.id)).all()
    return render_template('dashboard_student.html', user=user, enrolled=enrolled, available=available)


@app.route('/teacher')
@login_required(role='teacher')
def teacher_dashboard(user):
    courses = user.courses
    enrollments = Enrollment.query.join(Course).filter(Course.owner_id == user.id).all()
    return render_template('dashboard_teacher.html', courses=courses, enrollments=enrollments)


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
        flash('Sprachtest abgeschlossen.', 'success')
        return redirect(url_for('nursing_test'))
    return render_template('language_test.html', questions=LANGUAGE_TEST)


@app.route('/nursing-test', methods=['GET', 'POST'])
@login_required(role='student')
def nursing_test(user):
    if request.method == 'POST':
        score = 0
        for idx, question in enumerate(NURSING_TEST):
            if question.get('multi'):
                selected = request.form.getlist(f'question_{idx}')
                expected = question['answer'].split(';')
                if all(item in selected for item in expected) and len(selected) == len(expected):
                    score += 1
            else:
                if request.form.get(f'question_{idx}') == question['answer']:
                    score += 1
        user.nursing_score = score
        user.nursing_level = calculate_nursing_level(score)
        db.session.commit()
        flash('Pflegewissen-Test abgeschlossen.', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('nursing_test.html', questions=NURSING_TEST)


@app.route('/courses')
@login_required(role='student')
def courses(user):
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)


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
        flash('Du bist bereits angemeldet.', 'warning')
        return redirect(url_for('course_detail', course_id=course_id))
    enrollment = Enrollment(student_id=user.id, course_id=course.id)
    db.session.add(enrollment)
    db.session.commit()
    flash('Kurs erfolgreich angemeldet.', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/courses/<int:course_id>/module/<int:module_id>')
@login_required(role='student')
def course_module(user, course_id, module_id):
    course = Course.query.get_or_404(course_id)
    module = Module.query.get_or_404(module_id)
    return render_template('module_detail.html', course=course, module=module)


@app.route('/courses/<int:course_id>/module/<int:module_id>/quiz', methods=['GET', 'POST'])
@login_required(role='student')
def course_quiz(user, course_id, module_id):
    module = Module.query.get_or_404(module_id)
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
            answers.append({'question': question.question, 'selected': selected, 'correct': correct})
        attempt = QuizAttempt(student_id=user.id, module_id=module.id, score=score)
        db.session.add(attempt)
        db.session.commit()
        flash(f'Quiz abgeschlossen: {score}/{len(module.quiz_questions)}', 'success')
        return render_template('quiz_result.html', module=module, score=score, answers=answers)
    return render_template('quiz.html', module=module)


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
        flash('Kurs und erstes Modul gespeichert.', 'success')
        return redirect(url_for('teacher_dashboard'))
    return render_template('upload_course.html')


@app.route('/teacher/student-progress')
@login_required(role='teacher')
def student_progress(user):
    enrollments = Enrollment.query.join(Course).filter(Course.owner_id == user.id).all()
    return render_template('student_progress.html', enrollments=enrollments)


@app.route('/ai-professor', methods=['GET', 'POST'])
@login_required(role='student')
def ai_professor(user):
    response = None
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        response = get_ai_professor_response(topic, user.language_level)
    return render_template('ai_professor.html', response=response)


if __name__ == '__main__':
    app.run(debug=True)
