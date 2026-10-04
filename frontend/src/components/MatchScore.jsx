import {
  Target,
  TrendingUp
} from "lucide-react";


export default function MatchScore({
  score
}) {

  const safeScore = Math.max(
    0,
    Math.min(
      100,
      Number(score || 0)
    )
  );


  const circumference = 2 * Math.PI * 52;

  const offset =
    circumference -
    (safeScore / 100) *
      circumference;


  const getLabel = () => {

    if (safeScore >= 90) {
      return "Excellent Match";
    }

    if (safeScore >= 80) {
      return "Strong Match";
    }

    if (safeScore >= 70) {
      return "Good Match";
    }

    if (safeScore >= 50) {
      return "Moderate Match";
    }

    return "Low Match";
  };


  return (
    <div className="score-card">

      <div className="score-top">

        <div>

          <span className="eyebrow">
            AI ASSESSMENT
          </span>

          <h2>
            Overall Match
          </h2>

          <p>
            Resume compatibility with
            the selected job description.
          </p>

        </div>

        <div className="score-icon">
          <Target size={23} />
        </div>

      </div>


      <div className="score-content">

        <div className="score-ring">

          <svg
            viewBox="0 0 120 120"
          >

            <circle
              className="score-ring-bg"
              cx="60"
              cy="60"
              r="52"
            />

            <circle
              className="score-ring-progress"
              cx="60"
              cy="60"
              r="52"
              strokeDasharray={
                circumference
              }
              strokeDashoffset={
                offset
              }
            />

          </svg>

          <div className="score-number">
            <strong>
              {safeScore}%
            </strong>

            <span>
              Match
            </span>
          </div>

        </div>


        <div className="score-summary">

          <div className="match-label">
            <TrendingUp size={17} />
            {getLabel()}
          </div>

          <p>
            Based on skills, experience,
            responsibilities and job
            requirements.
          </p>

        </div>

      </div>

    </div>
  );
}