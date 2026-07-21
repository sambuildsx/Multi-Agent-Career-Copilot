import os
import re
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import Any, Type, TypeVar, get_type_hints

T = TypeVar("T")


def _is_typeddict(schema: Any) -> bool:
    """Return True if *schema* is a TypedDict class (not a Pydantic model)."""
    return isinstance(schema, type) and issubclass(schema, dict) and hasattr(schema, "__annotations__")

logger = logging.getLogger("uvicorn")

from app.config import settings

class LLMService:
    def __init__(self):
        api_key = settings.GOOGLE_API_KEY
        if api_key and not api_key.startswith("YOUR_") and "AIza" in api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, api_key=api_key, temperature=0, max_retries=1, timeout=120)
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGoogleGenerativeAI: {e}. Mock LLM will be used.")
                self.llm = None
        else:
            logger.warning("GOOGLE_API_KEY is not configured or placeholder. Mock LLM will be used.")
            self.llm = None
        
    def extract_structured_data(self, text: str, schema: Type[T], system_prompt: str) -> Any:
        if self.llm is not None:
            try:
                structured_llm = self.llm.with_structured_output(schema)
                prompt = f"{system_prompt}\n\nHere is the data:\n<data>{text}</data>"
                result = structured_llm.invoke(prompt)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}. Falling back to mock data.")

        return self._generate_mock_data(schema, text)

    def _generate_mock_data(self, schema: Type[T], text: str) -> Any:
        """Return either a Pydantic model instance or a plain dict (for TypedDicts)."""
        is_td = _is_typeddict(schema)
        name = schema.__name__
        text_lower = text.lower() if text else ""

        def _build(td_flag: bool, cls: Any, **kwargs: Any) -> Any:
            """Return cls(**kwargs) for Pydantic, or kwargs dict for TypedDict."""
            return kwargs if td_flag else cls(**kwargs)
        
        if name == "ResumeData":
            all_techs = ["python", "javascript", "typescript", "golang", "rust", "react", "angular", "vue", "django", "fastapi", "docker", "kubernetes", "aws", "gcp", "postgresql", "mysql", "mongodb", "redis", "ci/cd", "git"]
            found_techs = [t.title() if len(t) > 3 else t.upper() for t in all_techs if t in text_lower]
            if not found_techs:
                found_techs = ["Python", "React", "Docker", "Git"]
                
            return schema(
                raw_text=text or "Sample Resume Text",
                skills=found_techs,
                experience=[
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Innovations Inc.",
                        "duration": "2023 - Present",
                        "bullets": [
                            "Led design and implementation of a scalable FastAPI application backend using PostgreSQL.",
                            "Optimized database queries, reducing API response time by 40%.",
                            "Built CI/CD pipelines using GitHub Actions to automate testing and deployments.",
                            "Managed a team of 4 junior developers and reviewed code changes."
                        ]
                    },
                    {
                        "title": "Software Engineer",
                        "company": "Web Solutions Corp",
                        "duration": "2021 - 2023",
                        "bullets": [
                            "Developed responsive user interfaces using React and Tailwind CSS.",
                            "Worked closely with product owners to deliver key features on time.",
                            "Integrated third-party APIs and services for payment and notifications."
                        ]
                    }
                ],
                education=[
                    {
                        "degree": "Bachelor of Science in Computer Science",
                        "institution": "State University",
                        "year": "2021"
                    }
                ],
                projects=[
                    {
                        "name": "E-commerce Platform",
                        "stack": ["React", "Node.js", "MongoDB"],
                        "bullets": [
                            "Built a fully functional checkout flow with Stripe integration.",
                            "Implemented JWT authentication and role-based route protection."
                        ],
                        "has_metrics": True
                    },
                    {
                        "name": "DevOps Starter Kit",
                        "stack": ["Docker", "Terraform", "AWS"],
                        "bullets": [
                            "Created infrastructure templates for rapid application deployment."
                        ],
                        "has_metrics": False
                    }
                ],
                certifications=["AWS Certified Solutions Architect", "Docker Certified Associate"],
                weak_bullets=["Worked closely with product owners to deliver key features on time.", "Created infrastructure templates for rapid application deployment."],
                extracted_technologies=found_techs
            )
            
        elif name == "JDData":
            all_techs = ["python", "javascript", "typescript", "golang", "rust", "react", "angular", "vue", "django", "fastapi", "docker", "kubernetes", "aws", "gcp", "postgresql", "mysql", "mongodb", "redis", "ci/cd", "git"]
            found_techs = [t.title() if len(t) > 3 else t.upper() for t in all_techs if t in text_lower]
            if not found_techs:
                found_techs = ["Python", "FastAPI", "Docker", "AWS"]
                
            return schema(
                raw_text=text or "Sample Job Description",
                required_skills=found_techs[:3] if len(found_techs) >= 3 else found_techs,
                preferred_skills=found_techs[3:] if len(found_techs) > 3 else ["Kubernetes"],
                responsibilities=[
                    "Build and maintain robust backend APIs and microservices.",
                    "Deploy applications in cloud environments (AWS/GCP).",
                    "Ensure high performance, scalability, and security of services."
                ],
                technologies=found_techs,
                experience_level="Mid-Senior Level",
                important_keywords=found_techs
            )
            
        elif name == "ProjectRelevanceExplanation":
            return schema(
                explanation="The candidate's project portfolio shows strong relevance. They have deployed production-ready Docker containers and built web apps using modern frameworks matching the job requirements.",
                strengths=[
                    "Hands-on experience with core technologies required by the role.",
                    "Demonstrated ability to deploy containers and configure cloud environments."
                ],
                weaknesses=[
                    "Limited projects showcasing advanced Kubernetes orchestration."
                ],
                recommendations=[
                    "Deploy the DevOps Starter Kit to AWS using Terraform to showcase infrastructure-as-code."
                ]
            )

        elif name == "GeneratedQuestion":
            return schema(question=f"Can you walk me through how you'd approach a common {text} problem, and what trade-offs you'd consider?")

        elif name == "AnswerEvaluation":
            score = 65 if len(text_lower) > 50 else 40
            return schema(
                score=score,
                feedback="Mock evaluation: the answer covers the basics but could go deeper on trade-offs and edge cases.",
                strengths=["Communicated a clear line of reasoning."],
                weaknesses=["Didn't address edge cases or scalability concerns."],
            )

        elif name == "NextStepDecision":
            return schema(
                action="ask_question",
                next_question="Let's move to a different topic — how would you design a rate limiter for a public API?",
                reasoning="Mock decision: moving on after one exchange.",
            )

        elif name == "InterviewSummary":
            return schema(
                overall_score=68,
                summary_markdown="# Interview Summary\n\nMock summary — the candidate demonstrated reasonable fundamentals with room to grow on depth and edge-case handling.",
                key_strengths=["Clear communication", "Solid grasp of fundamentals"],
                key_areas_to_improve=["Depth on trade-offs", "Edge case handling"],
            )

        elif name == "InterviewPlan":
            return schema(
                target_role="Software Engineer",
                domain="backend",
                difficulty="medium",
                topics=["System Design", "Data Structures", "API Design"],
                estimated_questions=6,
                follow_up_depth=2,
            )

        elif name == "QuestionDecision":
            return schema(
                question="Can you explain how you would design a URL shortening service and what trade-offs you'd consider?",
                topic="System Design",
                difficulty="medium",
                is_followup=False,
            )

        elif name == "TechnicalEvaluation":
            score = 65 if len(text_lower) > 80 else 45
            return schema(
                score=score,
                strengths=["Demonstrated understanding of core concepts."],
                weaknesses=["Could elaborate more on edge cases and failure modes."],
                feedback="The answer shows a reasonable grasp of fundamentals but lacks depth on scalability trade-offs.",
            )

        elif name == "CommunicationEvaluation":
            return schema(
                confidence=70,
                clarity=72,
                grammar=85,
                professionalism=80,
                feedback="Communication was clear and professional. Could improve confidence when discussing unfamiliar topics.",
            )

        elif name == "ResumeReviewLLMOutput":
            return schema(
                section_scores={
                    "experience": 85,
                    "education": 90,
                    "projects": 80,
                    "skills": 85,
                    "formatting": 80,
                    "ats_readiness": 85,
                    "overall_impact": 85,
                },
                resume_heatmap={
                    "Experience": "Excellent",
                    "Projects": "Good",
                    "Skills": "Excellent",
                    "Education": "Excellent",
                    "Formatting": "Good",
                },
                strengths=[
                    {
                        "recommendation": "Strong technical skills listed",
                        "why": "Clear languages/frameworks section",
                        "impact": "Improves keyword indexing score",
                        "improved_version": "Group by category: Languages, Frameworks, Developer Tools"
                    },
                    {
                        "recommendation": "Well-structured experience section",
                        "why": "Chronological order is clear",
                        "impact": "Easier for recruiters to read",
                        "improved_version": None
                    }
                ],
                weaknesses=[
                    {
                        "recommendation": "Bullets lack quantification",
                        "why": "No metrics or percentages shown",
                        "impact": "Makes achievements feel less tangible",
                        "improved_version": "Change 'Worked on a FastAPI app' to 'Led FastAPI backend development, improving response time by 40%'"
                    },
                    {
                        "recommendation": "Missing deployment links for projects",
                        "why": "No live links or GitHub repos",
                        "impact": "Recruiters cannot verify your work",
                        "improved_version": "Add clickable URLs next to project titles"
                    }
                ],
                rewritten_bullets=[
                    {
                        "original": "Worked closely with product owners to deliver key features on time.",
                        "rewritten": "Collaborated with product owners to deliver 5 core features, reducing launch time by 15%.",
                        "why": "Added quantification and active verb",
                        "impact": "Demonstrates clear business impact and efficiency"
                    },
                    {
                        "original": "Created infrastructure templates for rapid application deployment.",
                        "rewritten": "Developed Terraform templates for AWS, accelerating container deployment speed by 25%.",
                        "why": "Specified technologies and measurable impact",
                        "impact": "Showcases cloud infrastructure proficiency"
                    }
                ],
                project_reviews=[
                    {
                        "project_name": "E-commerce Platform",
                        "review": "Excellent full-stack integration with payment gateways.",
                        "score": 85,
                        "strengths": ["Payment integration", "Database structure"],
                        "weaknesses": ["Lack of automated test suites", "No CI/CD pipeline documentation"],
                        "improved_description": "Designed a React/Node.js e-commerce app with Stripe checkout, handling 1k+ mock transactions.",
                        "expected_ATS_improvement": "+10 points"
                    },
                    {
                        "project_name": "DevOps Starter Kit",
                        "review": "A clean infrastructure-as-code repository showcasing Docker practices.",
                        "score": 78,
                        "strengths": ["Clear Docker files", "Readable setup instructions"],
                        "weaknesses": ["No multi-stage builds used", "Missing security scanning tools"],
                        "improved_description": "Engineered Docker container templates using multi-stage builds, reducing image sizes by 40%.",
                        "expected_ATS_improvement": "+8 points"
                    }
                ],
                priority_actions=[
                    {
                        "action": "Quantify resume bullet points",
                        "priority": "High",
                        "estimated_time": "30 mins",
                        "estimated_ATS_gain": "+15 points",
                        "difficulty": "Medium",
                        "reason": "Increases recruiters' trust in achievements"
                    },
                    {
                        "action": "Add live project links",
                        "priority": "Medium",
                        "estimated_time": "10 mins",
                        "estimated_ATS_gain": "+5 points",
                        "difficulty": "Easy",
                        "reason": "Allows quick verification of skills"
                    }
                ]
            )

        elif name == "CareerReport":
            resume_score = 75
            ats_score = None
            
            rs_match = re.search(r"Overall Resume Score:\s*(\d+)", text, re.IGNORECASE)
            if rs_match:
                resume_score = int(rs_match.group(1))
                
            ats_match = re.search(r"overall ats score:\s*(\d+)", text, re.IGNORECASE)
            if ats_match:
                ats_score = int(ats_match.group(1))
                
            overall_score = ats_score if ats_score is not None else resume_score
            
            # Extract recommendations/strengths/weaknesses from context
            strengths = []
            weaknesses = []
            recommendations = []
            
            in_strengths = False
            in_weaknesses = False
            for line in text.split("\n"):
                line_stripped = line.strip()
                if "resume strengths:" in line_stripped.lower() or "ats strengths:" in line_stripped.lower():
                    in_strengths = True
                    in_weaknesses = False
                    continue
                elif "resume weaknesses:" in line_stripped.lower() or "ats weaknesses:" in line_stripped.lower():
                    in_strengths = False
                    in_weaknesses = True
                    continue
                elif line_stripped.startswith("===") or "project reviews:" in line_stripped.lower() or "priority actions:" in line_stripped.lower() or "ats recommendations:" in line_stripped.lower():
                    in_strengths = False
                    in_weaknesses = False
                    
                if in_strengths and line_stripped.startswith("- Recommendation:"):
                    rec = line_stripped.replace("- Recommendation:", "").strip()
                    if rec:
                        strengths.append(rec)
                        recommendations.append(f"Strength: {rec}")
                elif in_weaknesses and line_stripped.startswith("- Recommendation:"):
                    rec = line_stripped.replace("- Recommendation:", "").strip()
                    if rec:
                        weaknesses.append(rec)
                        recommendations.append(f"Improvement: {rec}")
                        
            if not strengths:
                strengths = ["Strong technical foundations in candidate profile.", "Good project representation."]
            if not weaknesses:
                weaknesses = ["Bullet points lack metric-driven impact description.", "Missing live deployment references."]
            if not recommendations:
                recommendations = [
                    "Add quantifiable metrics to existing bullets (e.g. latency, speed improvements).",
                    "Add GitHub repository links and live URLs to verify projects."
                ]
                
            markdown = f"# Career Assessment Report\n\n## Overview\nThe candidate shows a solid foundation. The calculated overall score is **{overall_score}/100**.\n\n"
            markdown += "## Key Strengths\n" + "\n".join(f"- {s}" for s in strengths) + "\n\n"
            markdown += "## Areas to Improve\n" + "\n".join(f"- {w}" for w in weaknesses)
            
            return _build(
                is_td, schema,
                resume_score=resume_score,
                ats_score=ats_score,
                overall_score=overall_score,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                learning_roadmap=[
                    "Week 1-2: Quantify achievements with metrics.",
                    "Week 3-4: Build deployment scripts and host projects."
                ],
                markdown=markdown,
                recommendation_cards=[
                    {
                        "current": "Bullet points describe tasks without measurable outcomes.",
                        "better": "Add a specific metric to each bullet (e.g., 'reduced API latency by 35%').",
                        "impact": "Quantified bullets increase recruiter confidence",
                    },
                    {
                        "current": "Projects list stack but no live URLs or GitHub links.",
                        "better": "Add a GitHub repo link and, where possible, a live demo URL to each project.",
                        "impact": "Verifiable work dramatically improves shortlist rate",
                    },
                    {
                        "current": "Skills section lists technologies without grouping.",
                        "better": "Group skills by category: Languages | Frameworks | Developer Tools | Cloud.",
                        "impact": "Structured skills section passes ATS parsing faster",
                    },
                ],
            )

        elif name == "DifficultyDecision":
            return schema(
                action="change_topic",
                reasoning="Mock decision: the current topic has been covered with 2 questions. Moving to the next planned topic.",
                suggested_difficulty="medium",
                suggested_topic=None,
            )

        elif name == "OrchestratorDecision":
            # The orchestrator uses dynamically created schemas that share this
            # class name. The mock just picks the first agent that looks reasonable.
            if "interview" in text_lower or "plan" in text_lower:
                if "interview_plan_present=false" in text_lower:
                    return schema(next_agent="interview_agent", reason="Mock: generating plan.")
                return schema(next_agent="interview_agent", reason="Mock: continuing interview flow.")
            return schema(next_agent="career_coach", reason="Mock: defaulting to career coach for report generation.")

        try:
            return schema()
        except Exception:
            return None


