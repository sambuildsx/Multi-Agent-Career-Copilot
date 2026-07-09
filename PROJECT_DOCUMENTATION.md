# Multi-Agent Recruiter Copilot (CareerOS)

## Project Overview
Multi-Agent Recruiter Copilot is a LangGraph-powered multi-agent career optimization platform. It utilizes a sophisticated architecture designed to analyze a candidate's resume, evaluate their GitHub portfolio, compare their profile against a specific Job Description (JD), and provide actionable feedback. The system uses multiple specialized AI agents working concurrently to gather data, evaluate it, and generate a comprehensive career report.

The technology stack includes:
- **Frontend**: React, Tailwind CSS, React Query, Vite
- **Backend**: FastAPI, PostgreSQL, LangGraph, LangChain
- **LLMs & External APIs**: Gemini API (via unified LLMService), GitHub REST & GraphQL APIs

## Project Workflow & Architecture

The application is structured into four distinct layers:

1. **React Frontend**: Handles all user interactions, such as file uploads (resume PDF), job description text entry, GitHub URL input, and displays the final evaluation results on a dashboard. It communicates exclusively with the FastAPI backend.
2. **FastAPI Backend**: Manages authentication, file storage, API responses, and job dispatching.
3. **LangGraph Orchestrator**: Executes the core logic asynchronously. It runs a compiled `StateGraph` that manages the multi-agent pipeline and writes partial/final results back to PostgreSQL.
4. **Agent Pipeline**: 
   - **Ingestion**: Validates inputs (e.g., readable PDF, valid GitHub URL).
   - **Parallel Processing**: 
     - **Resume Agent**: Extracts and processes text from the PDF, scoring bullets and extracting skills.
     - **JD Agent**: Extracts required skills, technologies, and responsibilities from the job description.
     - **GitHub Agent**: Fetches repo data, commit activity, and pinned repositories to evaluate code quality.
   - **ATS Agent**: Runs after Resume and JD agents complete. It deterministically compares skills/keywords and utilizes an LLM for project relevance scoring.
   - **Aggregator**: Compiles all agent outputs into a final actionable report.
   - **Additional Agents**: Include tools for mock interviews, career coaching, and voice-based interactions.

## File Structure & Functionality

Below is an exhaustive breakdown of the project files and what each file does.

### Root Directory
- `Implementation plan`: A detailed architectural blueprint and roadmap for the project.
- `README.md`: The original project README.
- `tree_output.txt`: A text representation of the project's directory structure.

### Backend (`/backend`)
Handles the server logic, agent orchestration, and database operations.
- `requirements.txt`: Python dependencies required for the backend services.
- `alembic.ini`: Configuration for Alembic, used for database migrations.


#### `/backend/app`
- `main.py`: The entry point for the FastAPI application, wiring together routers, middleware, and app initialization.
- `config.py`: Centralized configuration management using Pydantic settings (e.g., database URIs, API keys).
- `__init__.py`: Marks the directory as a Python package.

**`/backend/app/agents`** (AI Agents Logic)
- `base_agent.py`: Abstract base class providing common retry logic and structure for all agents.
- `resume_agent.py`: Parses resume PDFs, extracts structured data (experience, education), and evaluates bullet points.
- `jd_agent.py`: Extracts key requirements, skills, and parameters from job descriptions.
- `github_agent.py`: Integrates with GitHub APIs to evaluate a candidate's portfolio, commit activity, and repo quality.
- `ats_agent.py`: Scores the candidate's resume against the job description using a hybrid deterministic and LLM approach.
- `orchestrator.py`: Manages the flow and coordination between various agents.
- `career_coach.py`: AI agent providing tailored career advice and improvement suggestions.
- `interviewer_agent.py`: Simulates an interview environment for candidates.
- `interview_evaluator.py`: Evaluates the candidate's responses during the mock interview.
- `voice_agent.py`: Handles voice-based interactions for the platform.
- `__init__.py`: Package marker.

**`/backend/app/db`** (Database Setup)
- `session.py`: Configures the SQLAlchemy engine and provides database session management.
- `__init__.py`: Package marker.
- `/migrations/env.py`: Alembic environment setup for running migrations.
- `/migrations/script.py.mako`: Template used by Alembic when generating new migration scripts.

