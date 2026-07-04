import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ResumeUpload from '../components/ResumeUpload';
import api from '../api';
import { LogOut } from 'lucide-react';

export default function AnalyzePage() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const navigate = useNavigate();

  // Step 1: just stash the file, don't upload yet — we still need the JD
  const handleFileSelected = (file) => {
    setResumeFile(file);
  };

  const handleAnalyze = async () => {
    if (!resumeFile || !jdText.trim()) return;

    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append('file', resumeFile);
      const uploadRes = await api.post('/upload/resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const { filename } = uploadRes.data;

      const analyzeRes = await api.post('/jobs/analyze', {
        filename,
        jd_text: jdText.trim(),
        github_repo_url: githubUrl.trim() || null,
      });
      const { job_id } = analyzeRes.data;

      const POLL_INTERVAL_MS = 3000;
      const MAX_POLLS = 60;
      let report = null;

      for (let i = 0; i < MAX_POLLS; i++) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
        const statusRes = await api.get(`/jobs/${job_id}`);
        const { status } = statusRes.data;

        if (status === 'completed') {
          const reportRes = await api.get(`/jobs/${job_id}/report`);
          report = reportRes.data;
          break;
        } else if (status === 'failed') {
          throw new Error('Analysis job failed on the server. Check backend logs.');
        }
      }

      if (!report) {
        throw new Error('Analysis timed out. The job is still running — try again later.');
      }

      navigate('/dashboard', {
        state: {
          results: {
            ...report,
            filename: resumeFile.name,
            score: report.resume_score ?? report.ats_score ?? 0,
            analysis: report,
          },
        },
      });
    } catch (error) {
      console.error('Analysis failed:', error);
      alert(error.response?.data?.detail || error.message || 'An error occurred during analysis. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const canAnalyze = resumeFile && jdText.trim().length > 0 && !isAnalyzing;

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

      <header className="p-6 flex justify-between items-center z-10">
        <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
          Recruiter Copilot
        </h2>
        <button
          onClick={handleLogout}
          className="flex items-center space-x-2 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span className="text-sm font-medium">Sign Out</span>
        </button>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 z-10">
        <div className="text-center mb-10">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Analyze Candidate</h1>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Upload a resume, paste the job description, and let the AI agents score the fit.
          </p>
        </div>

        <div className="w-full max-w-2xl mx-auto space-y-6">
          <ResumeUpload onFileSelected={handleFileSelected} selectedFile={resumeFile} />

          <div className="glass-panel p-6 rounded-2xl border border-slate-700">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Job Description *
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the job description here..."
              rows={8}
              className="w-full bg-slate-900/80 border border-slate-700/50 rounded-xl p-4 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none"
            />

            <label className="block text-sm font-medium text-slate-300 mt-4 mb-2">
              GitHub Repo URL (optional)
            </label>
            <input
              type="text"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/username/repo"
              className="w-full bg-slate-900/80 border border-slate-700/50 rounded-xl p-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <button
            onClick={handleAnalyze}
            disabled={!canAnalyze}
            className="btn-primary w-full flex items-center justify-center space-x-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <span>Analyze Resume</span>
            )}
          </button>

          {isAnalyzing && (
            <div className="flex items-center justify-center space-x-3 text-blue-400">
              <span className="flex h-3 w-3 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
              </span>
              <span className="text-sm font-medium">AI Agents are reviewing the profile...</span>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}