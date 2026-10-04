import hashlib
import json
import os
import re
from typing import List, Tuple, Type, TypeVar

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field, ValidationError

from matching_engine import compute_match_score, education_rank
from prompts import (
    EXPLANATION_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    JOB_REQUIREMENTS_SYSTEM_PROMPT,
    build_explanation_prompt,
    build_extraction_prompt,
    build_job_requirements_prompt,
)

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv("GROQ_MODEL")

if not GROQ_MODEL:
    raise RuntimeError(
        "GROQ_MODEL is missing. "
        "Add it to backend/.env"
    )


if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. "
        "Add it to backend/.env"
    )


client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# PYDANTIC RESPONSE MODELS
# ============================================================

class ResumeExtraction(BaseModel):
    candidate: str = Field(
        description="Candidate full name"
    )

    experience: str = Field(
        description="Total professional experience, e.g. '5 years'"
    )

    primary_skills: List[str] = Field(
        description=(
            "Primary technical/professional skills with "
            "clear evidence in the resume"
        )
    )

    soft_skills: List[str] = Field(
        description=(
            "Soft skills with clear evidence in the resume"
        )
    )

    education: str = Field(
        description=(
            "Candidate's highest/most relevant education"
        )
    )

    suggested_roles: List[str] = Field(
        description=(
            "Suitable job roles based on the candidate's "
            "actual profile"
        )
    )

    strengths: List[str] = Field(
        description=(
            "Candidate's strongest capabilities, "
            "grounded in the resume"
        )
    )


class JobRequirements(BaseModel):
    required_skills: List[str] = Field(
        description=(
            "Specific skills/technologies/tools the job "
            "explicitly requires"
        )
    )

    required_years: float = Field(
        default=0,
        ge=0,
        description=(
            "Minimum years of professional experience "
            "required, 0 if not stated"
        ),
    )

    required_education: str = Field(
        default="",
        description=(
            "Minimum education level required, "
            "empty string if not stated"
        ),
    )


T = TypeVar("T", bound=BaseModel)


# ============================================================
# JSON SCHEMA HINT (Groq has no native response_schema, so we
# describe the expected shape directly in the prompt and pair
# it with JSON mode)
# ============================================================

def _json_schema_hint(model: Type[BaseModel]) -> str:
    """
    Build a short instruction block describing the exact JSON
    object the model must return, derived from the Pydantic model.
    """

    schema = model.model_json_schema()

    return (
        "\n\nRespond with ONLY a single valid JSON object - no "
        "markdown code fences, no explanation before or after it. "
        "The JSON object must match this schema exactly "
        "(property names and types):\n"
        f"{json.dumps(schema, indent=2)}"
    )


# ============================================================
# GROQ CHAT COMPLETION HELPER
# ============================================================

def _chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool = False,
):
    kwargs = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    return client.chat.completions.create(**kwargs)


# ============================================================
# JSON RESPONSE CLEANER
# ============================================================

def clean_json_response(text: str) -> str:
    """
    Clean the model response before JSON parsing.

    Handles:
    - ```json ... ```
    - ``` ... ```
    - leading/trailing explanation
    - extra text around JSON
    - whitespace
    """

    if not text:
        raise ValueError(
            "Groq returned an empty response."
        )

    text = text.strip()

    # --------------------------------------------------------
    # Remove Markdown code fences
    # --------------------------------------------------------

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    # --------------------------------------------------------
    # If the response contains extra text, extract JSON object
    # --------------------------------------------------------

    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace != -1 and last_brace != -1:
        text = text[first_brace:last_brace + 1]

    return text.strip()


def parse_json_response(
    response_text: str,
    model: Type[T]
) -> T:
    """
    Safely parse Groq's structured JSON.

    First attempts:
        1. response text cleaning
        2. Pydantic JSON validation
        3. json.loads + Pydantic validation

    Provides a clear error instead of exposing:
        Unterminated string...
    """

    if not response_text:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    cleaned = clean_json_response(response_text)

    # --------------------------------------------------------
    # Attempt 1: Pydantic JSON validation
    # --------------------------------------------------------

    try:
        return model.model_validate_json(cleaned)

    except ValidationError:
        pass

    # --------------------------------------------------------
    # Attempt 2: Standard JSON parser
    # --------------------------------------------------------

    try:
        data = json.loads(cleaned)

        return model.model_validate(data)

    except json.JSONDecodeError as exc:

        preview = cleaned[:1000]

        raise RuntimeError(
            "Groq returned invalid JSON.\n\n"
            f"JSON error: {exc}\n\n"
            "Groq response preview:\n"
            f"{preview}"
        ) from exc

    except ValidationError as exc:

        raise RuntimeError(
            "Groq returned JSON, but it does not match "
            "the expected response structure.\n\n"
            f"Validation error: {exc}"
        ) from exc


# ============================================================
# HASH
# ============================================================

