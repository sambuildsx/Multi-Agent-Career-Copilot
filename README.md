# UpStride (Multi-Agent Career Copilot)

## 📌 Overview
UpStride is a production-style Multi-Agent Career Copilot built using FastAPI, LangGraph, React, and Gemini. 

Its mission is to help software engineers become interview-ready through AI-powered resume analysis, portfolio analysis, adaptive mock interviews, and personalized career coaching. The system uses multiple specialized AI agents working concurrently to gather data, evaluate it, and generate a comprehensive career report.

---

## 🏗️ Architecture & Philosophy
The application is structured into four distinct layers:
1. **React Frontend**: Handles all user interactions, such as file uploads (resume PDF), job description text entry, GitHub URL input, and displays the final evaluation results on a dashboard. It communicates exclusively with the FastAPI backend.
2. **FastAPI Backend**: Manages authentication, file storage, API responses, and job dispatching.
3. **LangGraph Orchestrator**: The brain of the system. It executes the core logic asynchronously, managing the multi-agent pipeline and writing results to PostgreSQL.
4. **Agent Pipeline**: Specialized agents perform distinct reasoning tasks, coordinated by the orchestrator.

**Design Principle:**
> Agents perform reasoning. Services perform external operations. The Orchestrator coordinates agents. No agent should perform another agent's responsibility.

### Tech Stack
- **Frontend**: React, Tailwind CSS, Vite
- **Backend**: FastAPI, LangGraph, SQLAlchemy, Pydantic
- **LLMs & APIs**: Gemini, LangChain, GitHub REST & GraphQL APIs
- **Database**: PostgreSQL

---

## ⚙️ Working of the Project & Workflows

The Orchestrator selects workflows, decides the next agent, retries invalid decisions, and validates LLM outputs. It NEVER parses resumes or evaluates answers itself.

### Workflow 1: Resume Optimization
`User -> ResumeAgent -> JDAgent (optional) -> ATSAgent -> CareerCoach -> Done`
- **Resume Agent**: Extracts text from the PDF, scoring bullets and extracting skills.
- **JD Agent**: Extracts required skills and responsibilities from the job description.
- **ATS Agent**: Scores the resume against the job description using deterministic and LLM approaches.

### Workflow 2: AI Mock Interview (Flagship Feature)
`User -> PlannerAgent -> InterviewAgent -> TechnicalEvaluator -> CommunicationAgent -> DifficultyController -> Orchestrator -> (Loop) -> CareerCoach -> Done`
- **PlannerAgent**: Reads inputs and creates an Interview Blueprint.
- **InterviewAgent**: Generates ONE interview question. Avoids repetition and respects the blueprint.
- **TechnicalEvaluator**: Evaluates technical correctness.
- **CommunicationAgent**: Evaluates confidence, grammar, clarity, and professionalism.
- **DifficultyController**: Recommends interview progression based on past scores.

### Workflow 3: GitHub Analysis
`User -> GitHubAgent -> CareerCoach -> Done`
- **GitHub Agent**: Fetches repo data, commit activity, and pinned repositories to evaluate code quality.

---

## 📂 File Structure & Functionality

Here is an exhaustive breakdown of the project files and their purpose:

### Root Directory
- `Implementation plan`: A detailed architectural blueprint and roadmap for the project.
- `README.md`: Project documentation and architecture details.
- `PROJECT_DOCUMENTATION.md`: Additional project details and historical reference.

### Backend (`/backend`)
Handles the server logic, agent orchestration, and database operations.
- `requirements.txt`: Python dependencies.
- `alembic.ini`: Configuration for database migrations.

#### `/backend/app/`
- `main.py`: Entry point for the FastAPI app, wiring routers and middleware.
- `config.py`: Centralized config management (e.g., database URIs, API keys).
- `dependencies.py`: Dependency injection for routes.

