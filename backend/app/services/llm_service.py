import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import Type, TypeVar

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger("uvicorn")

class LLMService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key and not api_key.startswith("YOUR_") and "AIza" in api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", api_key=api_key, temperature=0)
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGoogleGenerativeAI: {e}. Mock LLM will be used.")
                self.llm = None
        else:
            logger.warning("GOOGLE_API_KEY is not configured or placeholder. Mock LLM will be used.")
            self.llm = None
        
    def extract_structured_data(self, text: str, schema: Type[T], system_prompt: str) -> T:
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

    def _generate_mock_data(self, schema: Type[T], text: str) -> T:
        name = schema.__name__
        text_lower = text.lower() if text else ""
        
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
            
        elif name == "ProjectRelevanceResult":
            score = 80
            if "docker" in text_lower or "aws" in text_lower:
                score += 5
            if "react" in text_lower:
                score += 5
            score = min(95, score)
            
            return schema(
                score=score,
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
                action="new_topic",
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

        try:
            return schema()
        except Exception:
            return None