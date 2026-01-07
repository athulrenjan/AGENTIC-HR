import { useState } from "react";
import JDCreate from "./pages/JDCreate";
import Navbar from "./components/Navbar";

export default function App() {
  const [generatedJD, setGeneratedJD] = useState(null);
  const [candidates, setCandidates] = useState([]);

  const handleJDGenerated = (jd) => {
    setGeneratedJD(jd);
    // Scroll to preview section
    setTimeout(() => {
      document.getElementById('jd-preview')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleCandidatesFetched = (candidatesData) => {
    setCandidates(candidatesData);
  };

  return (
    <>
      <Navbar />
      <main className="py-8">
        <JDCreate onJDGenerated={handleJDGenerated} onCandidatesFetched={handleCandidatesFetched} />
        
        {generatedJD && (
          <div id="jd-preview" className="max-w-6xl mx-auto mt-12">
            <h2 className="text-2xl font-bold mb-6">Job Description Preview</h2>
            <div className="bg-white p-6 rounded-lg shadow-md">
              <textarea
                className="w-full h-96 p-4 border rounded-md"
                value={generatedJD.jd_text}
                onChange={(e) => setGeneratedJD({ ...generatedJD, jd_text: e.target.value })}
                placeholder="Edit the job description here..."
              />
            </div>
          </div>
        )}

        {candidates.length > 0 && (
          <div className="max-w-6xl mx-auto mt-12">
            <h2 className="text-2xl font-bold mb-6">Filtered Candidates</h2>
            <div className="grid gap-4">
              {candidates.map((candidate, index) => (
                <div key={index} className="bg-white p-6 rounded-lg shadow-md">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div><strong>Candidate Name:</strong> {candidate.candidate_name}</div>
                    <div><strong>UCID:</strong> {candidate.ucid}</div>
                    <div><strong>Job ID:</strong> {candidate.job_id}</div>
                    <div><strong>Fit Score:</strong> {candidate.fit_score}</div>
                    <div><strong>Key Skills:</strong> {candidate.key_skills.join(', ')}</div>
                    <div><strong>Experience Summary:</strong> {candidate.experience_summary}</div>
                    <div><strong>Strengths:</strong> {candidate.strengths.join(', ')}</div>
                    <div><strong>Gaps:</strong> {candidate.gaps.join(', ')}</div>
                    <div><strong>Screening Decision:</strong> {candidate.screening_decision}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </>
  );
}
