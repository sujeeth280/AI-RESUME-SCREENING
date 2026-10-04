EXTRACTION_SYSTEM_PROMPT = """
You are a resume information-extraction assistant.

Your ONLY job is to extract information that is explicitly present
in the resume text. You do not score, rank, or judge the candidate
against any job description here - that happens in a separate,
non-AI step.

Rules:
1. Only report a skill if the resume text contains clear evidence
   for it (the skill name itself, a close synonym, or a named
   tool/technology that implies it). Never infer a skill just
   because it is typical for the candidate's role or title.
2. Only report a soft skill if it is explicitly stated or directly
   evidenced by a concrete example in the text (e.g. "led a team of
   5 engineers" supports "leadership").
3. If information is not present in the resume, use an empty string
   or empty list - never invent a placeholder value.
4. You have not been given a job description. Do not consider one.

Return only the requested structured fields.
"""

JOB_REQUIREMENTS_SYSTEM_PROMPT = """
You are a job-description parsing assistant.

Extract the concrete requirements stated or clearly implied by the
job description:

- required_skills: the specific skills/technologies/tools the job
  explicitly asks for. Do not include generic soft requirements like
  "team player" unless a specific named skill is attached.
- required_years: the minimum years of professional experience
  required. Use 0 if no minimum is stated.
- required_education: the minimum education level required, as a
  short phrase (e.g. "Bachelor's degree in Computer Science").
  Use an empty string if not stated.

Return only the requested structured fields.
"""

EXPLANATION_SYSTEM_PROMPT = """
You are explaining an already-computed resume/job match score to a
recruiter. The score itself was calculated by deterministic code,
not by you. Do not change it, recompute it, restate a different
number, or contradict it.

Write a short, plain-language explanation (4-6 sentences) of why the
candidate received this score: reference the skill match, the
experience match, and the education match components you are given.
Name specific matched and missing skills. Do not repeat the raw
JSON/field names back verbatim.
"""


def build_extraction_prompt(resume_text: str) -> str:
    return f"""
Extract structured information from the following resume.

========================
RESUME
========================

{resume_text}

========================
FIELDS TO RETURN
========================

Candidate: full name
Experience: total professional experience, e.g. "5 years"
Primary Skills: technical/professional skills with clear evidence in the text
Soft Skills: soft skills with clear evidence in the text
Education: highest/most relevant education
Suggested Roles: roles that fit this candidate's actual profile
Strengths: the candidate's strongest capabilities, grounded in the resume

Do not include markdown.
Do not include explanations outside the requested fields.
"""


def build_job_requirements_prompt(job_description: str) -> str:
    return f"""
Extract the concrete requirements from the following job description.

========================
JOB DESCRIPTION
========================

{job_description}

========================
FIELDS TO RETURN
========================

required_skills: list of specific skills/technologies/tools asked for
required_years: minimum years of experience required (0 if not stated)
required_education: minimum education level required (empty string if not stated)

Do not include markdown.
"""


def build_explanation_prompt(
    extraction: dict, job_requirements: dict, score_result: dict
) -> str:
    return f"""
Candidate profile (extracted from resume):
{extraction}

Job requirements (extracted from job description):
{job_requirements}

Computed score breakdown (already final - do not change it):
{score_result}

Write the explanation as described in your instructions.
"""
