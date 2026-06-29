from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from gemini_helper import ask_gemini
from PyPDF2 import PdfReader
from models import db, User
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    answer = ""

    if request.method == 'POST':
        question = request.form['question']
        answer = ask_gemini(question)

    return render_template('chat.html', answer=answer)


@app.route('/test_gemini', methods=['GET'])
@login_required
def test_gemini():
    """Isolation test for Gemini connectivity/config."""
    prompt = "Hello Gemini"
    raw = ask_gemini(prompt)
    return {
        "prompt": prompt,
        "response": raw,
    }




# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

with app.app_context():
    db.create_all()


# Home Page
@app.route('/')
def home():
    return render_template('index.html')


# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Please login instead.')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        new_user = User(name=name, email=email, password=password_hash)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('dashboard'))


    return render_template('register.html')


# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Invalid email or password')
            return render_template('login.html')

        # password_hash is stored in DB
        if hasattr(user, 'password') and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid email or password')
        return render_template('login.html')

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))



# Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    result = None

    if request.method == 'POST':
        # Determine which form was submitted
        resume = request.files.get('resume')
        has_resume = bool(resume and resume.filename)

        has_linkedin = any(
            request.form.get(k, '').strip() for k in ('headline', 'skills', 'about')
        )

        if not has_resume and not has_linkedin:
            return render_template(
                'dashboard.html',
                result="Please upload a PDF resume OR fill LinkedIn headline/skills/about, then submit again."
            )

        # ---- Resume Analyzer (PDF) ----
        if has_resume:
            filename = resume.filename
            allowed_ext = {".pdf"}
            _, ext = os.path.splitext(filename.lower())

            if ext not in allowed_ext:
                return render_template(
                    'dashboard.html',
                    result="Invalid file type. Please upload a PDF resume only."
                )

            upload_dir = os.path.join(app.root_path, "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            safe_name = "".join(
                c for c in filename if c.isalnum() or c in (" ", ".", "_", "-")
            ).strip() or "resume.pdf"

            path = os.path.join(upload_dir, safe_name)
            resume.save(path)

            try:
                reader = PdfReader(path)
                text_parts = []
                max_pages = min(len(reader.pages), 6)  # performance: analyze first 6 pages
                max_chars = 12000  # performance: limit context size

                total = 0
                for i in range(max_pages):
                    extracted = reader.pages[i].extract_text() or ""
                    if not extracted.strip():
                        continue

                    if total + len(extracted) > max_chars:
                        extracted = extracted[: max_chars - total]

                    text_parts.append(extracted)
                    total += len(extracted)

                    if total >= max_chars:
                        break

                text = "\n".join(text_parts).strip()

                print(
                    f"[ResumeAnalyzer] Extracted chars: {len(text)}; pages_scanned: {max_pages}; file: {safe_name}"
                )

                if not text:
                    result = (
                        "Could not extract text from the PDF. "
                        "This is common with scanned PDFs. "
                        "Please upload a text-based PDF resume (or a resume with selectable text)."
                    )
                else:
                    prompt = f"""
You are an expert resume reviewer and recruiter (ATS-focused).

Resume Text:
{text}

Return EXACTLY in this format:

ATS_SCORE: <number from 0 to 100>
MISSING_SKILLS:
- <skill 1>
- <skill 2>
IMPROVEMENTS:
1. <improvement 1>
2. <improvement 2>
3. <improvement 3>
KEYWORDS_TO_ADD:
- <keyword 1>
- <keyword 2>
"""
                    print(f"[ResumeAnalyzer] Prompt chars: {len(prompt)}")
                    result = ask_gemini(prompt)
                    print(f"[ResumeAnalyzer] Gemini result chars: {len(result or '')}")


            except Exception as e:
                result = f"Resume processing failed: {str(e)}"

        # ---- LinkedIn Profile Analyzer (optional) ----
        elif has_linkedin:
            headline = request.form.get('headline', '')
            skills = request.form.get('skills', '')
            about = request.form.get('about', '')

            prompt = f"""
Analyze this LinkedIn Profile

Headline:
{headline}

Skills:
{skills}

About:
{about}

Give:
1. Profile Score
2. Missing Skills
3. Better Headline
4. Suggestions
"""
            print(f"[LinkedInAnalyzer] Prompt chars: {len(prompt)}")
            result = ask_gemini(prompt)

    return render_template('dashboard.html', result=result)


