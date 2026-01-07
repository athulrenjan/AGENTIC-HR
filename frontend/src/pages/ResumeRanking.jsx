import React, { useState, useEffect } from 'react';
import { listJDs, rankResumes } from '../api/jdApi';

const ResumeRanking = () => {
  const [jds, setJds] = useState([]);
  const [selectedJd, setSelectedJd] = useState('');
  const [driveUrl, setDriveUrl] = useState('');
  const [rankingResults, setRankingResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadJDs();
  }, []);

  const loadJDs = async () => {
    try {
      const res = await listJDs();
      setJds(res.data);
    } catch (err) {
      setError('Failed to load JDs');
    }
  };

  const handleRankResumes = async () => {
    if (!selectedJd || !driveUrl) {
      setError('Please select a JD and provide a Drive folder URL');
      return;
    }

    setLoading(true);
    setError('');
    setRankingResults(null);

    try {
      const results = await rankResumes(selectedJd, driveUrl);
      setRankingResults(results.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to rank resumes');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Resume Ranking</h1>

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Select Job Description:</label>
          <select
            value={selectedJd}
            onChange={(e) => setSelectedJd(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Choose a JD...</option>
            {jds.map((jd) => (
              <option key={jd.jd_id} value={jd.jd_id}>
                {jd.fields.title} ({jd.jd_id})
              </option>
            ))}
          </select>
        </div>

        <div className="mb-4">
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
          onClick={handleRankResumes}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
        >
          {loading ? 'Ranking Resumes...' : 'Rank Resumes'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
          {error}
        </div>
      )}

      {rankingResults && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Ranking Results</h2>
          <div className="bg-gray-50 p-4 rounded-md mb-6">
            <p className="mb-2"><strong>JD ID:</strong> {rankingResults.jd_id}</p>
            <p className="mb-2"><strong>Drive Folder ID:</strong> {rankingResults.drive_folder_id}</p>
            <p><strong>Total Resumes Ranked:</strong> {rankingResults.results.length}</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-50">
                  <th className="p-3 text-left font-semibold border-b">Rank</th>
                  <th className="p-3 text-left font-semibold border-b">Resume Name</th>
                  <th className="p-3 text-left font-semibold border-b">Match Score</th>
                  <th className="p-3 text-left font-semibold border-b">Status</th>
                </tr>
              </thead>
              <tbody>
                {rankingResults.results.map((result) => (
                  <tr key={result.rank} className="border-b hover:bg-gray-50">
                    <td className="p-3">{result.rank}</td>
                    <td className="p-3">{result.resume_name}</td>
                    <td className="p-3">{(result.score * 100).toFixed(1)}%</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        result.score > 0.7
                          ? 'bg-green-100 text-green-800'
                          : result.score > 0.5
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {result.score > 0.7 ? 'High Match' : result.score > 0.5 ? 'Medium Match' : 'Low Match'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeRanking;
