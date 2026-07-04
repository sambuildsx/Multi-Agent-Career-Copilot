from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db.session import AsyncSessionLocal, engine
from app.models.base import Base

# Import models so SQLAlchemy registers them
from app.models import job, user  # noqa: F401
from app.routes import analyze, auth, github, upload

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run application startup tasks."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Future cleanup (Redis, Celery, etc.) can go here.


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-Agent Recruiter Copilot API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(github.router)
app.include_router(upload.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"{settings.PROJECT_NAME} Backend Running 🚀",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Verify API and database availability."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        database = {
            "status": "connected"
        }

    except Exception as exc:
        database = {
            "status": "error",
            "error": type(exc).__name__,
        }

    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "database": database,
    }