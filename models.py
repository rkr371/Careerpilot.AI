from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )


class ResumeAnalysis(db.Model):
    __tablename__ = 'resume_analyses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    resume_filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    extracted_text = db.Column(db.Text, nullable=True)

    ats_compatibility_score = db.Column(db.Integer, nullable=True)
    overall_score = db.Column(db.Integer, nullable=True)

    strengths = db.Column(db.Text, nullable=True)  # JSON string
    weaknesses = db.Column(db.Text, nullable=True)  # JSON string
    missing_skills = db.Column(db.Text, nullable=True)  # JSON string
    suggested_improvements = db.Column(db.Text, nullable=True)  # JSON string
    career_recommendations = db.Column(db.Text, nullable=True)  # JSON string

    raw_response = db.Column(db.Text, nullable=True)


class LinkedInAnalysis(db.Model):
    __tablename__ = 'linkedin_analyses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    profile_source = db.Column(db.String(50), nullable=False)  # 'url' or 'text'
    upload_date = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    input_excerpt = db.Column(db.Text, nullable=True)

    profile_score = db.Column(db.Integer, nullable=True)

    headline_suggestions = db.Column(db.Text, nullable=True)  # JSON string
    about_improvements = db.Column(db.Text, nullable=True)  # JSON string
    skill_recommendations = db.Column(db.Text, nullable=True)  # JSON string
    networking_recommendations = db.Column(db.Text, nullable=True)  # JSON string
    personal_branding_suggestions = db.Column(db.Text, nullable=True)  # JSON string

    raw_response = db.Column(db.Text, nullable=True)

