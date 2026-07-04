import re
from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, JDData
from app.services.llm_service import LLMService

JD_PROMPT = """You are an expert technical recruiter. Extract the job requirements from the provided job description text.
Identify required skills, preferred skills, core responsibilities, and the general experience level expected.
Extract important keywords that represent core competencies.
"""

TECH_REGEX = re.compile(r'\b(python|java|javascript|typescript|c\+\+|golang|rust|react|angular|vue|node\.js|django|flask|fastapi|spring|docker|kubernetes|aws|gcp|azure|sql|postgresql|mysql|mongodb|redis|graphql|rest api|ci/cd|git|linux)\b', re.IGNORECASE)


class JDAgent(BaseAgent):
    def __init__(self):
        self.llm_service = LLMService()

    def run(self, state: CareerOSState) -> dict:
        if not state.jd_text or not state.jd_text.strip():
            return {
                "errors": ["JDAgent: called with empty jd_text — this should be filtered upstream in resume-only mode"],
                "completed_agents": ["jd"],
            }

        try:
            jd_data = self.llm_service.extract_structured_data(
                text=state.jd_text,
                schema=JDData,
                system_prompt=JD_PROMPT
            )
            jd_data.raw_text = state.jd_text

            found_techs = set(jd_data.technologies)
            found_techs_lower = {t.lower() for t in found_techs}

            matches = TECH_REGEX.findall(state.jd_text)
            for match in matches:
                if match.lower() not in found_techs_lower:
                    clean_tech = match.title() if len(match) > 3 else match.upper()
                    if clean_tech.upper() == 'CI/CD':
                        clean_tech = 'CI/CD'
                    found_techs.add(clean_tech)
                    found_techs_lower.add(match.lower())

            jd_data.technologies = list(found_techs)

            return {
                "jd_data": jd_data,
                "completed_agents": ["jd"]
            }
        except Exception as e:
            return {
                "errors": [f"JDAgent failed: {str(e)}"],
                "completed_agents": ["jd"]
            }