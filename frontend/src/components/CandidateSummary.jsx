import {
  Award,
  GraduationCap,
  Briefcase,
  UserRound
} from "lucide-react";


function InfoItem({
  icon,
  label,
  value
}) {

  return (
    <div className="info-item">

      <div className="info-icon">
        {icon}
      </div>

      <div>
        <span>
          {label}
        </span>

        <strong>
          {value || "Not identified"}
        </strong>
      </div>

    </div>
  );
}


function ListSection({
  title,
  items,
  icon
}) {

  return (
    <div className="summary-list-section">

      <div className="summary-list-heading">

        {icon}

        <h3>{title}</h3>

      </div>


      <div className="summary-list">

        {(items || []).length > 0 ? (

          items.map(
            (item, index) => (

              <div
                className="summary-list-item"
                key={`${item}-${index}`}
              >
                <span className="bullet">
                  {index + 1}
                </span>

                <span>
                  {item}
                </span>
              </div>

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


export default function CandidateSummary({
  data
}) {

  return (
    <div className="candidate-card">

      <div className="candidate-header">

        <div className="candidate-avatar">
          <UserRound size={28} />
        </div>

        <div>

          <span className="eyebrow">
            CANDIDATE PROFILE
          </span>

          <h2>
            {data.candidate ||
              "Candidate"}
          </h2>

        </div>

      </div>


      <div className="candidate-info-grid">

        <InfoItem
          icon={<Briefcase size={18} />}
          label="Experience"
          value={data.experience}
        />

        <InfoItem
          icon={
            <GraduationCap size={18} />
          }
          label="Education"
          value={data.education}
        />

      </div>


      <div className="candidate-lists">

        <ListSection
          title="Suggested Roles"
          items={data.suggested_roles}
          icon={
            <Award size={18} />
          }
        />

        <ListSection
          title="Strengths"
          items={data.strengths}
          icon={
            <Award size={18} />
          }
        />

      </div>

    </div>
  );
}