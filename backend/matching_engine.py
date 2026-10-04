"""
Deterministic match-scoring engine.

The LLM is used ONLY to extract structured facts (skills, years,
education level) from the resume and the job description. Every
number in the final score is then computed here, in plain Python,
so the same extracted facts always produce the same score.

    overall_score = round(
        0.60 * skill_score
        + 0.25 * experience_score
        + 0.15 * education_score
    )
"""

import re
from typing import Dict, List, Tuple

SKILL_WEIGHT = 0.60
EXPERIENCE_WEIGHT = 0.25
EDUCATION_WEIGHT = 0.15

EDUCATION_LEVELS = {
    "phd": 4,
    "doctorate": 4,
    "master": 3,
    "msc": 3,
    "m.tech": 3,
    "mtech": 3,
    "mba": 3,
    "bachelor": 2,
    "bsc": 2,
    "b.tech": 2,
    "btech": 2,
    "be ": 2,
    "bs ": 2,
    "diploma": 1,
    "associate": 1,
    "high school": 0,
    "secondary": 0,
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _extract_years(text: str) -> float:
    """Pull a numeric years-of-experience value out of free text like
    '5 years', '5+ years', '3-5 years of experience'."""
    if not text:
        return 0.0

    text = text.lower()
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*year",
        text,
    )
    if not match:
        return 0.0

    low = float(match.group(1))
    high = float(match.group(2)) if match.group(2) else low
    return (low + high) / 2


def education_rank(text: str) -> int:
    """Map free-text education (candidate's or a job requirement) to a
    comparable rank. Higher = more advanced."""
    if not text:
        return 0

    lowered = text.lower()
    best = 0
    for keyword, rank in EDUCATION_LEVELS.items():
        if keyword in lowered:
            best = max(best, rank)
    return best


def _skill_match(
    candidate_skills: List[str], required_skills: List[str]
) -> Tuple[float, List[str], List[str]]:
    if not required_skills:
        return 100.0, [], []

    normalized_candidate = [_normalize(s) for s in candidate_skills]
    matched, missing = [], []

    for req in required_skills:
        norm_req = _normalize(req)
        hit = any(
            norm_req in cand or cand in norm_req
            for cand in normalized_candidate
            if cand
        )
        (matched if hit else missing).append(req)

    score = (len(matched) / len(required_skills)) * 100
    return round(score, 2), matched, missing


def compute_match_score(extraction: dict, job_requirements: dict) -> dict:
    candidate_skills = (
        extraction.get("primary_skills", []) + extraction.get("soft_skills", [])
    )
    required_skills = job_requirements.get("required_skills", [])

    skill_score, matched_skills, missing_skills = _skill_match(
        candidate_skills, required_skills
    )

    candidate_years = _extract_years(extraction.get("experience", ""))
    required_years = job_requirements.get("required_years", 0) or 0

    if required_years <= 0:
        experience_score = 100.0
    else:
        experience_score = min(100.0, (candidate_years / required_years) * 100)

    candidate_edu_rank = education_rank(extraction.get("education", ""))
    required_edu_rank = job_requirements.get("required_education_rank", 0) or 0

    if required_edu_rank <= 0 or candidate_edu_rank >= required_edu_rank:
        education_score = 100.0
    else:
        education_score = (candidate_edu_rank / required_edu_rank) * 100

    overall_score = (
        SKILL_WEIGHT * skill_score
        + EXPERIENCE_WEIGHT * experience_score
        + EDUCATION_WEIGHT * education_score
    )
    overall_score = max(0, min(100, round(overall_score)))

    return {
        "overall_match": overall_score,
        "score_breakdown": {
            "skill_score": round(skill_score, 2),
            "experience_score": round(experience_score, 2),
            "education_score": round(education_score, 2),
            "weights": {
                "skills": SKILL_WEIGHT,
                "experience": EXPERIENCE_WEIGHT,
                "education": EDUCATION_WEIGHT,
            },
            "candidate_years_detected": candidate_years,
            "required_years": required_years,
            "candidate_education_rank": candidate_edu_rank,
            "required_education_rank": required_edu_rank,
            "formula": (
                "overall = round(0.60*skill_score + 0.25*experience_score "
                "+ 0.15*education_score)"
            ),
        },
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }
