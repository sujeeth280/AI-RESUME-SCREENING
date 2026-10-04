import {
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Users
} from "lucide-react";

import {
  useState
} from "react";

import ResumeUpload from "./components/ResumeUpload";
import JobDescription from "./components/JobDescription";
import CandidateSummary from "./components/CandidateSummary";
import MatchScore from "./components/MatchScore";
import Skills from "./components/Skills";
import Loading from "./components/Loading";

import {
  analyzeCandidate
} from "./services/api";


export default function App() {

  const [resume, setResume] =
    useState(null);

  const [jobDescription, setJobDescription] =
    useState("");

  const [result, setResult] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  async function handleAnalyze() {

    setError("");

    if (!resume) {
      setError(
        "Please upload a PDF resume."
      );
      return;
    }

    if (!jobDescription.trim()) {
      setError(
        "Please enter a job description."
      );
      return;
    }

    setLoading(true);

    try {

      const response =
        await analyzeCandidate(
          resume,
          jobDescription
        );

      setResult(
        response.data
      );

      window.scrollTo({
        top: 0,
        behavior: "smooth"
      });

    } catch (err) {

      const message =
        err.response?.data?.detail ||
        err.message ||
        "Something went wrong.";

      setError(message);

    } finally {

      setLoading(false);

    }
  }


  function reset() {

    setResume(null);
    setJobDescription("");
    setResult(null);
    setError("");

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });
  }


  return (
    <div className="app-shell">

      <header className="topbar">

        <div className="brand">

          <div className="brand-mark">
            <BrainCircuit size={22} />
          </div>

          <div>
            <strong>
              Resume<span>AI</span>
            </strong>

            <small>
              Intelligent Resume Screening
            </small>
          </div>

        </div>


        <div className="topbar-status">
          <span className="status-dot" />
          AI Screening System
        </div>

      </header>


      <main className="main-container">

        {!result && (

          <section className="hero">

            <div className="hero-badge">
              <Sparkles size={15} />
              AI-POWERED RECRUITMENT
            </div>

            <h1>
              Screen Resumes
              <span>
                Smarter & Faster
              </span>
            </h1>

            <p>
              Upload a candidate resume and
              compare it against a job
              description to instantly identify
              skills, experience, strengths and
              job fit.
            </p>

            <div className="hero-stats">

              <div>
                <strong>10x</strong>
                <span>Faster screening</span>
              </div>

              <div>
                <strong>AI</strong>
                <span>Powered analysis</span>
              </div>

              <div>
                <strong>100%</strong>
                <span>Structured output</span>
              </div>

            </div>

          </section>

        )}


        {!result ? (

          <section className="analysis-layout">

            <div className="analysis-form">

              <ResumeUpload
                file={resume}
                onFileChange={setResume}
              />

              <JobDescription
                value={jobDescription}
                onChange={setJobDescription}
              />

              {error && (

                <div className="error-message">
                  {error}
                </div>

              )}

              {loading ? (

                <Loading />

              ) : (

                <button
                  className="analyze-button"
                  type="button"
                  onClick={handleAnalyze}
                >

                  <span>
                    Analyze Candidate
                  </span>

                  <ChevronRight size={19} />

                </button>

              )}

            </div>


            <aside className="side-panel">

              <div className="side-card">

                <div className="side-icon">
                  <ShieldCheck size={22} />
                </div>

                <h3>
                  What AI checks
                </h3>

                <div className="check-list">

                  {[
                    "Candidate details",
                    "Professional experience",
                    "Technical skills",
                    "Soft skills",
                    "Education",
                    "Suitable roles",
                    "Strengths",
                    "Missing skills",
                    "Job match score"
                  ].map(
                    (item) => (

                      <div
                        key={item}
                        className="check-item"
                      >

                        <CheckCircle2
                          size={17}
                        />

                        <span>
                          {item}
                        </span>

                      </div>

                    )
                  )}

                </div>

              </div>


              <div className="side-card mini">

                <Users size={20} />

                <div>

                  <strong>
                    Built for recruiters
                  </strong>

                  <p>
                    Turn lengthy resumes into
                    structured candidate insights
                    in seconds.
                  </p>

                </div>

              </div>

            </aside>

          </section>

        ) : (

          <section className="results-page">

            <div className="results-header">

              <div>

                <span className="eyebrow">
                  SCREENING COMPLETE
                </span>

                <h1>
                  Candidate Analysis
                </h1>

                <p>
                  AI-generated screening results
                  based on the uploaded resume
                  and target job description.
                </p>

              </div>

              <button
                className="reset-button"
                onClick={reset}
              >
                <RotateCcw size={17} />
                New Screening
              </button>

            </div>


            <div className="results-grid">

              <div className="results-main">

                <CandidateSummary
                  data={result}
                />

                <Skills
                  primarySkills={
                    result.primary_skills
                  }
                  softSkills={
                    result.soft_skills
                  }
                  missingSkills={
                    result.missing_skills
                  }
                />

              </div>


              <aside className="results-sidebar">

                <MatchScore
                  score={
                    result.overall_match
                  }
                />

              </aside>

            </div>


            <div className="output-preview">

              <div>
                <span className="eyebrow">
                  AI OUTPUT
                </span>

                <h2>
                  Recruiter-ready summary
                </h2>

              </div>

              <pre>
{`Candidate: ${result.candidate}
Experience: ${result.experience}

Primary Skills:
${(result.primary_skills || [])
  .join("\n")}

Soft Skills:
${(result.soft_skills || [])
  .join("\n")}

Education:
${result.education}

Suggested Roles:
${(result.suggested_roles || [])
  .join("\n")}

Strengths:
${(result.strengths || [])
  .join("\n")}

Missing Skills:
${(result.missing_skills || [])
  .join("\n")}

Overall Match: ${result.overall_match}%`}
              </pre>

            </div>

          </section>

        )}

      </main>


      <footer className="footer">

        <span>
          ResumeAI
        </span>

        <span>
          AI Resume Screening Platform
        </span>

      </footer>

    </div>
  );
}