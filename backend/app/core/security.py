"""Shared authentication dependency.

Consolidates the JWT decode logic that was previously duplicated verbatim
across routes/analyze.py and routes/interview.py (both files had a NOTE
flagging the duplication). Import get_current_user_id from here instead of
re-implementing it in each router module.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config import settings

logger = logging.getLogger("uvicorn")

security = HTTPBearer()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Decode the JWT from the Authorization header and return the user ID.
    Raises 401 if the token is missing, malformed, or expired."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
            )
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JWT decode failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {type(e).__name__}",
        )
