import re
from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, ResumeData
from app.services.resume_parser import PDFService
from app.services.llm_service import LLMService

ACTION_VERBS = {"achieved", "built", "optimized", "reduced", "improved", "developed", 
                "managed", "led", "created", "designed", "implemented", "increased", 
                "decreased", "spearheaded", "delivered"}

RESUME_PROMPT = """You are an expert technical recruiter. Extract the candidate's information from the provided resume text.
Ensure you accurately extract all skills, experiences (with detailed bullet points), education, projects, and certifications.
For technologies, extract all tools, languages, and frameworks mentioned across the resume into `extracted_technologies`.
"""

class ResumeAgent(BaseAgent):
    def __init__(self):
        self.pdf_service = PDFService()
        self.llm_service = LLMService()

    def run(self, state: CareerOSState) -> dict:
        try:
            raw_text = self.pdf_service.extract_text(state.resume_pdf_path)
            
            resume_data = self.llm_service.extract_structured_data(
                text=raw_text,
                schema=ResumeData,
                system_prompt=RESUME_PROMPT
            )
            
            resume_data.raw_text = raw_text
            
            weak_bullets = []
            
            def check_bullet(bullet: str):
                words = set(re.findall(r'\w+', bullet.lower()))
                has_action_verb = any(verb in words for verb in ACTION_VERBS)
                has_quantification = bool(re.search(r'\d+', bullet)) or bool(re.search(r'one|two|three|four|five|six|seven|eight|nine|ten|percent|%', bullet.lower()))
                
                if not has_action_verb or not has_quantification:
                    weak_bullets.append(bullet)

            for exp in resume_data.experience:
                for bullet in exp.get("bullets", []):
                    check_bullet(bullet)
                    
            for proj in resume_data.projects:
                for bullet in proj.get("bullets", []):
                    check_bullet(bullet)
            
            resume_data.weak_bullets = weak_bullets
            
            return {
                "resume_data": resume_data,
                "completed_agents": ["resume"]
            }
        except Exception as e:
            return {
                "errors": [f"ResumeAgent failed: {str(e)}"],
                "completed_agents": ["resume"]
            }
