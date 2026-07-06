import asyncio
from app.graph.graph import app as graph_app
from app.graph.state import CareerOSState

async def main():
    initial_state = CareerOSState(
        job_id="test",
        user_id="test",
        resume_pdf_path="dummy.pdf",
        jd_text="test jd",
        workflow_type="resume"
    )
    try:
        async for state_update in graph_app.astream(initial_state):
            print("Finished node!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