import json
from datetime import datetime
from flask import abort

from werkzeug.utils import secure_filename

from models import ResumeAnalysis, LinkedInAnalysis


ALLOWED_RESUME_EXTS = {
    '.pdf', '.docx', '.txt'
}


def _allowed_resume(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_RESUME_EXTS


def _extract_text_from_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    parts = [p.text for p in (doc.paragraphs or []) if p.text and p.text.strip()]
    return "\n".join(parts).strip()


def _extract_text_from_txt(path: str) -> str:
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read().strip()


def _extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    text_parts = []
    max_pages = min(len(reader.pages), 8)
    max_chars = 20000
    total = 0
    for i in range(max_pages):
        extracted = reader.pages[i].extract_text() or ''
        extracted = extracted.strip()
        if not extracted:
            continue
        if total + len(extracted) > max_chars:
            extracted = extracted[: max_chars - total]
        text_parts.append(extracted)
        total += len(extracted)
        if total >= max_chars:
            break
    return "\n".join(text_parts).strip()


# --- AI Routes ---
@app.route('/resume_analyzer', methods=['GET', 'POST'])
@login_required
def resume_analyzer():
    if request.method == 'GET':
        return render_template('resume_analyzer.html', result=None, error_message=None)

    result = None
    error_message = None

    try:
        resume = request.files.get('resume')
        if not resume or not resume.filename:
            error_message = 'Please upload a resume file.'
            return render_template('resume_analyzer.html', result=None, error_message=error_message)

        if not _allowed_resume(resume.filename):
            error_message = 'Invalid file type. Upload PDF, DOCX, or TXT.'
            return render_template('resume_analyzer.html', result=None, error_message=error_message)

        filename = secure_filename(resume.filename)

        upload_root = os.path.join(app.root_path, 'uploads')
        upload_dir = os.path.join(upload_root, 'resume')

        # Ensure uploads/resume is a directory (not a file)
        if os.path.exists(upload_dir) and not os.path.isdir(upload_dir):
            os.replace(upload_dir, f"{upload_dir}.bak.{int(datetime.utcnow().timestamp())}")

        os.makedirs(upload_dir, exist_ok=True)

        # uuid-like unique filename without extra dependencies
        timestamp = int(datetime.utcnow().timestamp())
        path = os.path.join(upload_dir, f"{current_user.id}_{timestamp}_{filename}")

        # Prevent collisions by retrying with a suffix
        attempt = 0
        while os.path.exists(path):
            attempt += 1
            path = os.path.join(upload_dir, f"{current_user.id}_{timestamp}_{attempt}_{filename}")

        # ---- Save uploaded file ----
        try:
            resume.save(path)
            app.logger.info(f"[ResumeAnalyzer] File uploaded successfully: {path}")
            print(f"[ResumeAnalyzer] File saved: {path}")
        except Exception:
            app.logger.exception('[ResumeAnalyzer] Resume file save failed')
            error_message = 'Failed to save the uploaded file. Please try again.'
            return render_template('resume_analyzer.html', result=None, error_message=error_message)

        # ---- Extract resume text ----
        try:
            _, ext = os.path.splitext(filename.lower())
            if ext == '.pdf':
                extracted = _extract_text_from_pdf(path)
            elif ext == '.docx':
                extracted = _extract_text_from_docx(path)
            else:
                extracted = _extract_text_from_txt(path)

            extracted = (extracted or '').strip()
            app.logger.info(f"[ResumeAnalyzer] Resume text extracted. chars={len(extracted)}")
            print(f"[ResumeAnalyzer] Extracted chars: {len(extracted)}")

            if not extracted:
                error_message = 'Could not extract any text from this resume. If it’s a scanned PDF, try a text-based PDF or DOCX.'
                return render_template('resume_analyzer.html', result=None, error_message=error_message)
        except Exception as e:
            app.logger.exception('[ResumeAnalyzer] Text extraction failed')
            error_message = 'Resume text extraction failed. Please try another file.'
            return render_template('resume_analyzer.html', result=None, error_message=error_message)

        # ---- Gemini structured JSON prompt ----
        prompt = f"""
You are an expert resume reviewer and recruiter (ATS-focused).
Return ONLY valid JSON (no markdown, no extra text) that matches this schema exactly:
{{
  "overall_score": 0-100,
  "ats_score": 0-100,
  "strengths": [],
  "weaknesses": [],
  "missing_skills": [],
  "improvements": [],
  "career_recommendations": []
}}

Rules:
- Use numbers for scores.
- Provide arrays (can be empty) for each list.
- Do not wrap JSON in code fences.

Resume text:
{extracted[:18000]}
""".strip()

        app.logger.info(f"[ResumeAnalyzer] Gemini request sent. prompt_chars={len(prompt)}")
        print(f"[ResumeAnalyzer] Gemini request sent. prompt_chars={len(prompt)}")

        raw = ask_gemini(prompt)
        app.logger.info(f"[ResumeAnalyzer] Gemini response received. chars={(len(raw) if raw else 0)}")
        print(f"[ResumeAnalyzer] Gemini response received. chars={(len(raw) if raw else 0)}")

        # ask_gemini returns a user-friendly error string on failure; detect that early
        if raw is None or not str(raw).strip():
            error_message = 'Gemini returned an empty response. Please try again.'
            return render_template('resume_analyzer.html', result=None, error_message=error_message)

        # Parse JSON
        try:
            data = json.loads(raw)
        except Exception:
            # Surface a helpful message and keep raw for logging/DB raw_response
            app.logger.exception('[ResumeAnalyzer] Gemini response was not valid JSON')
            error_message = 'AI returned an unexpected response format. Please try again.'
            return render_template('resume_analyzer.html', result=None, error_message=error_message)

        # Validate minimum expected keys
        required_keys = [
            'overall_score', 'ats_score', 'strengths', 'weaknesses',
            'missing_skills', 'improvements', 'career_recommendations'
        ]
        if any(k not in data for k in required_keys):
            error_message = 'AI response was missing required fields. Please try again.'
            return render_template('resume_analyzer.html', result=None, error_message=error_message)

        # ---- Save to DB ----
        try:
            analysis = ResumeAnalysis(
                user_id=current_user.id,
                resume_filename=filename,
                extracted_text=extracted,
                ats_compatibility_score=int(data.get('ats_score')) if data.get('ats_score') is not None else None,
                overall_score=int(data.get('overall_score')) if data.get('overall_score') is not None else None,
                strengths=json.dumps(data.get('strengths', [])),
                weaknesses=json.dumps(data.get('weaknesses', [])),
                missing_skills=json.dumps(data.get('missing_skills', [])),
                suggested_improvements=json.dumps(data.get('improvements', [])),
                career_recommendations=json.dumps(data.get('career_recommendations', [])),
                raw_response=raw,
            )
            db.session.add(analysis)
            db.session.commit()
            app.logger.info(f"[ResumeAnalyzer] Analysis saved to database: analysis_id={analysis.id}")
            print(f"[ResumeAnalyzer] Analysis saved. id={analysis.id}")
        except Exception:
            app.logger.exception('[ResumeAnalyzer] Database save failed')
            error_message = 'Database error while saving the analysis. Please try again.'
            return render_template('resume_analyzer.html', result=None, error_message=error_message)

        result = {
            'overall_score': analysis.overall_score,
            'ats_score': analysis.ats_compatibility_score,
            'strengths': json.loads(analysis.strengths or '[]'),
            'weaknesses': json.loads(analysis.weaknesses or '[]'),
            'missing_skills': json.loads(analysis.missing_skills or '[]'),
            'improvements': json.loads(analysis.suggested_improvements or '[]'),
            'career_recommendations': json.loads(analysis.career_recommendations or '[]'),
        }

        return render_template('resume_analyzer.html', result=result, error_message=None)

    except Exception as e:
        app.logger.exception('[ResumeAnalyzer] Resume analysis failed (unexpected)')
        error_message = 'AI analysis failed. Please try again.'
        return render_template('resume_analyzer.html', result=None, error_message=error_message)



@app.route('/linkedin_analyzer', methods=['GET', 'POST'])
@login_required
def linkedin_analyzer():
    if request.method == 'GET':
        return render_template('linkedin_analyzer.html', result=None)

    headline = (request.form.get('headline') or '').strip()
    skills = (request.form.get('skills') or '').strip()
    about = (request.form.get('about') or '').strip()

    linkedin_url = (request.form.get('linkedin_url') or '').strip() if 'linkedin_url' in request.form else ''
    source = 'url' if linkedin_url else 'text'

    if not (linkedin_url or headline or skills or about):
        flash('Provide LinkedIn URL or paste headline/skills/about.')
        return redirect(url_for('linkedin_analyzer'))

    input_blob = {
        'linkedin_url': linkedin_url,
        'headline': headline,
        'skills': skills,
        'about': about
    }

    prompt = """
You are an expert LinkedIn profile coach.
Return ONLY valid JSON (no markdown) that matches this schema:
{
  "profile_score": 0-100,
  "headline_suggestions": [string],
  "about_improvements": [string],
  "skill_recommendations": [string],
  "networking_recommendations": [string],
  "personal_branding_suggestions": [string]
}

LinkedIn input:
""" + json.dumps(input_blob) + "\n"


    try:
        raw = ask_gemini(prompt)
        data = json.loads(raw)

        analysis = LinkedInAnalysis(
            user_id=current_user.id,
            profile_source=source,
            input_excerpt=str(input_blob)[:5000],
            profile_score=int(data.get('profile_score')) if data.get('profile_score') is not None else None,
            headline_suggestions=json.dumps(data.get('headline_suggestions', [])),
            about_improvements=json.dumps(data.get('about_improvements', [])),
            skill_recommendations=json.dumps(data.get('skill_recommendations', [])),
            networking_recommendations=json.dumps(data.get('networking_recommendations', [])),
            personal_branding_suggestions=json.dumps(data.get('personal_branding_suggestions', [])),
            raw_response=raw
        )
        db.session.add(analysis)
        db.session.commit()

        result = {
            'profile_score': analysis.profile_score,
            'headline_suggestions': json.loads(analysis.headline_suggestions or '[]'),
            'about_improvements': json.loads(analysis.about_improvements or '[]'),
            'skill_recommendations': json.loads(analysis.skill_recommendations or '[]'),
            'networking_recommendations': json.loads(analysis.networking_recommendations or '[]'),
            'personal_branding_suggestions': json.loads(analysis.personal_branding_suggestions or '[]'),
        }

        return render_template('linkedin_analyzer.html', result=json.dumps(result, indent=2))

    except Exception as e:
        app.logger.exception('LinkedIn analysis failed')
        flash(f'AI analysis failed: {str(e)}')
        return render_template('linkedin_analyzer.html', result=None)



@app.route('/career_roadmap', methods=['GET', 'POST'])
@login_required
def career_roadmap():
    return render_template('career_roadmap.html', result=None)


@app.route('/interview_prep', methods=['GET', 'POST'])
@login_required
def interview_prep():
    return render_template('interview_prep.html', result=None)


@app.route('/skill_gap_analyzer', methods=['GET', 'POST'])
@login_required
def skill_gap_analyzer():
    return render_template('skill_gap_analyzer.html', result=None)


@app.route('/project_recommendations', methods=['GET', 'POST'])
@login_required
def project_recommendations():
    return render_template('project_recommendations.html', result=None)


@app.route('/learning_resources', methods=['GET'])
@login_required
def learning_resources():
    return render_template('learning_resources.html', result=None)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template('settings.html', result=None)


@app.route('/about', methods=['GET'])
@login_required
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)


