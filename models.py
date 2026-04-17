from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ── Friendship (self-referential many-to-many) ──────────
friendship = db.Table('friendship',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
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

    # Gamification
    xp = db.Column(db.Integer, default=0)

    courses = db.relationship('Course', back_populates='owner', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', back_populates='student', cascade='all, delete-orphan')

    friends = db.relationship(
        'User', secondary=friendship,
        primaryjoin='User.id==friendship.c.user_id',
        secondaryjoin='User.id==friendship.c.friend_id',
        lazy='dynamic'
    )

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    recommended_level = db.Column(db.String(16), default='A1')
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    current_module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', back_populates='courses')
    modules = db.relationship('Module', back_populates='course', cascade='all, delete-orphan',
                              foreign_keys='Module.course_id', order_by='Module.position')
    enrollments = db.relationship('Enrollment', back_populates='course', cascade='all, delete-orphan')
    current_module = db.relationship('Module', foreign_keys='Course.current_module_id', post_update=True)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), index=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    module_type = db.Column(db.String(32), nullable=False)
    content = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', back_populates='modules', foreign_keys='Module.course_id')
    quiz_questions = db.relationship('QuizQuestion', back_populates='module', cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', back_populates='module', cascade='all, delete-orphan')

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), index=True)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_modules = db.Column(db.Integer, default=0)

    student = db.relationship('User', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')

    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='uq_enrollment_student_course'),)

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), index=True)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)
    answer = db.Column(db.String(160), nullable=False)
    multi_choice = db.Column(db.Boolean, default=False)

    module = db.relationship('Module', back_populates='quiz_questions')

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), index=True)
    score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, default=5)
    pct = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    next_review_at = db.Column(db.DateTime, nullable=True)

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


# ── Flashcards ─────────────────────────────────────────
class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), index=True)
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    module = db.relationship('Module')


class FlashcardProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcard.id'), index=True)
    box = db.Column(db.Integer, default=0)  # Leitner box 0-4
    next_review = db.Column(db.DateTime, default=datetime.utcnow)
    last_reviewed = db.Column(db.DateTime, nullable=True)

    student = db.relationship('User')
    flashcard = db.relationship('Flashcard')

    __table_args__ = (db.UniqueConstraint('student_id', 'flashcard_id', name='uq_flashcard_progress_student_card'),)


# ── Gamification ───────────────────────────────────────
class DailyGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    date = db.Column(db.Date, default=date.today, index=True)
    target_xp = db.Column(db.Integer, default=50)
    earned_xp = db.Column(db.Integer, default=0)

    student = db.relationship('User')

    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='uq_daily_goal_student_date'),)


class FriendMission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, default='')
    target_xp = db.Column(db.Integer, default=30)
    creator_xp = db.Column(db.Integer, default=0)
    friend_xp = db.Column(db.Integer, default=0)
    deadline = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[creator_id])
    friend = db.relationship('User', foreign_keys=[friend_id])


class LottoWinner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    week_date = db.Column(db.Date, nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User')

    __table_args__ = (db.UniqueConstraint('week_date', 'position', name='uq_lotto_week_position'),)


class CaseStudyAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    case_key = db.Column(db.String(80), nullable=False, index=True)
    steps_completed = db.Column(db.Integer, default=0)
    steps_total = db.Column(db.Integer, default=7)
    xp_earned = db.Column(db.Integer, default=0)
    duration_sec = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User')
