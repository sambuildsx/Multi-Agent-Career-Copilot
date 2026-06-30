import pytest
from unittest.mock import MagicMock
from app.agents.ats_agent import ATSAgent, ProjectRelevanceResult
from app.graph.state import CareerOSState, ResumeData, JDData

def test_ats_agent_deterministic_scores():
    agent = ATSAgent()
    
    mock_llm_result = ProjectRelevanceResult(
        score=80,
        explanation="Projects use relevant tech.",
        strengths=["Good backend projects"],
        weaknesses=[],
        recommendations=["Add more frontend"]
    )
    agent.llm_service.extract_structured_data = MagicMock(return_value=mock_llm_result)
    
    resume_data = ResumeData(
        raw_text="",
        skills=["Python", "FastAPI"],
        experience=[{"title": "Dev", "company": "Acme", "duration": "1yr", "bullets": ["Built a fast api service reducing latency by 20%"]}],
        education=[{"degree": "BS CS"}],
        projects=[],
        certifications=[],
        weak_bullets=[],
        extracted_technologies=["PostgreSQL"]
    )
    
    jd_data = JDData(
        raw_text="",
        required_skills=["Python", "React"],
        preferred_skills=["Docker"],
        responsibilities=[],
        technologies=["Python", "React", "Docker"],
        experience_level="Mid",
        important_keywords=["FastAPI"]
    )
    
    state = CareerOSState(
        job_id="1", user_id="1", resume_pdf_path="", jd_text="", github_input="",
        resume_data=resume_data, jd_data=jd_data
    )
    
    result = agent.run(state)
    ats = result["ats_result"]
    
    # Keyword match: important keywords are ["FastAPI"], resume has "FastAPI". Match = 100%
    assert ats.keyword_match_score == 100
    
    # Required skills: ["Python", "React"], resume has "Python". Match = 50%
    assert ats.required_skills_match == 50
    assert "react" in [s.lower() for s in ats.missing_skills]
    
    # Preferred skills: ["Docker"], resume has 0. Match = 0%
    assert ats.preferred_skills_match == 0
    
    # Completeness: education(25) + experience(25) + skills(25) + projects(0) = 75
    assert ats.completeness_score == 75
    
    # Action verbs: "Built" is in ACTION_VERBS. 1 out of 1 bullet.
    assert ats.action_verb_score == 100
    
    # Quantification: "20%" has digits. 1 out of 1.
    assert ats.quantification_score == 100
    
    # Overall score should be calculated correctly
    # 100*.25 + 50*.3 + 0*.1 + 75*.1 + 80*.15 + 100*.05 + 100*.05 = 25 + 15 + 0 + 7.5 + 12 + 5 + 5 = 69.5 -> 69
    assert ats.overall_score == 69