class InterviewLLMService(LLMService):
    """LLM service for interview agents — uses Groq when INTERVIEW_PROVIDER=groq,
    otherwise falls back to the parent Gemini LLM. Inherits _generate_mock_data
    from the base class so both code paths share the same fallback logic."""

    def __init__(self):
        # Do not call super().__init__() to avoid instantiating Gemini
        self.llm = None
        provider = "groq"
        model_name = getattr(settings, "INTERVIEW_MODEL", "llama-3.3-70b-versatile")

        logger.info(f"[INTERVIEW] Provider: {provider}")
        logger.info(f"[INTERVIEW] Model: {model_name}")

        self.interview_llm = None

        groq_api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured for the interview flow.")

        try:
            from langchain_groq import ChatGroq
            self.interview_llm = ChatGroq(
                model_name=model_name,
                groq_api_key=groq_api_key,
                temperature=0,
                max_retries=1,
                timeout=120,
            )
            logger.info(f"Initialized ChatGroq with model {model_name}")
        except Exception as e:
            logger.exception("Failed to initialize ChatGroq")
            raise

    def extract_structured_data(self, text: str, schema: Type[T], system_prompt: str) -> Any:
        if self.interview_llm is not None:
            try:
                structured_llm = self.interview_llm.with_structured_output(schema)
                prompt = f"{system_prompt}\n\nHere is the data:\n<data>{text}</data>"
                result = structured_llm.invoke(prompt)
                if result:
                    return result
            except Exception as e:
                logger.exception("Groq API call failed — using friendly fallback")
                fallback = self._generate_friendly_fallback(schema)
                if fallback is not None:
                    return fallback
                raise

        raise ValueError("Interview LLM is not initialized.")

    def _generate_friendly_fallback(self, schema: Type[T]) -> Any:
        name = schema.__name__
        if name == "NextStepDecision":
            return schema(
                action="ask_question",
                reasoning="Fallback due to LLM error.",
                topic="General",
                difficulty="medium",
                is_followup=False,
                next_question="I'm having a little trouble connecting right now, but let's keep going. Could you tell me more about your recent projects and the technical challenges you faced?"
            )
        elif name == "InterviewEvaluationResult":
            return schema(
                technical={
                    "score": 75,
                    "strengths": ["Clear response."],
                    "weaknesses": [],
                    "feedback": "Thanks for sharing that. My network connection is a bit unstable, but that sounds like a solid approach."
                },
                communication={
                    "confidence": 80,
                    "clarity": 80,
                    "grammar": 80,
                    "professionalism": 80,
                    "feedback": "Clear communication."
                }
            )
        return self._generate_mock_data(schema, "")