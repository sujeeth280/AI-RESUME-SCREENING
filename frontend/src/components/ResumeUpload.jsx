import {
  FileText,
  UploadCloud,
  X
} from "lucide-react";

export default function ResumeUpload({
  file,
  onFileChange
}) {

  function handleDrop(event) {
    event.preventDefault();

    const droppedFile =
      event.dataTransfer.files?.[0];

    if (
      droppedFile &&
      droppedFile.type === "application/pdf"
    ) {
      onFileChange(droppedFile);
    }
  }


  function handleInput(event) {

    const selectedFile =
      event.target.files?.[0];

    if (selectedFile) {
      onFileChange(selectedFile);
    }
  }


  return (
    <div className="field-card">

      <div className="field-heading">
        <div>
          <span className="eyebrow">
            STEP 01
          </span>

          <h2>Resume PDF</h2>

          <p>
            Upload the candidate's resume
            for AI screening.
          </p>
        </div>

        <div className="icon-box">
          <FileText size={21} />
        </div>
      </div>


      {!file ? (

        <label
          className="drop-zone"
          onDragOver={(event) =>
            event.preventDefault()
          }
          onDrop={handleDrop}
        >

          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleInput}
          />

          <div className="upload-icon">
            <UploadCloud size={30} />
          </div>

          <strong>
            Drop your resume here
          </strong>

          <span>
            or click to browse
          </span>

          <small>
            PDF only · Maximum 10 MB
          </small>

        </label>

      ) : (

        <div className="selected-file">

          <div className="selected-file-icon">
            <FileText size={22} />
          </div>

          <div className="selected-file-info">
            <strong>
              {file.name}
            </strong>

            <span>
              {(file.size / 1024 / 1024).toFixed(2)}
              {" "}MB
            </span>
          </div>

          <button
            type="button"
            className="icon-button"
            onClick={() =>
              onFileChange(null)
            }
          >
            <X size={18} />
          </button>

        </div>

      )}

    </div>
  );
}