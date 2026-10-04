import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ai_service import analyze_resume, hash_text
from database import get_db, init_db
from models import Candidate
from parser import extract_text_from_pdf, is_resume_like


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


MAX_FILE_SIZE_MB = int(
    os.getenv(
        "MAX_FILE_SIZE_MB",
        "10"
    )
)

MAX_FILE_SIZE = (
    MAX_FILE_SIZE_MB
    * 1024
    * 1024
)


app = FastAPI(
    title="ResumeAI",
    description="AI-powered resume screening system",
    version="2.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():

    init_db()


@app.get("/")
def root():

    return {
        "message": "ResumeAI API is running",
        "status": "ok",
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post("/api/analyze")
async def analyze_candidate(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    db: Session = Depends(get_db),
):

    if not resume.filename:
        raise HTTPException(
            status_code=400,
            detail="Resume file is required."
        )

    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    if not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description is required."
        )

    unique_id = uuid.uuid4().hex

    safe_filename = (
        f"{unique_id}_{Path(resume.filename).name}"
    )

    file_path = UPLOAD_DIR / safe_filename

    try:

        content = await resume.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File is too large. "
                    f"Maximum size is {MAX_FILE_SIZE_MB} MB."
                ),
            )

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        resume_text = extract_text_from_pdf(
            str(file_path)
        )

        if len(resume_text) < 20:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The PDF does not contain enough "
                    "readable text."
                ),
            )

        # --- Reject non-resume PDFs before any AI/matching work ---
        if not is_resume_like(resume_text):
            raise HTTPException(
                status_code=400,
                detail="Please upload a valid resume.",
            )

        # --- Duplicate detection: same resume + same JD already screened ---
        resume_hash = hash_text(resume_text)
        job_hash = hash_text(job_description)

        existing = (
            db.query(Candidate)
            .filter(
                Candidate.resume_hash == resume_hash,
                Candidate.job_hash == job_hash,
            )
            .order_by(Candidate.created_at.desc())
            .first()
        )

        if existing:

            try:
                analysis = json.loads(existing.analysis_json)
            except Exception:
                analysis = {}

            result = {
                "id": existing.id,
                "resume_filename": existing.resume_filename,
                "duplicate": True,
                **analysis,
            }

            return JSONResponse(
                content={
                    "success": True,
                    "data": result,
                }
            )

        analysis = analyze_resume(
            resume_text,
            job_description
        )

        candidate = Candidate(
            candidate_name=analysis["candidate"],
            resume_filename=resume.filename,
            job_description=job_description,
            resume_text=resume_text,
            analysis_json=json.dumps(
                analysis,
                ensure_ascii=False
            ),
            resume_hash=resume_hash,
            job_hash=job_hash,
        )

        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        result = {
            "id": candidate.id,
            "resume_filename": resume.filename,
            "duplicate": False,
            **analysis,
        }

        output_file = (
            OUTPUT_DIR
            / f"{candidate.id}_analysis.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as output:

            json.dump(
                result,
                output,
                indent=2,
                ensure_ascii=False
            )

        return JSONResponse(
            content={
                "success": True,
                "data": result,
            }
        )

    except HTTPException:
        raise

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc)
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}"
        )

    finally:

        if file_path.exists():

            try:
                file_path.unlink()

            except Exception:
                pass


@app.get("/api/candidates")
def get_candidates(
    db: Session = Depends(get_db)
):

    candidates = (
        db.query(Candidate)
        .order_by(
            Candidate.created_at.desc()
        )
        .all()
    )

    result = []

    for candidate in candidates:

        try:
            analysis = json.loads(
                candidate.analysis_json
            )

        except Exception:
            analysis = {}

        result.append(
            {
                "id": candidate.id,
                "candidate": candidate.candidate_name,
                "resume_filename": candidate.resume_filename,
                "overall_match": analysis.get(
                    "overall_match",
                    0
                ),
                "created_at": (
                    candidate.created_at.isoformat()
                    if candidate.created_at
                    else None
                ),
            }
        )

    return {
        "success": True,
        "data": result,
    }


@app.get("/api/candidates/{candidate_id}")
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):

    candidate = (
        db.query(Candidate)
        .filter(
            Candidate.id == candidate_id
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    try:

        analysis = json.loads(
            candidate.analysis_json
        )

    except Exception:

        analysis = {}

    return {
        "success": True,
        "data": {
            "id": candidate.id,
            "resume_filename": candidate.resume_filename,
            **analysis,
        },
    }
