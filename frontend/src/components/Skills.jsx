import {
  CheckCircle2,
  Sparkles,
  XCircle
} from "lucide-react";


function SkillGroup({
  title,
  items = [],
  type = "normal"
}) {

  return (
    <div className="result-section">

      <div className="result-section-title">

        {type === "missing" ? (
          <XCircle size={18} />
        ) : (
          <CheckCircle2 size={18} />
        )}

        <span>{title}</span>

      </div>


      <div className="chip-list">

        {items.length > 0 ? (

          items.map(
            (item, index) => (

              <span
                key={`${item}-${index}`}
                className={
                  type === "missing"
                    ? "skill-chip missing"
                    : "skill-chip"
                }
              >
                {item}
              </span>

            )
          )

        ) : (

          <span className="empty-result">
            None identified
          </span>

        )}

      </div>

    </div>
  );
}


export default function Skills({
  primarySkills,
  softSkills,
  missingSkills
}) {

  return (
    <div className="skills-grid">

      <div className="skills-card">

        <div className="skills-card-header">

          <div className="icon-box">
            <Sparkles size={19} />
          </div>

          <div>
            <h3>Skills</h3>

            <p>
              Core capabilities identified
              from the resume
            </p>
          </div>

        </div>


        <SkillGroup
          title="Primary Skills"
          items={primarySkills}
        />

        <SkillGroup
          title="Soft Skills"
          items={softSkills}
        />

      </div>


      <div className="skills-card missing-card">

        <div className="skills-card-header">

          <div className="icon-box warning">
            <XCircle size={19} />
          </div>

          <div>
            <h3>Missing Skills</h3>

            <p>
              Important job requirements
              not clearly demonstrated
            </p>
          </div>

        </div>


        <SkillGroup
          title="Skill Gaps"
          items={missingSkills}
          type="missing"
        />

      </div>

    </div>
  );
}