# Career Coach AI

## Overview

Career Coach AI is a production-style Multi-Agent AI system built using FastAPI, LangGraph, React, and Gemini.

The purpose of the application is **not** simply to optimize resumes.

Its mission is:

> Help software engineers become interview-ready through AI-powered resume analysis, portfolio analysis, adaptive mock interviews, and personalized career coaching.

This project should demonstrate **real agent orchestration**, not just multiple LLM API calls.

---

# Architecture Philosophy

This is NOT a chatbot.

This is NOT a sequential pipeline.

This is a Multi-Agent AI System.

The system follows one principle:

> Agents perform reasoning.

> Services perform external operations.

> The Orchestrator coordinates agents.

No agent should perform another agent's responsibility.

---

# Tech Stack

Backend

- FastAPI
- LangGraph
- SQLAlchemy
- Pydantic
- Gemini
- LangChain

Frontend

- React
- TailwindCSS

Database

- PostgreSQL

---

# Existing Architecture

```
backend/

app/

agents/

graph/

routes/

services/

models/

db/
```

---

# Existing Services

Services already exist.

DO NOT move business logic into services.

Services are only wrappers.

Current services:

- LLMService
- PDFService
- GitHubService
- VoiceService (to be added)

---

# Existing Agents

Already implemented

- ResumeAgent
- JDAgent
- ATSAgent
- PlannerAgent
- TechnicalEvaluatorAgent
- CommunicationAgent
- CareerCoachAgent
- OrchestratorAgent

Do NOT redesign these.

Extend them if necessary.

---

# Design Rules

Every agent must have ONE responsibility.

Never merge responsibilities.

Bad example

InterviewAgent

↓

asks question

↓

scores answer

↓

writes report

Good example

InterviewAgent

↓

asks question

TechnicalEvaluator

↓

scores

CareerCoach

↓

summarizes

---

# Orchestrator

The Orchestrator is the brain.

Responsibilities

- Select workflow

- Decide next agent

- Retry invalid decisions

- Validate LLM decisions

- End workflows

The Orchestrator NEVER

- parses resumes

- evaluates answers

- generates interview questions

- summarizes interviews

---

# Workflow 1

Resume Optimization

```
User

↓

ResumeAgent

↓

JDAgent (optional)

↓

ATSAgent

↓

CareerCoach

↓

Done
```

---

# Workflow 2

AI Mock Interview

This is the flagship feature.

```
User

↓

PlannerAgent

↓

InterviewAgent

↓

TechnicalEvaluator

↓

CommunicationAgent

↓

DifficultyController

↓

Orchestrator

↓

InterviewAgent

↓

...

↓

CareerCoach

↓

Done
```

The interview should feel like a real interviewer.

---

# Workflow 3

GitHub Analysis

```
User

↓

GitHubAgent

↓

CareerCoach

↓

Done
```

---

# PlannerAgent

Responsibilities

- Read Resume

- Read Job Description

- Read Target Role

- Create Interview Blueprint

Output

- Topics

- Objectives

- Question Distribution

- Difficulty

- Estimated Questions

Planner NEVER asks questions.

---

# InterviewAgent

Responsibilities

Generate ONE interview question.

Nothing else.

Should

- Ask one question

- Avoid repetition

- Ask follow-up questions

- Respect InterviewPlan

Should NOT

- Evaluate

- Coach

- Summarize

- Route

---

# TechnicalEvaluator

Responsibilities

Evaluate only technical correctness.

Output

- Score

- Strengths

- Weaknesses

- Missing Concepts

---

# CommunicationAgent

Responsibilities

Evaluate

- Confidence

- Grammar

- Clarity

- Professionalism

Should ignore technical correctness.

---

# DifficultyController (Needs Implementation)

Responsibilities

Read

- Technical score

- Communication score

- Interview history

- Current topic

Return

- Increase difficulty

- Decrease difficulty

- Ask follow-up

- Change topic

- End interview

The DifficultyController NEVER generates questions.

It only recommends interview progression.

---

# CareerCoach

Responsibilities

Read

- Resume

- ATS

- GitHub

- Interview

Return

- Final report

- Learning roadmap

- Weaknesses

- Strengths

- Missing skills

- Personalized recommendations

---

# LangGraph Rules

The graph should remain modular.

Do NOT create one giant graph.

Each workflow owns its own graph.

The orchestrator coordinates agents inside the workflow.

---

# State

