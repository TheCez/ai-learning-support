from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    country = db.Column(db.String(80))
    language = db.Column(db.String(80))
    speciality = db.Column(db.String(120))
    language_level = db.Column(db.String(16), default='A1')
    nursing_level = db.Column(db.String(16), default='beginner')
    language_score = db.Column(db.Integer, default=0)
    nursing_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    courses = db.relationship('Course', back_populates='owner', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', back_populates='student', cascade='all, delete-orphan')

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    recommended_level = db.Column(db.String(16), default='A1')
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', back_populates='courses')
    modules = db.relationship('Module', back_populates='course', cascade='all, delete-orphan', order_by='Module.position')
    enrollments = db.relationship('Enrollment', back_populates='course', cascade='all, delete-orphan')

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    module_type = db.Column(db.String(32), nullable=False)
    content = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', back_populates='modules')
    quiz_questions = db.relationship('QuizQuestion', back_populates='module', cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', back_populates='module', cascade='all, delete-orphan')

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_modules = db.Column(db.Integer, default=0)

    student = db.relationship('User', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)
    answer = db.Column(db.String(160), nullable=False)
    multi_choice = db.Column(db.Boolean, default=False)

    module = db.relationship('Module', back_populates='quiz_questions')

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))
    score = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', back_populates='quiz_attempts')
    module = db.relationship('Module', back_populates='quiz_attempts')

class ContentUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    owner = db.relationship('User')
