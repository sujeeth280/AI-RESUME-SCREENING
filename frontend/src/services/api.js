import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 120000
});


export async function analyzeCandidate(
  resume,
  jobDescription
) {
  const formData = new FormData();

  formData.append(
    "resume",
    resume
  );

  formData.append(
    "job_description",
    jobDescription
  );

  const response = await api.post(
    "/analyze",
    formData,
    {
      headers: {
        "Content-Type":
          "multipart/form-data"
      }
    }
  );

  return response.data;
}


export async function getCandidates() {
  const response = await api.get(
    "/candidates"
  );

  return response.data;
}


export async function getCandidate(
  candidateId
) {
  const response = await api.get(
    `/candidates/${candidateId}`
  );

  return response.data;
}