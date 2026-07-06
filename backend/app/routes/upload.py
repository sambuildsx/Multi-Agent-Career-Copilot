import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Accept a PDF resume, save it to disk, and return the stored filename.
    """
    accepted_types = (
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    if file.content_type not in accepted_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Accepted: PDF, DOC, DOCX.",
        )

    # Generate a unique filename to avoid collisions
    ext = Path(file.filename).suffix  # e.g. ".pdf"
    unique_name = f"{uuid.uuid4()}{ext}"
    save_path = UPLOAD_DIR / unique_name

    contents = await file.read()
    with open(save_path, "wb") as f:
        f.write(contents)

    return {
        "message": "File uploaded successfully",
        "filename": unique_name,
        "original_filename": file.filename,
        "size_bytes": len(contents),
        "path": str(save_path),
    }
