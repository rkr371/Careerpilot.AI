# 🚀 CareerPilot AI

> **Your AI-Powered Career Development Assistant**

CareerPilot AI is an intelligent web application designed to help students, job seekers, and professionals accelerate their careers using Artificial Intelligence. It provides resume analysis, LinkedIn profile evaluation, personalized career roadmaps, interview preparation, skill gap analysis, project recommendations, learning resources, and an AI career assistant—all in one platform.

---

## 🌟 Features

### 🔐 User Authentication

* Secure user registration and login
* Session management
* Protected dashboard

### 📄 Resume Analyzer

* Upload PDF resumes
* AI-powered resume analysis
* ATS compatibility insights
* Strengths & weaknesses detection
* Resume improvement suggestions

### 💼 LinkedIn Profile Analyzer

* Analyze LinkedIn profile content
* Profile optimization suggestions
* Skills evaluation
* Professional branding recommendations

### 🛣 Career Roadmap Generator

* Personalized career roadmap
* Step-by-step learning path
* Recommended certifications
* Career milestone planning

### 🎤 AI Interview Preparation

* Technical interview questions
* HR interview questions
* Behavioral interview practice
* Personalized interview guidance

### 📊 Skill Gap Analyzer

* Identify missing skills
* Compare current skills with target career
* Generate improvement recommendations

### 💡 AI Project Recommendation Engine

* Personalized project ideas
* Portfolio-building suggestions
* Beginner to advanced projects
* Resume-enhancing recommendations

### 📚 Learning Resources

* AI-generated learning resources
* Books
* Courses
* Documentation
* Practice platforms

### 🤖 AI Career Assistant

* Career guidance chatbot
* Learning recommendations
* Career advice
* Skill development support

---

# 🛠 Tech Stack

## Backend

* Python
* Flask
* Flask Blueprint
* Flask Session
* SQLite

## Frontend

* HTML5
* CSS3
* Bootstrap 5
* JavaScript
* Jinja2 Templates

## AI

* Google Gemini AI API

## Database

* SQLite

---

# 📂 Project Structure

```text
CareerPilot-AI/
│
├── app.py
├── config.py
├── requirements.txt
├── database.db
│
├── routes/
├── services/
├── models/
├── templates/
├── static/
├── uploads/
└── utils/
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/CareerPilot-AI.git

cd CareerPilot-AI
```

## Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file in the project root.

```env
SECRET_KEY=your_secret_key

GEMINI_API_KEY=your_gemini_api_key

DATABASE_URL=sqlite:///database.db
```

---

## Run Application

```bash
python app.py
```

Open your browser:

```
http://127.0.0.1:5000
```

---

# 📷 Application Modules

* Home
* Login
* Register
* Dashboard
* Resume Analyzer
* LinkedIn Analyzer
* Career Roadmap
* Interview Preparation
* Skill Gap Analyzer
* Project Recommendation
* Learning Resources
* AI Chat Assistant

---

# 🤖 AI Workflow

```text
User Input
      │
      ▼
Flask Backend
      │
      ▼
Prompt Engineering
      │
      ▼
Google Gemini AI
      │
      ▼
Response Processing
      │
      ▼
JSON Parsing
      │
      ▼
Frontend Display
```

---

# 🗄 Database

SQLite is used for storing:

* User Accounts
* Login Credentials
* Session Information
* User Activity
* Career Data

---

# 🔒 Security Features

* Password Hashing
* Session Authentication
* Secure File Uploads
* Environment Variables
* Input Validation
* SQL Injection Protection
* Error Handling

---

# 📌 Future Improvements

* OAuth Login (Google & LinkedIn)
* Resume Score Visualization
* AI Cover Letter Generator
* Resume Builder
* Job Recommendation System
* Email Notifications
* PostgreSQL Support
* Docker Deployment
* CI/CD Pipeline
* Admin Dashboard
* Analytics Dashboard
* Multi-language Support

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push to GitHub

```bash
git push origin feature-name
```

5. Open a Pull Request

---

# 🐞 Known Issues

Current development includes ongoing improvements for:

* Gemini AI response optimization
* JSON response handling
* Resume analysis accuracy
* LinkedIn profile parsing
* Career roadmap generation
* Performance optimization

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Developer

**CareerPilot AI**

Developed with ❤️ using **Python, Flask, SQLite, Bootstrap, and Google Gemini AI**.

---

## ⭐ Support

If you like this project:

⭐ Star this repository

🍴 Fork it

🛠 Contribute to improve CareerPilot AI

---

> **Empowering Careers with Artificial Intelligence 🚀**
> 
