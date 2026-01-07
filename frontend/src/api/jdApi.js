import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
});

export const createJD = (fields) =>
  API.post("/jd/create", { fields });

export const approveJD = (jdId) =>
  API.post(`/jd/${jdId}/approve`);

export const rejectJD = (jdId, reason) =>
  API.post(`/jd/${jdId}/reject`, { reason });

export const regenerateJD = (jdId) =>
  API.post(`/jd/${jdId}/regenerate`);

export const extractFromText = (text) =>
  API.post("/jd/extract/text", null, { params: { text } });

export const extractFromFile = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return API.post("/jd/extract/file", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getTemplates = () =>
  API.get("/jd/templates");

export const listJDs = () =>
  API.get("/jd/list");

export const getJD = (jdId) =>
  API.get(`/jd/${jdId}`);

export const updateJDText = (jdId, jdText) =>
  API.post(`/jd/${jdId}/update-text`, { jd_text: jdText });

export const rankResumes = (jdId, driveUrl) =>
  API.post("/jd/rank-resumes", { jd_id: jdId, drive_folder_url: driveUrl });
