from flask import Flask, render_template, request, redirect, url_for
from gemini_helper import ask_gemini
from PyPDF2 import PdfReader
from models import db, User
import os

app = Flask(__name__)


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    answer = ""

    if request.method == 'POST':
        question = request.form['question']
        answer = ask_gemini(question)

    return render_template('chat.html', answer=answer)


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
            return "Email already exists"

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect('/dashboard')

    return render_template('login.html')


# Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    result = None

    if request.method == 'POST':
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


if __name__ == '__main__':
    app.run(debug=True)