**`/backend/app/graph`** (LangGraph Configuration)
- `graph.py`: Defines and compiles the `StateGraph` that maps out the execution flow of all agents.
- `nodes.py`: Contains node functions that wrap agent executions for the graph.
- `routing.py`: Defines conditional edges for graph routing (e.g., error handling, fan-out logic).
- `state.py`: Defines the `CareerOSState` Pydantic model, representing the shared state mutated by graph nodes.
- `__init__.py`: Package marker.

**`/backend/app/models`** (Database ORM Models)
- `base.py`: SQLAlchemy declarative base for other models to inherit.
- `job.py`: Defines the `analysis_jobs`, `agent_results`, and `final_reports` tables.
- `user.py`: Defines the `users` table for authentication.
- `__init__.py`: Package marker.

**`/backend/app/routers`** (API Endpoints)
- `auth.py`: Endpoints for user registration, login, and JWT token generation.
- `upload.py`: Endpoints for handling PDF resume uploads.
- `analyze.py`: Endpoints for submitting new analysis jobs and retrieving status/results.
- `github.py`: Specific endpoints related to fetching or validating GitHub data.
- `__init__.py`: Package marker.

**`/backend/app/services`** (Business Logic Services)
- `llm_service.py`: Wrapper for the Gemini API (or OpenAI) to provide a unified LLM interface.
- `pdf_service.py`: Utilizes `pdfplumber` to extract raw text and structural data from uploaded PDFs.
- `github_service.py`: GitHub API client with rate-limiting and REST/GraphQL integrations.
- `__init__.py`: Package marker.



**`/backend/tests`** (Unit and Integration Tests)
- `test_agents.py`: Test suite for individual agent behaviors and outputs.
- `test_ats_agent.py`: Specific test suite ensuring the ATS scoring algorithms work correctly.

### Frontend (`/frontend`)
The React application providing the user interface.
- `package.json` & `package-lock.json`: Defines npm dependencies, scripts, and project metadata.
- `vite.config.js`: Configuration for the Vite build tool and development server.
- `tailwind.config.js` & `postcss.config.js`: Configuration for Tailwind CSS styling.
- `.oxlintrc.json`: Linter configuration rules.
- `index.html`: The main HTML template where the React app is mounted.

#### `/frontend/public`
- `favicon.svg`: The website favicon.
- `icons.svg`: SVG sprite sheet containing various UI icons.

#### `/frontend/src`
- `main.jsx`: The entry point for the React application that renders the root component.
- `App.jsx` & `App.css`: The root component establishing layout, routing, and global styles.
- `index.css`: Global CSS containing Tailwind directives and custom utility classes.
- `api.js`: Defines Axios instances with authentication interceptors for API calls.

**`/frontend/src/assets`**
- `hero.png`: Main image asset for the landing page.
- `react.svg` & `vite.svg`: Logos used in the application.

**`/frontend/src/components`** (Reusable UI Elements)
- `AgentSection.jsx`: A collapsible panel component that displays results from a specific agent.
- `RecommendationList.jsx`: Renders a prioritized list of actionable items for the user.
- `ResumeUpload.jsx`: A drag-and-drop file upload component for submitting PDFs.
- `ScoreCard.jsx`: Displays animated, circular scores for various metrics (e.g., ATS Score, GitHub Score).
- `SkillGapBadges.jsx`: Color-coded badges indicating matched versus missing skills.

**`/frontend/src/pages`** (Application Views)
- `AnalyzePage.jsx`: The view where users upload their resume and input job descriptions/GitHub URLs.
- `DashboardPage.jsx`: The main results view that polls for job status and dynamically renders the multi-agent report.
- `InterviewPage.jsx`: Page view for conducting mock interviews.
- `LoginPage.jsx`: User authentication screen for logging in.
- `RegisterPage.jsx` & `SignupPage.jsx`: Views for creating a new user account.

**`/frontend/src/services`**
- `api.js`: Handles specific API endpoint wrappers, abstracting network calls from UI components.
