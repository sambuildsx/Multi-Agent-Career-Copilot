"""GET /jobs/{job_id}

Reads AgentResult rows from the DB (no agents or LangGraph nodes triggered),
infers a target role using deterministic skill-to-role mapping,
and returns matching job listings from the Adzuna API.

Search strategy:
  1. First call: "{role} [Intern]" (full query, no skills appended — Adzuna treats
     space-separated words as strict AND, so extra skills kill results).
  2. If 0 results: retry ONCE with just "{role}" as the what param.
  Maximum 2 Adzuna calls per request.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.models.optimizer import AgentResult, AnalysisJob
from app.services.job_service import infer_roles, build_search_query, top_skills_for_query, get_fallback_jobs

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/jobs", tags=["jobs"])

# ---------------------------------------------------------------------------
# In-memory cache: key → (result_dict, expiry_timestamp_seconds)
# ---------------------------------------------------------------------------
_cache: Dict[Tuple, Tuple[dict, float]] = {}
_CACHE_TTL = 15 * 60  # 15 minutes


def _cache_get(key: Tuple) -> Optional[dict]:
    entry = _cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    if entry:
        del _cache[key]  # evict stale entry
    return None


def _cache_set(key: Tuple, value: dict) -> None:
    _cache[key] = (value, time.time() + _CACHE_TTL)


# ---------------------------------------------------------------------------
# Adzuna API call — single request, returns parsed job list
# ---------------------------------------------------------------------------
async def _fetch_adzuna(
    *,
    what: str,
    country: str,
    page: int,
    results_per_page: int,
    where: Optional[str],
    remote: bool,
) -> Tuple[list, int, str]:
    """
    Fetch jobs from Adzuna. Returns (jobs_list, status_code, full_url_str).
    Raises HTTPException on non-200 only if keys are missing.
    Returns empty list on non-200 Adzuna response (so fallback can trigger).
    """
    if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "Job search is not configured. "
                "ADZUNA_APP_ID and ADZUNA_APP_KEY must be set on the server."
            ),
        )

    # Append "remote" keyword only when remote=True (Adzuna India doesn't have
    # a dedicated remote filter param, so we embed it in the keyword query).
    query = f"{what} remote" if remote else what

    params: Dict[str, Any] = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "results_per_page": min(results_per_page, 50),
        "what": query,
        "content-type": "application/json",
    }
    # Only send "where" if the caller provided a non-empty string.
    if where and where.strip():
        params["where"] = where.strip()

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

    # Build a human-readable URL string for logging (without secrets)
    safe_params = {k: v for k, v in params.items() if k not in ("app_id", "app_key")}
    logged_url = f"{url}?app_id=***&app_key=***&" + "&".join(
        f"{k}={v}" for k, v in safe_params.items()
    )

    logger.info(f"[jobs] Adzuna URL → {logged_url}")

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)

    logger.info(f"[jobs] Adzuna status_code={resp.status_code}")

    if resp.status_code != 200:
        logger.error(f"[jobs] Adzuna error body: {resp.text[:400]}")
        # Return empty list so the caller can decide to fallback or surface error.
        return [], resp.status_code, logged_url

    raw_jobs = resp.json().get("results", [])
    jobs: List[dict] = []
    for j in raw_jobs:
        desc_raw = j.get("description", "")
        desc = desc_raw[:280] + "..." if len(desc_raw) > 280 else desc_raw

        salary_min = j.get("salary_min")
        salary_max = j.get("salary_max")

        jobs.append({
            "title": j.get("title", ""),
            "company": j.get("company", {}).get("display_name", ""),
            "location": j.get("location", {}).get("display_name", ""),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "description": desc,
            "redirect_url": j.get("redirect_url", ""),
            "created": j.get("created", ""),
        })

    return jobs, resp.status_code, logged_url


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.get("/{job_id}")
async def get_jobs(
    job_id: str,
    employment_type: str = Query(default="internship", pattern="^(internship|fulltime)$"),
    remote: bool = Query(default=False),
    location: Optional[str] = Query(default=None),
    results_per_page: int = Query(default=20, ge=1, le=50),
    career_track: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    # ── 0. Log incoming request ────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("JOBS REQUEST RECEIVED")
    logger.info(f"job_id={job_id}")
    logger.info(f"employment_type={employment_type}")
    logger.info(f"location={location!r}")
    logger.info(f"remote={remote}")
    logger.info(f"career_track={career_track!r}")
    logger.info(f"page={page}")
    logger.info(f"ADZUNA_APP_ID exists={bool(settings.ADZUNA_APP_ID)}")
    logger.info(f"ADZUNA_APP_KEY exists={bool(settings.ADZUNA_APP_KEY)}")
    logger.info(f"ADZUNA_COUNTRY={settings.ADZUNA_COUNTRY!r}")
    logger.info("=" * 60)

    # ── 1. Verify job belongs to this user ────────────────────────────────
    job_row = (
        await db.execute(
            select(AnalysisJob).where(
                AnalysisJob.id == job_id,
                AnalysisJob.user_id == user_id,
            )
        )
    ).scalars().first()
    if not job_row:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    # ── 2. Load AgentResult rows (read-only, no agents triggered) ─────────
    agent_rows = (
        await db.execute(select(AgentResult).where(AgentResult.job_id == job_id))
    ).scalars().all()

    agent_map: Dict[str, Any] = {
        row.agent_name: row.result_json
        for row in agent_rows
        if row.result_json
    }

    # Extract nested resume_data (stored as {"resume_data": {...}, "resume_review": {...}})
    resume_raw = agent_map.get("resume", {})
    resume_data: Optional[dict] = (
        resume_raw.get("resume_data") if isinstance(resume_raw, dict) else None
    )
    jd_data: Optional[dict] = agent_map.get("jd")
    ats_result: Optional[dict] = agent_map.get("ats")

    logger.info(f"[jobs] resume_loaded={resume_data is not None}")
    logger.info(f"[jobs] jd_loaded={jd_data is not None}")
    logger.info(f"[jobs] ats_loaded={ats_result is not None}")

    if not resume_data:
        raise HTTPException(
            status_code=400,
            detail=(
                "Resume analysis data is missing or corrupted for this report. "
                "Please re-run the analysis before searching for jobs."
            ),
        )

    # ── 3. Role inference ──────────────────────────────────────────────────
    if career_track:
        primary_role = career_track
        secondary_roles: list[str] = []
    else:
        primary_role, secondary_roles = infer_roles(resume_data, jd_data)

    logger.info(f"[jobs] inferred_role={primary_role!r}")
    logger.info(f"[jobs] secondary_roles={secondary_roles}")

    # ── 4. Cache lookup (check AFTER role is resolved) ─────────────────────
    cache_key = (
        job_id,
        employment_type,
        career_track or primary_role,
        location,
        remote,
        page,
        results_per_page,
    )
    cached = _cache_get(cache_key)
    if cached:
        logger.info(f"[jobs] Cache HIT — job_id={job_id} role={primary_role} page={page}")
        return cached

    # ── 5. Build Adzuna query ──────────────────────────────────────────────
    # Skills are intentionally NOT appended to the query — Adzuna treats
    # each word as a strict AND, so "Backend Developer Intern FastAPI PostgreSQL"
    # returns far fewer (often zero) results than "Backend Developer Intern".
    top_skills = top_skills_for_query(resume_data, jd_data)  # capped at 3 in service
    what = build_search_query(primary_role, employment_type, top_skills)

    logger.info(f"[jobs] search_query={what!r}")
    logger.info(f"[jobs] Calling Adzuna country={settings.ADZUNA_COUNTRY!r}")

    # ── 6. Primary Adzuna call ─────────────────────────────────────────────
    try:
        jobs, status_code, api_url = await _fetch_adzuna(
            what=what,
            country=settings.ADZUNA_COUNTRY,
            page=page,
            results_per_page=results_per_page,
            where=location,
            remote=remote,
        )
    except HTTPException:
        raise  # re-raise config errors (missing API keys) as-is
    except Exception as exc:
        logger.warning(f"[jobs] Adzuna call raised {exc!r} — using demo fallback jobs")
        jobs = get_fallback_jobs()
        status_code = 0

    logger.info(f"[jobs] jobs_received={len(jobs)} (primary query)")

    # ── 7. Fallback: simpler query if 0 results ────────────────────────────
    # Max 2 Adzuna calls total. No further retries.
    if len(jobs) == 0 and status_code == 200:
        logger.warning("[jobs] Adzuna returned zero jobs — attempting fallback query.")

        # Fallback 1: just the role without "Intern" suffix
        fallback_what = primary_role.strip()
        if fallback_what != what:
            logger.info(f"[jobs] Fallback query={fallback_what!r}")
            jobs, fb_status, fb_url = await _fetch_adzuna(
                what=fallback_what,
                country=settings.ADZUNA_COUNTRY,
                page=page,
                results_per_page=results_per_page,
                where=location,
                remote=remote,
            )
            logger.info(f"[jobs] jobs_received={len(jobs)} (fallback query={fallback_what!r})")
            if len(jobs) == 0:
                logger.warning(f"[jobs] Fallback also returned zero jobs (query={fallback_what!r}).")
        else:
            logger.info("[jobs] Primary and fallback queries are identical — skipping second call.")

    elif len(jobs) == 0 and status_code != 0:
        # Non-200 on primary call (status_code == 0 means exception fallback already applied)
        logger.warning(f"[jobs] Adzuna returned zero jobs (status_code={status_code}).")
        raise HTTPException(
            status_code=502,
            detail=f"Job search API returned an error (HTTP {status_code}).",
        )

    if len(jobs) == 0:
        logger.warning("[jobs] All Adzuna queries returned zero results — using demo fallback jobs.")
        jobs = get_fallback_jobs()

    # ── 8. Compose response & store in cache ──────────────────────────────
    response = {
        "role": primary_role,
        "secondary_roles": secondary_roles,
        "employment_type": employment_type,
        "page": page,
        "results_per_page": results_per_page,
        "jobs": jobs,
    }
    _cache_set(cache_key, response)
    return response
