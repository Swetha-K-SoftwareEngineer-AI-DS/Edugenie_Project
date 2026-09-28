# 🎓 EduGenie – AI Educational Assistant

> **Tagline:** *Learn Smarter. Understand Better. Grow Faster.*

EduGenie is a modern, full-stack, AI-powered educational assistant designed for students and self-directed learners across various academic stages. It integrates **Google Gemini Generative AI** with a secure **FastAPI** backend, **SQLAlchemy ORM**, **MySQL** database persistence, and a responsive **HTML5 + CSS3 + Vanilla JavaScript** dashboard.

---

## 🌟 Key Features

1. **💬 Ask EduGenie (Educational Chat)**
   - Smart, student-friendly concise answers.
   - Simplified conceptual explanations and real-world analogies.
   - Key takeaway bullet points and instant copy functionality.

2. **🎯 AI Quiz Generator**
   - On-demand multiple-choice quiz generation from topics or textbook passages.
   - Customizable difficulty levels (*Beginner*, *Intermediate*, *Advanced*) and question counts.
   - Interactive quiz interface with real-time progress indicators.
   - Automated evaluation with score percentage, personalized feedback, and detailed explanations for every question.

3. **📑 Smart Summarizer**
   - Condenses long research papers, textbook chapters, or lecture notes.
   - Key takeaways checklist.
   - Glossary extraction with terminology definitions.
   - Original vs. summarized word reduction metrics.

4. **🗺️ Personalized Learning Path**
   - Step-by-step roadmap tailored to student background, career goals, and daily study time.
   - Weekly/modular milestones with learning objectives, hands-on practice, mini-projects, and next steps.
   - Printable and exportable curriculum view.

5. **📊 Unified Activity Tracking**
   - Automatic recording of all student queries, quiz scores, summaries, and roadmaps in MySQL.
   - Real-time history feed on the main dashboard.

6. **🔒 Built-in Web Security**
   - Strict API key isolation (keys reside only in backend `.env`).
   - SQL Injection prevention using SQLAlchemy ORM parameterized queries.
   - Cross-Site Scripting (XSS) mitigation via DOM sanitization and HTML escaping.
   - Rate limiting using SlowAPI.
   - Pydantic schema validation.

---

## 🏗️ Architecture & Technology Stack

```
   ┌────────────────────────────────────────────────────────┐
   │                    Client Browser                      │
   │           HTML5  •  CSS3  •  Vanilla JavaScript        │
   └───────────────────────────┬────────────────────────────┘
                               │ HTTP / REST API (JSON)
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │                  FastAPI Backend Server                │
   │  • Uvicorn ASGI Server     • Pydantic V2 Schemas       │
   │  • SlowAPI Rate Limiting   • CORS Security             │
   └───────────────┬────────────────────────┬───────────────┘
                   │                        │
                   ▼                        ▼
      ┌─────────────────────────┐  ┌─────────────────────────┐
      │   SQLAlchemy 2.0 ORM    │  │    Google Gemini API    │
      │   MySQL 8.0 / MariaDB   │  │   (gemma-4-31b-it)      │
      │   (SQLite fallback)     │  │   Controlled Prompts    │
      └─────────────────────────┘  └─────────────────────────┘
```

### Backend
* **Language:** Python 3.10+
* **Framework:** FastAPI
* **Server:** Uvicorn
* **Database ORM:** SQLAlchemy 2.0
* **MySQL Connector:** PyMySQL + Cryptography
* **AI Integration:** Google Generative AI SDK (`gemma-4-31b-it`)
* **Security & Rate Limiting:** SlowAPI, Passlib (Bcrypt), Python-Jose

### Frontend
* **Core:** Semantic HTML5 & Vanilla JavaScript (No heavy frameworks)
* **Styling:** Custom CSS3 Design System with Light/Dark theme tokens & Glassmorphism
* **Typography:** Plus Jakarta Sans & JetBrains Mono

---

## 📁 Folder Structure

```
Edugenie_Project/
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI Application Entrypoint & Static Server
│   ├── config.py                # Environment & Settings Loader
│   ├── database.py              # SQLAlchemy Engine & Session Provider
│   ├── models.py                # Database Table Models (User, Chat, Quiz, etc.)
│   ├── schemas.py               # Pydantic Request & Response Schemas
│   ├── ai_service.py            # Google Gemini AI Integration & Prompt Templates
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py              # Ask AI Endpoint (/api/chat)
│   │   ├── quiz.py              # Quiz Generator & Evaluation (/api/quiz)
│   │   ├── summary.py           # Summarizer Endpoint (/api/summarize)
│   │   ├── learning.py          # Learning Path Endpoint (/api/learning-path)
│   │   └── activity.py          # Unified Activity Log (/api/activity)
│   └── utils/
│       ├── __init__.py
│       └── security.py          # XSS Sanitizers, JSON Parsers, Password Hasher
├── frontend/
│   ├── index.html               # Responsive Student Dashboard
│   ├── style.css                # Academic Design System & Theme Styles
│   └── script.js                # Frontend Controller & REST API Integration
├── database/
│   └── schema.sql               # MySQL DDL Database Creation Script
├── .env.example                 # Template for environment variables
├── .env                         # Local environment settings (ignored by Git)
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python backend dependencies
└── README.md                    # Project Documentation
```

