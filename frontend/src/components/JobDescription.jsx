import {
  BriefcaseBusiness
} from "lucide-react";

export default function JobDescription({
  value,
  onChange
}) {

  return (
    <div className="field-card">

      <div className="field-heading">

        <div>
          <span className="eyebrow">
            STEP 02
          </span>

          <h2>Job Description</h2>

          <p>
            Add the role requirements to
            calculate the candidate match.
          </p>
        </div>

        <div className="icon-box">
          <BriefcaseBusiness size={21} />
        </div>

      </div>


      <textarea
        className="job-textarea"
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        placeholder={`Example:

QA Engineer

Experience:
2-5 years

Required Skills:
Python
Selenium
API Testing
SQL
Postman
Automation Testing

Responsibilities:
Design test cases
Execute functional tests
Automate regression testing
Report defects
Collaborate with developers`}
      />

      <div className="textarea-footer">
        <span>
          {value.length} characters
        </span>

        <span>
          Required for match scoring
        </span>
      </div>

    </div>
  );
}