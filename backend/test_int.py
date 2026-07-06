import asyncio
from app.graph.interview_graph import interview_graph as int_app
from app.graph.state import CareerOSState

async def test_int():
    s = CareerOSState(job_id="x", user_id="x", user_goal="engineer", workflow_type="interview")
    try:
        async for _ in int_app.astream(s):
            print("Int node done")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_int())
