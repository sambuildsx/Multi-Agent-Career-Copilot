import re
from typing import List
from pydantic import BaseModel
from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, ATSResult
from app.services.llm_service import LLMService

class ProjectRelevanceResult(BaseModel):
    score: int
    explanation: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

PROJECT_RELEVANCE_PROMPT = """You are an expert ATS (Applicant Tracking System) evaluator. 
Given the technologies required for the job and the candidate's projects, evaluate the relevance of their projects to the job.
Provide a score from 0 to 100, an explanation for the score, and list any strengths, weaknesses, and recommendations.
"""

class ATSAgent(BaseAgent):
    def __init__(self):
        self.llm_service = LLMService()

    def run(self, state: CareerOSState) -> dict:
        try:
            resume = state.resume_data
            jd = state.jd_data

            if not resume or not jd:
                raise ValueError("Both Resume and JD data are required for ATS evaluation.")

            explanations = {}

            # 1. Keyword Match
            resume_keywords = set([k.lower() for k in resume.skills + resume.extracted_technologies])
            jd_keywords = set([k.lower() for k in jd.important_keywords])
            if jd_keywords:
                matched_keywords = resume_keywords.intersection(jd_keywords)
                keyword_match_score = int((len(matched_keywords) / len(jd_keywords)) * 100)
            else:
                keyword_match_score = 100
            explanations["keyword_match"] = f"Matched {len(resume_keywords.intersection(jd_keywords))} out of {len(jd_keywords)} important keywords."

            # 2. Required Skills Match
            jd_req_skills = set([s.lower() for s in jd.required_skills])
            if jd_req_skills:
                matched_req = resume_keywords.intersection(jd_req_skills)
                required_skills_match = int((len(matched_req) / len(jd_req_skills)) * 100)
                missing_req = list(jd_req_skills - matched_req)
            else:
                required_skills_match = 100
                missing_req = []
            explanations["required_skills"] = f"Matched {len(resume_keywords.intersection(jd_req_skills))} out of {len(jd_req_skills)} required skills."

            # 3. Preferred Skills Match
            jd_pref_skills = set([s.lower() for s in jd.preferred_skills])
            if jd_pref_skills:
                matched_pref = resume_keywords.intersection(jd_pref_skills)
                preferred_skills_match = int((len(matched_pref) / len(jd_pref_skills)) * 100)
            else:
                preferred_skills_match = 100
            explanations["preferred_skills"] = f"Matched {len(resume_keywords.intersection(jd_pref_skills))} out of {len(jd_pref_skills)} preferred skills."

            # 4. Completeness Score
            completeness = 0
            if resume.education: completeness += 25
            if resume.experience: completeness += 25
            if resume.projects: completeness += 25
            if resume.skills: completeness += 25
            completeness_score = completeness
            explanations["completeness"] = f"Resume section completeness is {completeness}%."

            # 5. Project Relevance (LLM Call)
            project_text = ""
            for p in resume.projects:
                project_text += f"Project: {p.get('name', 'Unknown')}\nStack: {p.get('stack', [])}\nBullets:\n"
                for b in p.get('bullets', []):
                    project_text += f"- {b}\n"
            
            llm_input = f"Job Technologies: {', '.join(jd.technologies)}\n\nCandidate Projects:\n{project_text}"
            
            relevance_result = self.llm_service.extract_structured_data(
                text=llm_input,
                schema=ProjectRelevanceResult,
                system_prompt=PROJECT_RELEVANCE_PROMPT
            )
            project_relevance_score = min(100, max(0, relevance_result.score))
            explanations["project_relevance"] = relevance_result.explanation

            # 6 & 7. Action Verb and Quantification Scores
            all_bullets = []
            for exp in resume.experience:
                all_bullets.extend(exp.get("bullets", []))
            for proj in resume.projects:
                all_bullets.extend(proj.get("bullets", []))

            ACTION_VERBS = {"achieved", "built", "optimized", "reduced", "improved", "developed", 
                            "managed", "led", "created", "designed", "implemented", "increased", 
                            "decreased", "spearheaded", "delivered"}

            action_verb_hits = 0
            quantification_hits = 0

            for bullet in all_bullets:
                words = set(re.findall(r'\w+', bullet.lower()))
                if any(verb in words for verb in ACTION_VERBS):
                    action_verb_hits += 1
                
                if bool(re.search(r'\d+', bullet)) or bool(re.search(r'one|two|three|four|five|six|seven|eight|nine|ten|percent|%', bullet.lower())):
                    quantification_hits += 1

            total_bullets = len(all_bullets) if all_bullets else 1
            action_verb_score = int((action_verb_hits / total_bullets) * 100)
            quantification_score = int((quantification_hits / total_bullets) * 100)
            explanations["action_verb"] = f"{action_verb_hits} out of {total_bullets} bullets contain strong action verbs."
            explanations["quantification"] = f"{quantification_hits} out of {total_bullets} bullets include metrics or quantification."

            # Calculate Final Overall Score
            overall_score = int(
                (keyword_match_score * 0.25) +
                (required_skills_match * 0.30) +
                (preferred_skills_match * 0.10) +
                (completeness_score * 0.10) +
                (project_relevance_score * 0.15) +
                (action_verb_score * 0.05) +
                (quantification_score * 0.05)
            )
            explanations["overall"] = "Weighted average of all ATS sub-scores."

            ats_result = ATSResult(
                overall_score=overall_score,
                keyword_match_score=keyword_match_score,
                required_skills_match=required_skills_match,
                preferred_skills_match=preferred_skills_match,
                completeness_score=completeness_score,
                project_relevance_score=project_relevance_score,
                action_verb_score=action_verb_score,
                quantification_score=quantification_score,
                strengths=relevance_result.strengths,
                weaknesses=relevance_result.weaknesses,
                missing_skills=missing_req,
                recommendations=relevance_result.recommendations,
                score_explanations=explanations
            )

            return {
                "ats_result": ats_result,
                "completed_agents": ["ats"]
            }
        except Exception as e:
            return {
                "errors": [f"ATSAgent failed: {str(e)}"],
                "completed_agents": ["ats"]
            }
