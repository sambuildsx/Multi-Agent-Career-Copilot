<!-- Improved compatibility of back to top link -->
<a id="readme-top"></a>

<h1 align="center">UpStride — Multi-Agent Career Copilot</h1>


<a id="readme-top"></a>

<h3 align="center">Agentic AI GitHub PR Review Assistant</h3>

<p align="center">
An AI-powered platform that helps developers optimize resumes, practice adaptive mock interviews, analyze portfolios, and discover opportunities using specialized AI agents orchestrated with LangGraph.
<br />
<br />
<a href="https://youtu.be/7_gCYzwiufg">View Demo</a>
&middot;
<a href="https://github.com/sambuildsx/UpStride-Multi-Agent-Career-Copilot/issues">Report Bug</a>
&middot;
<a href="https://github.com/sambuildsx/UpStride-Multi-Agent-Career-Copilot/issues">Request Feature</a>
</p>

---

# Table of Contents

<details>

<summary>Explore the documentation</summary>

<ol>

<li>
<a href="#about-the-project">About The Project</a>
<ul>
<li><a href="#why-upstride">Why UpStride?</a></li>
<li><a href="#design-principle">Design Principle</a></li>
<li><a href="#built-with">Built With</a></li>
</ul>
</li>

<li><a href="#architecture-highlights">Architecture Highlights</a></li>

<li><a href="#key-features">Key Features</a></li>

<li>
<a href="#workflows">Workflows</a>
<ul>
<li><a href="#workflow-1-resume-analysis">Resume Analysis</a></li>
<li><a href="#workflow-2-adaptive-interview">Adaptive Interview</a></li>
<li><a href="#workflow-3-github-analysis">GitHub Analysis</a></li>
</ul>
</li>

<li><a href="#system-architecture">System Architecture</a></li>

<li><a href="#project-structure">Project Structure</a></li>

<li>
<a href="#getting-started">Getting Started</a>
<ul>
<li><a href="#prerequisites">Prerequisites</a></li>
<li><a href="#installation">Installation</a></li>
</ul>
</li>

<li><a href="#environment-variables">Environment Variables</a></li>

<li><a href="#future-improvements">Future Improvements</a></li>

<li><a href="#license">License</a></li>

<li><a href="#contact">Contact</a></li>

</ol>

</details>

---

# About The Project

UpStride is a production-style multi-agent career assistant designed to help students and software engineers become interview-ready.

Modern job preparation often requires switching between resume analyzers, ATS tools, interview platforms, portfolio reviewers, and job portals.

UpStride brings all of these experiences together in one platform.

Unlike traditional AI applications that rely on a single prompt, UpStride uses multiple specialized AI agents working collaboratively to analyze resumes, conduct interviews, evaluate portfolios, and generate actionable career insights.

The platform combines:

- Resume optimization
- ATS evaluation
- Adaptive mock interviews
- Career coaching
- Job recommendations
- Personalized reports

---

# Architecture Highlights

- Multi-agent orchestration using LangGraph.
- Independent AI agents with dedicated responsibilities.
- Fully asynchronous FastAPI backend.
- Real-time report generation.
- Secure JWT authentication.
- PDF resume parsing.
- Adaptive interview difficulty progression.
- Personalized career recommendations.
- PostgreSQL persistence layer.
- Modular workflows for resume, interview, and GitHub analysis.

---

#  Key Features

---

## Resume Optimization

Upload a resume and receive detailed feedback.

### Features

- Resume parsing
- Skill extraction
- Resume completeness score
- Bullet-point evaluation
- Strength analysis
- Weakness detection
- Actionable recommendations

---

##ATS Evaluation

Analyze resumes against job descriptions.

### Features

- Job description parsing
- Skill-gap analysis
- ATS compatibility scoring
- Missing skills detection
- Personalized improvement suggestions

---

## Adaptive Mock Interviews

The flagship feature of UpStride.

Unlike traditional interview platforms, UpStride dynamically adjusts interview difficulty according to the candidate's performance.

### Features

- AI-generated questions
- Difficulty progression
- Technical evaluation
- Communication analysis
- Adaptive interview flow
- Detailed interview feedback

---

## Career Coaching

