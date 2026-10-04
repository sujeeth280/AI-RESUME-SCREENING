import re
from pathlib import Path

import fitz


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF using PyMuPDF.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF not found: {file_path}"
        )

    text_parts = []

    document = fitz.open(file_path)

    try:
        for page in document:
            page_text = page.get_text("text")

            if page_text:
                text_parts.append(page_text)
    finally:
        document.close()

    extracted_text = "\n".join(text_parts)

    extracted_text = extracted_text.strip()

    if not extracted_text:
        raise ValueError(
            "No readable text was found in the PDF."
        )

    return extracted_text


RESUME_SIGNAL_KEYWORDS = [
    "experience",
    "education",
    "skills",
    "employment",
    "objective",
    "summary",
    "certification",
    "project",
    "work history",
    "career",
    "qualification",
    "internship",
    "achievements",
    "references",
]

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_PATTERN = re.compile(r"(\+?\d[\d\-\s()]{7,}\d)")


def is_resume_like(text: str, min_signal_score: int = 3) -> bool:
    """
    Deterministic, free (no LLM call) heuristic that rejects obvious
    non-resume PDFs (invoices, contracts, articles, reports, etc.)
    before the document is ever sent to the AI/matching pipeline.

    This is intentionally conservative rather than a perfect
    classifier - it looks for the structural signals essentially
    every resume has (contact info + section keywords) and rejects
    documents missing most of them.
    """

    if not text or len(text.strip()) < 100:
        return False

    lowered = text.lower()

    keyword_hits = sum(
        1 for keyword in RESUME_SIGNAL_KEYWORDS if keyword in lowered
    )

    has_email = bool(_EMAIL_PATTERN.search(text))
    has_phone = bool(_PHONE_PATTERN.search(text))

    signal_score = keyword_hits + (1 if has_email else 0) + (1 if has_phone else 0)

    return signal_score >= min_signal_score
