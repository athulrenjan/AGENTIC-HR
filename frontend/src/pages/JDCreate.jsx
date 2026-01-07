import { useState, useEffect } from "react";
import { createJD, extractFromText, extractFromFile, getTemplates, rankResumes, approveJD, updateJDText } from "../api/jdApi";

export default function JDCreate({ onJDCreate, onCandidatesFetched }) {
  const [mode, setMode] = useState("manual");
  const [templates, setTemplates] = useState({});
  const [form, setForm] = useState({
    title: "",
    level: "",
    mandatory_skills: "",
    nice_to_have_skills: "",
    location: "",
    team_size: "",
    budget: "",
    inclusion_criteria: "",
    exclusion_criteria: "",
  });
  const [pasteText, setPasteText] = useState("");
  const [uploadedFile, setUploadedFile] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filteringLoading, setFilteringLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState({});
  const [driveUrl, setDriveUrl] = useState("");
  const [previewMode, setPreviewMode] = useState(false);
  const [editedJDText, setEditedJDText] = useState("");

  useEffect(() => {
    getTemplates().then(res => setTemplates(res.data));
  }, []);

  const applyTemplate = (templateName) => {
    const template = templates[templateName];
    if (template) {
      setForm({
        ...form,
        ...template,
        mandatory_skills: template.mandatory_skills.join(", "),
        nice_to_have_skills: template.nice_to_have_skills.join(", "),
        inclusion_criteria: template.inclusion_criteria.join(", "),
        exclusion_criteria: template.exclusion_criteria.join(", "),
      });
    }
  };

  const extractFromPaste = async () => {
    if (!pasteText.trim()) return;
    setLoading(true);
    try {
      const res = await extractFromText(pasteText);
      setExtractedData(res.data);
      populateFormFromExtracted(res.data);
    } catch (error) {
      console.error("Extraction failed:", error);
    }
    setLoading(false);
  };

  const extractFromUpload = async () => {
    if (!uploadedFile) return;
    setLoading(true);
    try {
      const res = await extractFromFile(uploadedFile);
      setExtractedData(res.data);
      populateFormFromExtracted(res.data);
    } catch (error) {
      console.error("Extraction failed:", error);
    }
    setLoading(false);
  };

  const populateFormFromExtracted = (data) => {
    setForm({
      ...form,
      ...data.fields,
      mandatory_skills: data.fields.mandatory_skills.join(", "),
      nice_to_have_skills: data.fields.nice_to_have_skills.join(", "),
      inclusion_criteria: data.fields.inclusion_criteria.join(", "),
      exclusion_criteria: data.fields.exclusion_criteria.join(", "),
    });
  };

  const validateForm = () => {
    const newErrors = {};
    if (!form.title.trim()) newErrors.title = "Title is required";
    if (!form.level.trim()) newErrors.level = "Level is required";
    if (!form.mandatory_skills.trim()) newErrors.mandatory_skills = "Mandatory skills are required";
    if (!form.location.trim()) newErrors.location = "Location is required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const submit = async () => {
    if (!validateForm()) return;

    const payload = {
      ...form,
      mandatory_skills: form.mandatory_skills.split(",").map((s) => s.trim()),
      nice_to_have_skills: form.nice_to_have_skills.split(",").map((s) => s.trim()).filter(s => s),
      inclusion_criteria: form.inclusion_criteria.split(",").map((s) => s.trim()).filter(s => s),
      exclusion_criteria: form.exclusion_criteria.split(",").map((s) => s.trim()).filter(s => s),
      team_size: parseInt(form.team_size) || 1,
    };

    try {
      const res = await createJD(payload);
      setResult(res.data);
      setEditedJDText(res.data.jd_text);
      setPreviewMode(true);
      if (onJDCreate) onJDCreate();
    } catch (error) {
      console.error("Create JD failed:", error);
    }
  };

  const confirmJD = async () => {
    try {
      // If the text was edited, update it
      if (editedJDText !== result.jd_text) {
        await updateJDText(result.jd_id, editedJDText);
        setResult({ ...result, jd_text: editedJDText });
      }
      // Approve the JD
      await approveJD(result.jd_id);
      setResult({ ...result, status: "APPROVED" });
      setPreviewMode(false);
    } catch (error) {
      console.error("Confirm JD failed:", error);
      alert("Failed to confirm JD. Please try again.");
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Create Job Description</h2>

      {/* Mode Selector */}
      <div className="mb-6">
        <div className="flex space-x-2">
          {["manual", "paste", "upload"].map((m) => (
            <button
              key={m}
              className={`px-4 py-2 rounded ${mode === m ? "bg-blue-600 text-white" : "bg-gray-200"}`}
              onClick={() => setMode(m)}
            >
              {m === "manual" ? "Fill Manually" : m === "paste" ? "Paste JD" : "Upload JD"}
            </button>
          ))}
        </div>
      </div>

      {/* Template Selector */}
      <div className="mb-6">
        <select
          className="border p-2 w-full"
          onChange={(e) => e.target.value && applyTemplate(e.target.value)}
        >
          <option value="">Use Template (Optional)</option>
          {Object.keys(templates).map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* Mode Content */}
      {mode === "paste" && (
        <div className="mb-6">
          <textarea
            placeholder="Paste the job description text here..."
            className="border p-2 w-full h-32 mb-3"
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
          />
          <button
            className="bg-green-600 text-white px-4 py-2"
            onClick={extractFromPaste}
            disabled={loading}
          >
            {loading ? "Extracting..." : "Extract Fields"}
          </button>
        </div>
      )}

      {mode === "upload" && (
        <div className="mb-6">
          <input
            type="file"
            accept=".pdf,.docx"
            className="border p-2 w-full mb-3"
            onChange={(e) => setUploadedFile(e.target.files[0])}
          />
          {uploadedFile && (
            <div className="mb-3">
              <p>File: {uploadedFile.name} ({(uploadedFile.size / 1024).toFixed(1)} KB)</p>
              <button
                className="bg-green-600 text-white px-4 py-2"
                onClick={extractFromUpload}
                disabled={loading}
              >
                {loading ? "Extracting..." : "Extract from File"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Form Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {[
          { key: "title", label: "Job Title", required: true },
          { key: "level", label: "Level", required: true },
          { key: "location", label: "Location", required: true },
          { key: "team_size", label: "Team Size", type: "number" },
          { key: "budget", label: "Budget" },
        ].map(({ key, label, required, type = "text" }) => (
          <div key={key}>
            <input
              type={type}
              placeholder={label}
              className={`border p-2 w-full ${errors[key] ? "border-red-500" : ""}`}
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
            {required && <span className="text-red-500">*</span>}
            {errors[key] && <p className="text-red-500 text-sm">{errors[key]}</p>}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {[
          { key: "mandatory_skills", label: "Mandatory Skills (comma separated)", required: true },
          { key: "nice_to_have_skills", label: "Nice to Have Skills (comma separated)" },
          { key: "inclusion_criteria", label: "Inclusion Criteria (comma separated)" },
          { key: "exclusion_criteria", label: "Exclusion Criteria (comma separated)" },
        ].map(({ key, label, required }) => (
          <div key={key}>
            <textarea
              placeholder={label}
              className={`border p-2 w-full h-20 ${errors[key] ? "border-red-500" : ""}`}
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
            {required && <span className="text-red-500">*</span>}
            {errors[key] && <p className="text-red-500 text-sm">{errors[key]}</p>}
          </div>
        ))}
      </div>

      {/* Confidence Scores */}
      {extractedData && extractedData.confidence_scores && (
        <div className="mb-6 p-4 bg-yellow-50 border">
          <h3 className="font-semibold mb-2">Extraction Confidence</h3>
          {Object.entries(extractedData.confidence_scores).map(([field, score]) => (
            <div key={field} className="flex justify-between">
              <span>{field}:</span>
              <span className={score < 0.6 ? "text-red-600" : "text-green-600"}>
                {(score * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}

      <button
        className="bg-black text-white px-6 py-3 text-lg"
        onClick={submit}
        disabled={loading}
      >
        Generate JD
      </button>

      {previewMode && result && (
        <div className="mt-6 p-4 border bg-blue-50">
          <h3 className="text-lg font-semibold mb-4">Preview and Edit JD</h3>
          <textarea
            value={editedJDText}
            onChange={(e) => setEditedJDText(e.target.value)}
            className="w-full h-64 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Edit the job description here..."
          />
          <button
            className="mt-4 bg-green-600 text-white px-6 py-2 rounded"
            onClick={confirmJD}
          >
            Confirm JD
          </button>
        </div>
      )}

      {result && !previewMode && (
        <div className="mt-6 p-4 border bg-green-50">
          <p><b>JD ID:</b> {result.jd_id}</p>
          <p><b>Status:</b> {result.status}</p>

          <div className="mt-4">
            <label className="block text-sm font-medium mb-2">Google Drive Folder URL:</label>
            <input
              type="url"
              value={driveUrl}
              onChange={(e) => setDriveUrl(e.target.value)}
              placeholder="https://drive.google.com/drive/folders/..."
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <small className="block mt-1 text-gray-500 text-xs">
              Paste the URL of a Google Drive folder containing resume PDFs
            </small>
          </div>

          <button
            className="mt-4 bg-blue-600 text-white px-6 py-2 rounded disabled:bg-gray-400 disabled:cursor-not-allowed"
            onClick={async () => {
              if (!driveUrl.trim()) {
                alert("Please provide a Google Drive folder URL");
                return;
              }

              setFilteringLoading(true);
              try {
                const res = await rankResumes(result.jd_id, driveUrl);
                const rankedResumes = res.data.results;

                // Transform the ranked resumes to match the expected candidate format
                const candidates = rankedResumes.map((rankedResume, index) => ({
                  ucid: `NVISUST-2025-${String(index + 1).padStart(4, '0')}`, // Generate UCID from index
                  candidate_name: rankedResume.candidate_name || `Candidate ${index + 1}`,
                  job_id: result.jd_id,
                  fit_score: Math.round(rankedResume.score * 100), // Convert to percentage
                  key_skills: rankedResume.matched_keywords.slice(0, 5), // Take first 5 matched keywords
                  experience_summary: `Experience level: ${rankedResume.experience_level.toFixed(1)}/1.0`,
                  strengths: [
                    `Role category: ${rankedResume.role_category}`,
                    `Rank: ${rankedResume.rank}`,
                    `Status: ${rankedResume.status}`
                  ],
                  gaps: [], // Could be enhanced based on missing keywords
                  screening_decision: rankedResume.status === "High Match" ? "PASS" : "REVIEW"
                }));

                if (onCandidatesFetched) {
                  onCandidatesFetched(candidates);
                }
              } catch (error) {
                console.error("Filtering failed:", error);
                console.error("Error response:", error.response?.data);
                alert(`Failed to filter candidates: ${error.response?.data?.detail || error.message || "Unknown error"}`);
              } finally {
                setFilteringLoading(false);
              }
            }}
            disabled={filteringLoading}
          >
            {filteringLoading ? "Filtering Candidates..." : "Go for Filtering"}
          </button>
        </div>
      )}
    </div>
  );
}
