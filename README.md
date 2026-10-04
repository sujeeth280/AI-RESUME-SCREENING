# ResumeAI — v2 (deterministic scoring)

## What changed and why

### 1. The score is no longer LLM-generated
**Before:** `ai_service.py` asked Gemini to output `overall_match` directly as
part of its JSON response. Same resume + same JD could produce different
scores across runs because the model was making a subjective judgment call,
not doing arithmetic.

**Now**, the pipeline is:

```
Resume PDF
   |
extract_text_from_pdf()          <- unchanged, PyMuPDF
   |
is_resume_like()                 <- NEW: deterministic reject of non-resumes
   |
hash_text() duplicate check      <- NEW: same resume+JD -> reuse existing result
   |
extract_resume_data()  (LLM, temperature=0)   -> facts only, no score
extract_job_requirements() (LLM, temperature=0) -> facts only, no score
   |
_filter_hallucinated_skills()    <- NEW: drops any skill not found in resume text
   |
matching_engine.compute_match_score()  <- NEW: pure Python, no LLM call
   |
generate_explanation() (LLM)     <- explains the number, cannot change it
   |
Result (score + breakdown + explanation)
```

### 2. The exact formula (`backend/matching_engine.py`)

```
overall_score = round(
    0.60 * skill_score
  + 0.25 * experience_score
  + 0.15 * education_score
)
```

- `skill_score` = (matched required skills / total required skills) × 100,
  computed by normalized substring matching between the candidate's
  extracted skills and the JD's extracted required skills.
- `experience_score` = min(100, candidate_years / required_years × 100),
  years parsed with a regex from the LLM-extracted "experience" and
  "required_years" fields. 100 if the job states no minimum.
- `education_score` = 100 if candidate's education rank ≥ required rank,
  else proportional. Ranks: PhD/Doctorate=4, Master's=3, Bachelor's=2,
  Diploma/Associate=1, none=0.

None of this arithmetic touches the network. **Given the same extracted
facts, it always produces the same number** — tested with 10 identical
runs in a row, see "Tests run" below.

The one caveat worth being upfront about: the *facts themselves* still
come from an LLM call (`extract_resume_data` / `extract_job_requirements`),
now at `temperature=0` for maximum determinism, but even at temperature 0
LLM APIs aren't 100% guaranteed bit-for-bit deterministic across calls.
Duplicate detection (below) sidesteps this in practice by never re-running
the same resume+JD pair a second time.

### 3. Non-resume rejection (`backend/parser.py::is_resume_like`)
A free, instant heuristic (keyword signals + email/phone regex) that
rejects invoices, contracts, articles, etc. **before** any Gemini call is
made — so it's also a cost control. Returns `400 "Please upload a valid
resume."` on the `/api/analyze` endpoint.

### 4. Duplicate detection (`app.py`, `models.py`)
`Candidate` now has `resume_hash` and `job_hash` columns (sha256 of
normalized resume text / JD). On upload, if a row with the same pair
already exists, the endpoint returns that existing result with
`"duplicate": true` instead of re-running the LLM and creating a second
row. This directly answers "same resume uploaded twice → two records or
detect the duplicate?" — now it's detected.

This is a lightweight version of the `Candidate -> Resume Version ->
Screening History` model — enough to stop duplicate work/records without
a bigger schema migration. Promoting it to full versioned history (e.g.
same resume, different JD = new screening under the same candidate) is a
natural next step if you want it.

### 5. Hallucination guard (`ai_service.py::_filter_hallucinated_skills`)
After extraction, every `primary_skill` / `soft_skill` the model returns
is checked against the raw resume text (case-insensitive). Anything not
traceable to the actual document is dropped and reported in
`flags.dropped_hallucinated_skills` in the API response, instead of
silently feeding a possibly-invented skill into the score.

## Tests run (see conversation for full output)

| Test | Result |
|---|---|
| Same extracted resume + JD, scored 10x in a row | All 10 scores identical (70) — deterministic |
| Resume-shaped text vs. a padded invoice through `is_resume_like` | Resume → `True`, invoice → `False` |
| Skill list with one invented skill ("Kubernetes" not in resume text) | Correctly dropped, kept the 3 grounded skills |
| `hash_text()` on same content with different casing/whitespace | Identical hash both times |

These cover everything that doesn't require a live Gemini API key. The
LLM-calling functions (`extract_resume_data`, `extract_job_requirements`,
`generate_explanation`) are wired the same way as the original working
code and use the same `google-genai` client — I did not have a `GEMINI_API_KEY`
to hit the real API from this environment, so **please run one real
`/api/analyze` call on your side to confirm end-to-end**, then re-upload
the same resume+JD a second time and confirm you get `"duplicate": true`
back instead of a fresh (possibly different) score.

## What I could NOT change
Only `index.html`, `package.json`, and `vite.config.js` were uploaded for
the frontend — no `src/` folder or React components were included, so
there's no UI code to update. The API response now includes new fields
(`score_breakdown`, `matched_skills`, `explanation`, `flags`, `duplicate`)
that the frontend isn't displaying yet. If you share the `src/` folder I
can wire those into the UI.
