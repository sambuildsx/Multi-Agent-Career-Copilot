import asyncio
import os
from app.db.session import engine
from app.models.base import Base
from app.routes.analyze import run_and_save_analysis
from app.models.job import AnalysisJob
from app.db.session import AsyncSessionLocal
from sqlalchemy import select

async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        job = AnalysisJob(user_id="test_user", status="pending", resume_path="test.pdf")
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id
    
    print(f"Created job {job_id}, starting analysis...")
    
    # Mock PDF extraction so ResumeAgent succeeds
    from app.services.resume_parser import PDFService
    original_extract = PDFService.extract_text
    PDFService.extract_text = lambda self, path: "Mock Resume Text with Docker and Python"
    
    try:
        await run_and_save_analysis(job_id, "test_user", "test.pdf", None)
    finally:
        PDFService.extract_text = original_extract
        
    print("Analysis finished!")
    
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
        updated_job = res.scalars().first()
        print(f"Final status: {updated_job.status}")

if __name__ == "__main__":
    asyncio.run(test_db())
