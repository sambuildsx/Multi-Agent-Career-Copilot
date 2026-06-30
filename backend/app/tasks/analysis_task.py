import asyncio
from celery_worker import celery_app
from app.graph.graph import app as graph_app
from app.graph.state import CareerOSState

@celery_app.task(bind=True)
def run_analysis_job(self, job_id: str, user_id: str, resume_pdf_path: str, jd_text: str, github_input: str):
    """
    Celery task that invokes the LangGraph state machine.
    """
    initial_state = CareerOSState(
        job_id=job_id,
        user_id=user_id,
        resume_pdf_path=resume_pdf_path,
        jd_text=jd_text,
        github_input=github_input
    )
    
    # We use astream to support incremental updates (which will be written to PostgreSQL in integration)
    async def run_graph():
        async for state_update in graph_app.astream(initial_state):
            # In Milestone 7 (Integration), we will parse state_update and update agent_results DB table here.
            pass
            
    asyncio.run(run_graph())