Combine insights from all agents into a single career report.

### Features

- Personalized roadmap
- Strength analysis
- Weakness analysis
- Skill recommendations
- Learning suggestions

---

## Job Recommendations

Discover relevant opportunities.

### Features

- Internship recommendations
- Full-time opportunities
- Skill-based filtering
- Direct application links

---

# 🛠️ Built With

## Frontend

- React
- Vite
- Tailwind CSS
- React Router
- Axios

---

## Backend

- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- Background Tasks

---

## AI & Orchestration

- LangGraph
- LangChain
- Gemini
- Groq

---

## Database

- PostgreSQL

---

# Workflows

---

## Workflow 1: Resume Analysis

```text
User
 ↓
Resume Agent
 ↓
JD Agent (Optional)
 ↓
ATS Agent
 ↓
Career Coach
 ↓
Final Report
```

### Agents Involved

- Resume Agent
- JD Agent
- ATS Agent
- Career Coach

---

## Workflow 2: Adaptive Interview

```text
User
 ↓
Planner Agent
 ↓
Interview Agent
 ↓
Technical Evaluator
 ↓
Communication Agent
 ↓
Difficulty Controller
 ↓
Career Coach
 ↓
Final Report
```

### Agents Involved

- Planner Agent
- Interview Agent
- Technical Evaluator
- Communication Agent
- Difficulty Controller
- Career Coach

---

# System Architecture

```text
                         ┌──────────────────┐
                         │      User        │
                         └────────┬─────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │     React Frontend     │
                     └────────┬───────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │     FastAPI Backend     │
                    └────────┬────────────────┘
                             │
                             ▼
                  ┌────────────────────────────┐
                  │   LangGraph Orchestrator   │
                  └────────┬───────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                                     │
        ▼                                     ▼

  Resume Agent                        Interview Agent

        │                                     │

        └──────────────────┼──────────────────┘
                           │
                           ▼

                    Career Coach Agent

                           │
                           ▼

                    Final Career Report

                           │
                           ▼

                       PostgreSQL
```

---

# Project Structure

```text
backend/
│
├── app/
│   ├── agents/
│   ├── graph/
│   ├── routes/
│   ├── prompts/
│   ├── services/
│   ├── db/
│   ├── models/
│   └── utils/
│
├── requirements.txt
└── alembic.ini

frontend/
│
├── src/
│   ├── pages/
│   ├── components/
│   ├── services/
│   └── assets/
│
├── package.json
└── vite.config.js
```

---

# 🗄️ Database Tables

- users
- analysis_jobs
- final_reports
- agent_results
- interview_sessions
- interview_turns

---

# Getting Started

Follow the steps below to run the project locally.

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Gemini API Key

---

## Installation

### Clone Repository

```bash
git clone YOUR_REPOSITORY_URL

cd UpStride
```

---

## Backend Setup

```bash
cd backend

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```

---

### Run Database Migrations

```bash
alembic upgrade head
```

---

### Start Backend

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

---

## Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# Environment Variables

Create a `.env` file:

```env
DATABASE_URL=

JWT_SECRET=

JWT_ALGORITHM=

GEMINI_API_KEY=

GITHUB_TOKEN=

FRONTEND_URL=
```

---

# 📸 Screenshots

## Dashboard

<img src="./assets/dashboard.png"/>

---

## Resume Analysis

<img src="./assets/resume.png"/>

---

## AI Interview

<img src="./assets/interview.png"/>

---

## Final Report

<img src="./assets/report.png"/>

---

# Future Improvements

- Voice interviews
- Coding interviews
- LinkedIn analysis
- Portfolio reviews
- Progress tracking
- Long-term career memory
- Analytics dashboard
- Interview history
- Collaborative feedback

---

# License

Distributed under the MIT License.

---

# Contact

**Samriddhi Bhardwaj**

GitHub:

```text
https://github.com/sambuildsx
```

LinkedIn:

```text
https://linkedin.com/in/YOUR_PROFILE
```

Project Link:

```text
https://github.com/sambuildsx/UpStride-Multi-Agent-Career-Copilot
```

---

<p align="right">(<a href="#readme-top">back to top</a>)</p>