---

## 🚀 Quickstart Installation Guide

### Step 1: Clone or Navigate to the Project Directory

```bash
cd c:\Users\swethakarunakaran\Downloads\Edugenie_Project
```

### Step 2: Create and Activate a Python Virtual Environment

**Windows (PowerShell or Command Prompt):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (`.env`)

1. Copy `.env.example` to `.env` (or edit existing `.env`):
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and configure your keys:
   ```ini
   # 1. Google Gemini API Key (Get a free key at https://aistudio.google.com/app/apikey)
   GEMINI_API_KEY=AIzaSyYourActualGeminiApiKeyHere

   # 2. MySQL Database Connection URL
   # Replace root:password with your MySQL credentials
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/edugenie_db

   # Set to True to automatically use SQLite if MySQL server is not running
   ALLOW_SQLITE_FALLBACK=True

   # 3. Security Settings
   SECRET_KEY=edugenie_secure_random_key_2026
   ```

### Step 5: (Optional) Initialize MySQL Database

If using MySQL:
1. Start your MySQL service (via XAMPP, MySQL Workbench, or Command Line).
2. Execute the schema script:
   ```bash
   mysql -u root -p < database/schema.sql
   ```
> *Note: If MySQL is not installed or running, the app will smoothly use the local SQLite database automatically (`ALLOW_SQLITE_FALLBACK=True`), allowing you to test immediately.*

### Step 6: Start the Backend Server

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 7: Open the Application in your Browser

Open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

*(Interactive Swagger API docs are available at **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**).*

---

## 📡 REST API Documentation

| Method | Endpoint | Description | Sample Request |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | System & DB health check | *None* |
| `POST` | `/api/chat` | Ask educational questions | `{"question": "Explain photosynthesis."}` |
| `POST` | `/api/quiz` | Generate MCQs from topic/text | `{"topic": "Pythagoras Theorem", "difficulty": "beginner", "question_count": 5}` |
| `POST` | `/api/quiz/evaluate` | Evaluate submitted answers | `{"topic": "...", "questions": [...], "answers": [...]}` |
| `POST` | `/api/summarize` | Summarize educational text | `{"text": "Large passage...", "title": "Optional title"}` |
| `POST` | `/api/learning-path` | Generate personalized roadmap | `{"topic": "SQL", "level": "beginner", "goal": "job-ready", "daily_time": 60, "duration": "8 weeks"}` |
| `GET` | `/api/activity` | Unified student activity log | `/api/activity?limit=10` |

---

## 🛡️ Security Implementation

- **API Key Confidentiality:** The Gemini API key is loaded only inside Python backend process memory and is never transmitted to or rendered in client JavaScript or HTML.
- **SQL Injection Defense:** SQLAlchemy ORM executes all queries with parameterized placeholders.
- **XSS Prevention:** All user inputs and AI generated content are safely escaped before rendering into DOM elements.
- **Controlled Prompt Engineering:** Structured system prompts ensure Gemini returns valid JSON while preventing prompt escape or arbitrary script generation.
- **Rate Limiting:** Protects backend endpoints against brute-force and request flooding.

---

## 💡 Troubleshooting & FAQ

* **Q: I get "AI service is not configured. Please add your GEMINI_API_KEY in the .env file."**
  * **A:** Obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) and paste it into `.env` under `GEMINI_API_KEY=...`. Restart the backend server.
* **Q: I don't have MySQL installed on my computer yet.**
  * **A:** Keep `ALLOW_SQLITE_FALLBACK=True` in `.env`. EduGenie will automatically create an `edugenie.db` SQLite database so all features and database persistence work instantly without manual database installation.
* **Q: Can I change the Gemini model?**
  * **A:** Yes! You can set `GEMINI_MODEL=gemini-1.5-pro` or `GEMINI_MODEL=gemini-1.5-flash` in `.env`.

---

## 📄 License & Academic Note

Developed as a full-stack educational project showcasing modern Generative AI integrations, clean software engineering patterns, and responsive web accessibility.
