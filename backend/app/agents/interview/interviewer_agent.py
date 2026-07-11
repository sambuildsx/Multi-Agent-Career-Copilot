from typing import List, Optional
from pydantic import BaseModel
from typing import Literal

from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, InterviewPlan, InterviewState
from app.services.llm_service import InterviewLLMService


class NextStepDecision(BaseModel):
    """Replaces what used to be two separate calls (difficulty_controller +
    interviewer) with one: decide how the interview should progress AND,
    if continuing, generate the next question in the same response."""
    action: Literal["ask_question", "end_interview"]
    reasoning: str
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    is_followup: bool = False
    next_question: Optional[str] = None


PLANNER_PROMPT = """You are an expert technical interview designer. Given the candidate's
background and (optionally) a target job description, design an interview blueprint.

Only include topics with real evidence of relevance in the resume or JD — don't ask about
a technology that's absent from both. If a JD is provided, weight topic selection toward
what it emphasizes over what the resume happens to list. Keep estimated_questions realistic
for the difficulty and topic count (roughly 2-4 questions per topic).

Interview modes:
- "Generic Interview": Standard technical interview for the given role/domain with no resume or JD context.
- "Resume-Based Interview": Topics MUST probe the candidate's actual projects, specific technologies they claim, and address resume weaknesses. Directly reference project names and technologies.
- "Resume + JD Interview": PRIORITIZE ATS skill gaps (missing required skills) and role-specific skills from the JD. Also include resume project questions but weight them less heavily than the gap coverage."""

FIRST_QUESTION_PROMPT = """You are conducting a live technical interview. Given the interview
plan, ask an appropriate opening question for the first topic. Return the question, its
topic, and difficulty. is_followup must be false for an opening question.

For "Resume-Based Interview": ensure the question directly references actual projects, technologies (e.g. "Your Friend.ly project uses Socket.io. Explain how real-time communication works."), ATS gaps, or weaknesses from the candidate's profile.
For "Resume + JD Interview": prioritize questions about ATS-identified missing skills or role requirements, then weave in resume project questions."""

NEXT_STEP_PROMPT = """You are conducting a live technical interview and deciding what happens
next, given the plan and the full transcript so far (including the latest evaluated answer).

Decide ONE of:
- end_interview: if enough topics/questions have been meaningfully covered relative to the
  plan's estimated_questions, or the candidate has clearly struggled across multiple topics
  with no value in continuing.
- ask_question: otherwise. When asking:
  - Follow up on the most recent answer if it was weak, shallow, or worth probing deeper
    (up to the plan's follow_up_depth for that topic).
  - Otherwise move to whichever planned topic has had the fewest questions asked so far.
  - Adjust difficulty up if the candidate is scoring consistently high, down if consistently
    struggling.

Always populate next_question when action is ask_question.

For "Resume-Based Interview": questions must directly reference actual projects, technologies, or weaknesses from the candidate's profile.
For "Resume + JD Interview": prioritize covering ATS skill gaps (missing required skills) and role-specific JD requirements over general resume questions."""


