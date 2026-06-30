from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import upload, github, auth, analyze

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(github.router)
app.include_router(upload.router)


@app.on_event("startup")
async def startup_event():
    from app.db.session import engine
    from app.models.base import Base
    from app.models.user import User
    from app.models.job import AnalysisJob, AgentResult, FinalReport
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/", tags=["root"])
async def root():
    return {
        "message": "CareerOS Backend Running 🚀",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
async def health_check():
    from sqlalchemy import text
    from app.db.session import AsyncSessionLocal
    db_status = "unknown"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except BaseException as exc:
        db_status = f"error: {type(exc).__name__}: {str(exc)[:120]}"

    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "database": db_status,
    }