# Multi-Agent Recruiter Copilot

**Recruiter Copilot** is an AI-powered resume analysis application that utilizes multiple intelligent agents to evaluate candidate resumes against job descriptions, identifying skill gaps, scoring matches, and providing actionable recommendations.

## 🚀 Features

- **Multi-Agent Architecture**: Built with LangGraph and LangChain to utilize specialized AI agents for distinct parts of the analysis process.
- **Automated Resume Parsing**: Extracts content from uploaded PDF and Word document resumes using `pdfplumber`.
- **Intelligent Scoring**: Generates a fit score (0-100) indicating how well a candidate aligns with the requirements.
- **Skill Gap Analysis**: Identifies specifically which required skills a candidate has and which they are missing.
- **Actionable Recommendations**: Provides tailored advice for interviewers and recruiters on how to approach the candidate.
- **Modern UI**: A sleek, responsive, glassmorphism-inspired React frontend built with Vite and Tailwind CSS v4.
- **Secure Authentication**: JWT-based user registration and login system.

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **AI/LLM**: LangChain, LangGraph, Google GenAI
- **Database**: SQLAlchemy (asyncpg / aiosqlite), Alembic
- **Task Queue**: Celery & Redis
- **Security**: Passlib (bcrypt), PyJWT

### Frontend
- **Framework**: React 19 (Vite)
- **Styling**: Tailwind CSS v4
- **Routing**: React Router DOM
- **Icons**: Lucide React
- **HTTP Client**: Axios (with interceptors)

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (if using Celery for background tasks)
- (Optional) PostgreSQL database

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables (create a `.env` file):
   ```env
   # Add required API keys (e.g., GOOGLE_API_KEY) and database URLs
   ```
5. Run the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```
   *The API will be available at `http://127.0.0.1:8000`*

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   *The web app will be available at `http://localhost:5173` (or the port specified by Vite)*

## 🚦 Usage

1. Open the frontend application in your browser.
2. Sign up for a new account or log in.
3. Upload a candidate's resume (PDF or DOCX).
4. Wait for the AI agents to process the resume.
5. Review the generated Dashboard containing the match score, skill breakdown, and recommendations.

## 📁 Project Structure

```text
Multi-agent Recruiter Copilot/
├── backend
│   ├── app
│   │   ├── agents
│   │   │   ├── __init__.py
│   │   │   ├── ats_agent.py
│   │   │   ├── base_agent.py
│   │   │   ├── github_agent.py
│   │   │   ├── jd_agent.py
│   │   │   └── resume_agent.py
│   │   ├── db
│   │   │   ├── migrations
│   │   │   │   ├── env.py
│   │   │   │   └── script.py.mako
│   │   │   ├── __init__.py
│   │   │   └── session.py
│   │   ├── graph
│   │   │   ├── __init__.py
│   │   │   ├── graph.py
│   │   │   ├── nodes.py
│   │   │   ├── routing.py
│   │   │   └── state.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── job.py
│   │   │   └── user.py
│   │   ├── routers
│   │   │   ├── __init__.py
│   │   │   ├── analyze.py
│   │   │   ├── auth.py
│   │   │   ├── github.py
│   │   │   └── upload.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   ├── github_service.py
│   │   │   ├── llm_service.py
│   │   │   └── pdf_service.py
│   │   ├── tasks
│   │   │   ├── __init__.py
│   │   │   └── analysis_task.py
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── main.py
│   ├── tests
│   │   ├── test_agents.py
│   │   └── test_ats_agent.py
│   ├── uploads
│   ├── .env
│   ├── alembic.ini
│   ├── celery_worker.py
│   └── requirements.txt
├── frontend
│   ├── public
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── src
│   │   ├── assets
│   │   │   ├── hero.png
│   │   │   ├── react.svg
│   │   │   └── vite.svg
│   │   ├── components
│   │   │   ├── AgentSection.jsx
│   │   │   ├── RecommendationList.jsx
│   │   │   ├── ResumeUpload.jsx
│   │   │   ├── ScoreCard.jsx
│   │   │   └── SkillGapBadges.jsx
│   │   ├── pages
│   │   │   ├── AnalyzePage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   └── SignupPage.jsx
│   │   ├── services
│   │   │   └── api.js
│   │   ├── api.js
│   │   ├── App.css
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── .gitignore
│   ├── .oxlintrc.json
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── README.md
│   ├── tailwind.config.js
│   └── vite.config.js
├── .gitignore
└── README.md
```

## 📄 License

This project is licensed under the MIT License.