class InterviewAgent(BaseAgent):
    """Owns the full interview flow: planning, question generation, topic
    switching, adaptive difficulty, and follow-ups. Merges what used to be
    three separate agents (PlannerAgent, InterviewerAgent,
    DifficultyController) into one, per the simplified architecture.
    Never evaluates answers — that's InterviewEvaluator's job."""

    def __init__(self):
        self.llm_service = InterviewLLMService()

    def _infer_domain_hint(self, resume_data, jd_data) -> str:
        skills = []
        if resume_data and getattr(resume_data, "skills", None):
            skills.extend([s.lower() for s in resume_data.skills])
        if jd_data and getattr(jd_data, "required_skills", None):
            skills.extend([s.lower() for s in jd_data.required_skills])
        
        skills_text = " ".join(skills)
        if any(k in skills_text for k in ["react", "angular", "vue", "frontend", "html", "css", "nextjs", "tailwind"]):
            return "Frontend"
        elif any(k in skills_text for k in ["node", "django", "spring", "backend", "sql", "postgres", "mongodb", "fastapi", "express"]):
            return "Backend"
        elif any(k in skills_text for k in ["docker", "aws", "kubernetes", "devops", "ci/cd", "terraform"]):
            return "DevOps"
        elif any(k in skills_text for k in ["machine learning", "tensorflow", "pytorch", "data science", "pandas", "numpy"]):
            return "Data Science"
        elif any(k in skills_text for k in ["android", "ios", "react native", "flutter", "mobile"]):
            return "Mobile"
        
        return "General Software Engineering"

    def _plan(self, target_role: Optional[str], resume_text: Optional[str], jd_text: Optional[str], inferred_domain: Optional[str] = None) -> InterviewPlan:
        parts = []
        if target_role:
            parts.append(f"Target role: {target_role}")
        elif inferred_domain:
            parts.append(f"Inferred Probable Domain: {inferred_domain} (Use this as context for shaping questions, but generate questions based primarily on the candidate profile)")

        if resume_text:
            parts.append(f"Candidate resume:\n{resume_text}")
        if jd_text:
            parts.append(f"Job description:\n{jd_text}")
        if not resume_text and not jd_text:
            parts.append("No resume or JD provided — design a general blueprint for this role.")
        context = "\n\n".join(parts)

        plan = self.llm_service.extract_structured_data(
            text=context, schema=InterviewPlan, system_prompt=PLANNER_PROMPT
        )
        plan.target_role = target_role or inferred_domain or "General"
        return plan

    def _first_question(self, plan: InterviewPlan) -> NextStepDecision:
        context = (
            f"Plan: topics={plan.topics}, estimated_questions={plan.estimated_questions}, "
            f"follow_up_depth={plan.follow_up_depth}, difficulty={plan.difficulty}"
        )
        return self.llm_service.extract_structured_data(
            text=context, schema=NextStepDecision, system_prompt=FIRST_QUESTION_PROMPT
        )

    def _next_step(self, interview: InterviewState) -> NextStepDecision:
        plan = interview.plan
        transcript_text = "\n\n".join(
            f"Turn {t['turn_number']} | Topic: {t['topic']} | Followup: {t['is_followup']}\n"
            f"Q: {t['question']}\nA: {t.get('answer')}\n"
            f"Technical score: {t.get('technical_score')}\nCommunication score: {t.get('communication_score')}"
            for t in interview.transcript
        )
        context = (
            f"Plan: topics={plan.topics}, estimated_questions={plan.estimated_questions}, "
            f"follow_up_depth={plan.follow_up_depth}\n"
            f"Current difficulty: {interview.current_difficulty}\n\n"
            f"Transcript so far:\n{transcript_text}"
        )
        return self.llm_service.extract_structured_data(
            text=context, schema=NextStepDecision, system_prompt=NEXT_STEP_PROMPT
        )

    def run(self, state: CareerOSState) -> dict:
        interview = state.get("interview") or InterviewState()

        # Phase 1: no plan yet — design the interview blueprint.
        if interview.plan is None:
            user_goal = state.get("user_goal", "")   # interview mode
            target_role = state.get("target_role")
            resume_data = state.get("resume_data")
            jd_text = state.get("jd_text")
            
            inferred_domain = None

            if user_goal in ("Resume-Based Interview", "Resume + JD Interview"):
                resume_review = state.get("resume_review")
                ats_result = state.get("ats_result")
                jd_data = state.get("jd_data")
                
                if not target_role:
                    inferred_domain = self._infer_domain_hint(resume_data, jd_data if user_goal == "Resume + JD Interview" else None)

                context_parts = [f"=== CANDIDATE RESUME PROFILE (Mode: {user_goal}) ==="]
                if target_role:
                    context_parts.append(f"Technical Domain: {target_role}")
                else:
                    context_parts.append(f"Inferred Probable Domain: {inferred_domain}")
                if resume_data:
                    context_parts.append(f"Skills on Resume: {', '.join(resume_data.skills)}")
                    if resume_data.projects:
                        context_parts.append("Projects:")
                        for p in resume_data.projects:
                            stack_str = ", ".join(p.get("stack", [])) if p.get("stack") else "none"
                            context_parts.append(f"  - {p.get('name')}: Stack: {stack_str}")

                if resume_review:
                    strengths = []
                    weaknesses = []
                    priority_actions = []

                    # Extract from dict or object safely
                    if isinstance(resume_review, dict):
                        strengths = [s.get("recommendation") if isinstance(s, dict) else getattr(s, "recommendation", str(s)) for s in resume_review.get("strengths", [])]
                        weaknesses = [w.get("recommendation") if isinstance(w, dict) else getattr(w, "recommendation", str(w)) for w in resume_review.get("weaknesses", [])]
                        priority_actions = [p.get("action") if isinstance(p, dict) else getattr(p, "action", str(p)) for p in resume_review.get("priority_actions", [])]
                    else:
                        strengths = [getattr(s, "recommendation", str(s)) for s in getattr(resume_review, "strengths", [])]
                        weaknesses = [getattr(w, "recommendation", str(w)) for w in getattr(resume_review, "weaknesses", [])]
                        priority_actions = [getattr(p, "action", str(p)) for p in getattr(resume_review, "priority_actions", [])]

                    if strengths:
                        context_parts.append(f"Resume Strengths: {', '.join(strengths)}")
                    if weaknesses:
                        context_parts.append(f"Resume Weaknesses/Areas to Improve: {', '.join(weaknesses)}")
                    if priority_actions:
                        context_parts.append(f"Priority Actions suggested: {', '.join(priority_actions)}")

                if ats_result:
                    matched_techs = getattr(ats_result, "matched_technologies", []) or (ats_result.model_dump().get("matched_technologies", []) if hasattr(ats_result, "model_dump") else [])
                    missing_techs = getattr(ats_result, "missing_technologies", []) or (ats_result.model_dump().get("missing_technologies", []) if hasattr(ats_result, "model_dump") else [])
                    if matched_techs:
                        context_parts.append(f"ATS Matched Skills: {', '.join(matched_techs)}")
                    if missing_techs:
                        context_parts.append(f"ATS Missing Skills/Gaps (PRIORITY for Resume+JD mode): {', '.join(missing_techs)}")

                if jd_data:
                    context_parts.append(f"Job Required Skills: {', '.join(jd_data.required_skills)}")

                if user_goal == "Resume + JD Interview":
                    context_parts.append("\n=== RESUME + JD INTERVIEW INSTRUCTIONS ===")
                    context_parts.append(
                        "PRIORITY ORDER for topic selection:\n"
                        "1. ATS gap skills (missing required skills listed above) — must cover these first.\n"
                        "2. Role-specific skills from the job description that appear in required/preferred skills.\n"
                        "3. Resume project questions for claimed technologies.\n"
                        "Questions must mention the specific technology or skill being tested."
                    )
                elif jd_text:
                    context_parts.append("\n=== JOB MATCHING INSTRUCTIONS ===")
                    context_parts.append(
                        "Design an interview plan that balances:\n"
                        "1. Resume questions targeting the candidate's actual projects, listed skills (e.g. Socket.io, LangChain, RAG), and weaknesses.\n"
                        "2. ATS gap questions focusing on missing required skills.\n"
                        "3. Role-specific engineering questions based on the job description."
                    )
                else:
                    context_parts.append("\n=== RESUME-ONLY INSTRUCTIONS ===")
                    context_parts.append(
                        "No JD was provided. Design an interview plan focusing entirely on "
                        "the candidate's resume projects, listed technologies, and weaknesses."
                    )

                resume_text = "\n".join(context_parts)
            else:
                # Generic Interview — no resume/JD context injected.
                resume_text = None

            plan = self._plan(target_role, resume_text, jd_text if user_goal == "Resume + JD Interview" else None, inferred_domain)
            new_interview = interview.model_copy(update={
                "plan": plan, "current_difficulty": plan.difficulty
            })
            return {"interview": new_interview, "completed_agents": ["interview_agent"]}

        # Phase 2: plan exists but no question asked yet — ask the opener.
        if not interview.transcript:
            decision = self._first_question(interview.plan)
            return self._apply_question(interview, decision)

        # Phase 3: last turn has been evaluated (both scores present) —
        # decide what happens next and ask (or end).
        last_turn = interview.transcript[-1]
        if last_turn.get("answer") is not None and last_turn.get("technical_score") is not None:
            decision = self._next_step(interview)
            if decision.action == "end_interview":
                new_interview = interview.model_copy(update={"interview_complete": True})
                return {"interview": new_interview, "completed_agents": ["interview_agent"]}
            return self._apply_question(interview, decision)

        # Shouldn't normally be reached — a question is pending an answer,
        # which the graph halts on before returning control here.
        return {"completed_agents": ["interview_agent"]}

    def _apply_question(self, interview: InterviewState, decision: NextStepDecision) -> dict:
        new_turn = {
            "turn_number": interview.turn_number + 1,
            "topic": decision.topic or (interview.plan.topics[0] if interview.plan.topics else "General"),
            "difficulty": decision.difficulty or interview.current_difficulty,
            "is_followup": decision.is_followup,
            "question": decision.next_question,
            "answer": None,
            "technical_score": None,
            "communication_score": None,
        }
        updates = {
            "transcript": interview.transcript + [new_turn],
            "turn_number": interview.turn_number + 1,
            "current_topic": new_turn["topic"],
            "current_question": new_turn["question"],
            "current_answer": None,
        }
        if decision.difficulty:
            updates["current_difficulty"] = decision.difficulty

        new_interview = interview.model_copy(update=updates)
        return {"interview": new_interview, "completed_agents": ["interview_agent"]}