**`/backend/app/agents/`** (AI Agents Logic)
- `base_agent.py`: Base class providing common retry logic.
- `orchestrator.py`: Manages flow and coordination between agents.
- `resume_agent.py`: Parses resumes and extracts data.
- `jd_agent.py`: Extracts requirements from job descriptions.
- `github_agent.py`: Integrates with GitHub APIs to evaluate a candidate.
- `ats_agent.py`: Scores candidate resume against JD.
- `planner_agent.py`: Plans the mock interview blueprint.
- `interviewer_agent.py`: Simulates the interview environment.
- `technical_evaluator.py`: Evaluates technical correctness of answers.
- `communication_agent.py`: Evaluates communication skills.
- `difficulty_controller.py`: Adjusts interview difficulty dynamically.
- `career_coach.py`: Provides actionable feedback and roadmaps.

**`/backend/app/graph/`** (LangGraph Configuration)
- `state.py`: Defines the `CareerOSState` Pydantic model for shared state.
- `routing.py`: Defines conditional edges for graph routing.
- `nodes.py`: Contains node functions wrapping agent executions.
- `resume_graph.py`, `interview_graph.py`, `github_graph.py`: Specialized workflow graphs.

**`/backend/app/prompts/`** (LLM Prompts)
- Contains all prompt templates for agents (e.g., `orchestrator_prompt.py`, `coach_prompt.py`). Ensures no duplicated prompts in business logic.

**`/backend/app/routes/`** (API Endpoints)
- `auth.py`: User registration and login.
- `resume.py`, `upload.py`: Handles PDF uploads and resume parsing.
- `github.py`: Endpoints for fetching GitHub data.
- `interview.py`, `dashboard.py`: Handles mock interview progression and retrieving results.

**`/backend/app/services/`** (External Operations)
- `llm_service.py`: Wrapper for the Gemini API.
- `pdf_service.py`: Utilizes `pdfplumber` to extract text from PDFs.
- `github_service.py`: GitHub API client.
- `speech_to_text.py`, `text_to_speech.py`: Voice integration services.
- `embedding_service.py`, `storage_service.py`: Helper services for AI and files.

**`/backend/app/models/`** (Database ORM)
- `base.py`: SQLAlchemy declarative base.
- `user.py`, `resume.py`, `github.py`, `interview.py`, `report.py`: Table definitions.

**`/backend/app/db/`** (Database Setup)
- `session.py`: Database engine and session management.
- `migrations/`: Alembic migration scripts.

**`/backend/app/utils/`** 
- `logger.py`, `constants.py`, `exceptions.py`, `helpers.py`: Utility functions and global constants.

### Frontend (`/frontend`)
The React application providing the user interface.
- `package.json` & `vite.config.js`: Dependencies and build configuration.
- `tailwind.config.js`: Tailwind CSS styling rules.
- `index.html`: Main HTML template.

#### `/frontend/src/`
- `main.jsx` & `App.jsx`: React entry point and root component establishing layout and routing.
- `index.css`: Global CSS and utility classes.

**`/frontend/src/components/`** (Reusable UI Elements)
- `AgentSection.jsx`: Collapsible panel displaying agent results.
- `RecommendationList.jsx`: Renders prioritized actionable items.
- `ResumeUpload.jsx`: Drag-and-drop file upload.
- `ScoreCard.jsx`: Animated, circular scores for metrics.
- `SkillGapBadges.jsx`: Badges indicating matched/missing skills.

**`/frontend/src/pages/`** (Application Views)
- `Dashboard.jsx`: Main view polling for job status.
- `Resume.jsx`: Resume optimization flow.
- `GitHub.jsx`: GitHub review flow.
- `Interview.jsx`: Mock interview platform.
- `Report.jsx`: Final career report.
- `Login.jsx` & `Register.jsx`: Authentication pages.

**`/frontend/src/services/`**
- API endpoint wrappers and Axios interceptors for backend communication.

---

## 🚀 Future Features
- Voice & Coding Interviews
- LinkedIn & Portfolio Review
- Progress Tracking & Interview History