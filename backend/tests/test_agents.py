import pytest
from unittest.mock import patch, MagicMock
from app.agents.resume_agent import ResumeAgent
from app.agents.jd_agent import JDAgent
from app.graph.state import CareerOSState, ResumeData, JDData

def test_resume_agent_post_processing():
    agent = ResumeAgent()
    
    agent.pdf_service.extract_text = MagicMock(return_value="Mock PDF content")
    
    mock_llm_data = ResumeData(
        raw_text="",
        skills=["Python"],
        experience=[{"title": "Dev", "company": "Tech", "duration": "1 yr", "bullets": ["Built a fast api service", "Did some stuff"]}],
        education=[],
        projects=[],
        certifications=[],
        weak_bullets=[],
        extracted_technologies=["Python"]
    )
    agent.llm_service.extract_structured_data = MagicMock(return_value=mock_llm_data)
    
    state = CareerOSState(job_id="1", user_id="1", resume_pdf_path="dummy.pdf", jd_text="", github_input="")
    
    result = agent.run(state)
    resume_data = result["resume_data"]
    
    # "Did some stuff" has no action verb from our list and no numbers
    assert len(resume_data.weak_bullets) == 1
    assert "Did some stuff" in resume_data.weak_bullets
    assert resume_data.raw_text == "Mock PDF content"
    assert "Built a fast api service" not in resume_data.weak_bullets # Has 'Built'

def test_jd_agent_regex_fallback():
    agent = JDAgent()
    
    mock_llm_data = JDData(
        raw_text="",
        required_skills=["Python"],
        preferred_skills=[],
        responsibilities=[],
        technologies=["Python"], # Missing Docker and AWS which are in text
        experience_level="Mid",
        important_keywords=[]
    )
    agent.llm_service.extract_structured_data = MagicMock(return_value=mock_llm_data)
    
    state = CareerOSState(job_id="1", user_id="1", resume_pdf_path="", jd_text="We need Python, Docker, and AWS experience.", github_input="")
    
    result = agent.run(state)
    jd_data = result["jd_data"]
    
    techs_lower = [t.lower() for t in jd_data.technologies]
    assert "docker" in techs_lower
    assert "aws" in techs_lower