def hash_text(text: str) -> str:
    """
    Stable hash used for duplicate-screening detection.
    """

    normalized = " ".join(
        text.lower().split()
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


# ============================================================
# HALLUCINATION FILTER
# ============================================================

def _filter_hallucinated_skills(
    skills: List[str],
    resume_text: str
) -> Tuple[List[str], List[str]]:
    """
    Keep only skills that can be traced to the resume.
    """

    lowered_resume = resume_text.lower()

    kept = []
    dropped = []

    for skill in skills:

        skill_norm = skill.lower().strip()

        if not skill_norm:
            continue

        core_token = skill_norm.split()[0]

        if (
            skill_norm in lowered_resume
            or core_token in lowered_resume
        ):
            kept.append(skill)

        else:
            dropped.append(skill)

    return kept, dropped


# ============================================================
# RESUME EXTRACTION
# ============================================================

def extract_resume_data(
    resume_text: str
) -> dict:

    if not resume_text.strip():
        raise ValueError(
            "Resume text is empty."
        )

    prompt = build_extraction_prompt(
        resume_text
    )

    try:

        response = _chat_completion(
            system_prompt=(
                EXTRACTION_SYSTEM_PROMPT
                + _json_schema_hint(ResumeExtraction)
            ),
            user_prompt=prompt,
            temperature=0,
            max_tokens=3000,
            json_mode=True,
        )

    except Exception as exc:

        raise RuntimeError(
            f"Groq extraction request failed: {exc}"
        ) from exc

    parsed = parse_json_response(
        response.choices[0].message.content,
        ResumeExtraction
    )

    result = parsed.model_dump()

    # --------------------------------------------------------
    # Remove hallucinated primary skills
    # --------------------------------------------------------

    kept_primary, dropped_primary = (
        _filter_hallucinated_skills(
            result["primary_skills"],
            resume_text
        )
    )

    # --------------------------------------------------------
    # Remove hallucinated soft skills
    # --------------------------------------------------------

    kept_soft, dropped_soft = (
        _filter_hallucinated_skills(
            result["soft_skills"],
            resume_text
        )
    )

    result["primary_skills"] = kept_primary

    result["soft_skills"] = kept_soft

    result["_dropped_hallucinated_skills"] = (
        dropped_primary + dropped_soft
    )

    return result


# ============================================================
# JOB REQUIREMENTS EXTRACTION
# ============================================================

def extract_job_requirements(
    job_description: str
) -> dict:

    if not job_description.strip():
        raise ValueError(
            "Job description is empty."
        )

    prompt = build_job_requirements_prompt(
        job_description
    )

    try:

        response = _chat_completion(
            system_prompt=(
                JOB_REQUIREMENTS_SYSTEM_PROMPT
                + _json_schema_hint(JobRequirements)
            ),
            user_prompt=prompt,
            temperature=0,
            max_tokens=2000,
            json_mode=True,
        )

    except Exception as exc:

        raise RuntimeError(
            "Groq job-requirements request failed: "
            f"{exc}"
        ) from exc

    parsed = parse_json_response(
        response.choices[0].message.content,
        JobRequirements
    )

    result = parsed.model_dump()

    result["required_education_rank"] = (
        education_rank(
            result["required_education"]
        )
    )

    return result


# ============================================================
# EXPLANATION
# ============================================================

def generate_explanation(
    extraction: dict,
    job_requirements: dict,
    score_result: dict
) -> str:

    prompt = build_explanation_prompt(
        extraction,
        job_requirements,
        score_result
    )

    try:

        response = _chat_completion(
            system_prompt=EXPLANATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=600,
            json_mode=False,
        )

    except Exception as exc:

        raise RuntimeError(
            f"Groq explanation request failed: {exc}"
        ) from exc

    return (
        response.choices[0].message.content or ""
    ).strip()


# ============================================================
# COMPLETE RESUME ANALYSIS
# ============================================================

def analyze_resume(
    resume_text: str,
    job_description: str
) -> dict:

    if not resume_text.strip():
        raise ValueError(
            "Resume text is empty."
        )

    if not job_description.strip():
        raise ValueError(
            "Job description is empty."
        )

    # --------------------------------------------------------
    # STEP 1
    # Extract resume
    # --------------------------------------------------------

    extraction = extract_resume_data(
        resume_text
    )

    # --------------------------------------------------------
    # STEP 2
    # Extract JD requirements
    # --------------------------------------------------------

    job_requirements = extract_job_requirements(
        job_description
    )

    # --------------------------------------------------------
    # STEP 3
    # Calculate score deterministically
    # --------------------------------------------------------

    score_result = compute_match_score(
        extraction,
        job_requirements
    )

    # --------------------------------------------------------
    # STEP 4
    # Generate explanation
    # --------------------------------------------------------

    explanation = generate_explanation(
        extraction,
        job_requirements,
        score_result
    )

    # --------------------------------------------------------
    # STEP 5
    # Final result
    # --------------------------------------------------------

    result = {

        "candidate": extraction["candidate"],

        "experience": extraction["experience"],

        "primary_skills": (
            extraction["primary_skills"]
        ),

        "soft_skills": (
            extraction["soft_skills"]
        ),

        "education": extraction["education"],

        "suggested_roles": (
            extraction["suggested_roles"]
        ),

        "strengths": (
            extraction["strengths"]
        ),

        "matched_skills": (
            score_result["matched_skills"]
        ),

        "missing_skills": (
            score_result["missing_skills"]
        ),

        "overall_match": (
            score_result["overall_match"]
        ),

        "score_breakdown": (
            score_result["score_breakdown"]
        ),

        "explanation": explanation,

        "flags": {
            "dropped_hallucinated_skills": (
                extraction.get(
                    "_dropped_hallucinated_skills",
                    []
                )
            ),
        },
    }

    return result


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def match_resume_to_job(
    resume_text: str,
    job_description: str
) -> dict:

    return analyze_resume(
        resume_text,
        job_description
    )