CareerOSState already exists.

Do NOT redesign it unless necessary.

Use immutable updates with model_copy().

---

# Coding Standards

Production quality.

Every file must contain

- Type hints

- Docstrings

- Logging

- Pydantic models

- Structured output

No duplicated prompts.

No business logic inside routes.

No business logic inside services.

---

# Frontend

Pages

- Dashboard

- Resume Optimization

- GitHub Review

- Mock Interview

- Career Report

Interview UI should resemble a real interview platform.

---

# Future Features

- Voice Interview

- Coding Interview

- LinkedIn Review

- Portfolio Review

- Progress Tracking

- Previous Interview History

---

# Goal

This project should demonstrate

- Multi-Agent AI

- LangGraph

- Agent Orchestration

- Adaptive AI Interviews

- Production Backend Design

Structure of the project :
CareerOS-AI/
│
├── backend/
│   │
│   ├── app/
│   │   │
│   │   ├── agents/
│   │   │   │
│   │   │   ├── base_agent.py
│   │   │   ├── orchestrator.py                ⭐ Brain
│   │   │   │
│   │   │   ├── resume_agent.py
│   │   │   ├── jd_agent.py
│   │   │   ├── ats_agent.py
│   │   │   ├── github_agent.py
│   │   │   │
│   │   │   ├── planner_agent.py
│   │   │   ├── interviewer_agent.py
│   │   │   ├── technical_evaluator.py
│   │   │   ├── communication_agent.py
│   │   │   ├── difficulty_controller.py       ⭐ NEW
│   │   │   ├── career_coach.py
│   │   │   │
│   │   │   └── __init__.py
│   │   │
│   │   ├── graph/
│   │   │   │
│   │   │   ├── state.py
│   │   │   ├── routing.py
│   │   │   ├── nodes.py
│   │   │   │
│   │   │   ├── resume_graph.py
│   │   │   ├── interview_graph.py
│   │   │   ├── github_graph.py
│   │   │   │
│   │   │   └── __init__.py
│   │   │
│   │   ├── prompts/
│   │   │   │
│   │   │   ├── orchestrator_prompt.py
│   │   │   ├── planner_prompt.py
│   │   │   ├── interviewer_prompt.py
│   │   │   ├── technical_prompt.py
│   │   │   ├── communication_prompt.py
│   │   │   ├── difficulty_prompt.py
│   │   │   ├── coach_prompt.py
│   │   │   ├── resume_prompt.py
│   │   │   ├── ats_prompt.py
│   │   │   ├── jd_prompt.py
│   │   │   └── github_prompt.py
│   │   │
│   │   ├── routes/
│   │   │   │
│   │   │   ├── auth.py
│   │   │   ├── resume.py
│   │   │   ├── github.py
│   │   │   ├── interview.py
│   │   │   ├── dashboard.py
│   │   │   └── upload.py
│   │   │
│   │   ├── services/
│   │   │   │
│   │   │   ├── llm_service.py
│   │   │   ├── pdf_service.py
│   │   │   ├── github_service.py
│   │   │   ├── speech_to_text.py
│   │   │   ├── text_to_speech.py
│   │   │   ├── embedding_service.py
│   │   │   └── storage_service.py
│   │   │
│   │   ├── models/
│   │   │   │
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── resume.py
│   │   │   ├── github.py
│   │   │   ├── interview.py
│   │   │   └── report.py
│   │   │
│   │   ├── db/
│   │   │   │
│   │   │   ├── session.py
│   │   │   ├── migrations/
│   │   │   └── __init__.py
│   │   │
│   │   ├── utils/
│   │   │   │
│   │   │   ├── logger.py
│   │   │   ├── constants.py
│   │   │   ├── exceptions.py
│   │   │   └── helpers.py
│   │   │
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── main.py
│   │
│   ├── uploads/
│   ├── tests/
│   │   ├── agents/
│   │   ├── graph/
│   │   ├── services/
│   │   └── routes/
│   │
│   ├── .env
│   ├── requirements.txt
│   └── alembic.ini
│
├── frontend/
│   │
│   ├── src/
│   │   │
│   │   ├── assets/
│   │   ├── components/
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Resume.jsx
│   │   │   ├── GitHub.jsx
│   │   │   ├── Interview.jsx
│   │   │   ├── Report.jsx
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   │
│   │   ├── hooks/
│   │   ├── context/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   └── package.json
│
└── README.md