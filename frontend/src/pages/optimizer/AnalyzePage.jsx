import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import ResumeUpload from '../../components/optimizer/ResumeUpload';
import NavBar from '../../components/shared/NavBar';
import CursorGrid from '../../components/shared/CursorGrid';
import ResumeAnalysisLoader from '../../components/shared/ResumeAnalysisLoader';
import api from '../../api';

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.45, delay: i * 0.08, ease: [0.25, 0.46, 0.45, 0.94] },
  }),
};

export default function AnalyzePage() {
  const [mode, setMode] = useState('normal'); // 'normal' | 'jd'
  const [resumeFile, setResumeFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const navigate = useNavigate();

  const handleFileSelected = (file) => {
    setResumeFile(file);
  };

  const handleModeChange = (newMode) => {
    setMode(newMode);
    if (newMode === 'normal') setJdText('');
  };

  const handleAnalyze = async () => {
    if (!resumeFile) return;
    if (mode === 'jd' && !jdText.trim()) return;

    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append('file', resumeFile);
      const uploadRes = await api.post('/upload/resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const { filename } = uploadRes.data;

      const analyzeRes = await api.post('/optimizer/analyze', {
        filename,
        jd_text: mode === 'jd' ? jdText.trim() : null,
      });
      const { job_id } = analyzeRes.data;

      const POLL_INTERVAL_MS = 3000;
      const MAX_POLLS = 60;
      let report = null;

      for (let i = 0; i < MAX_POLLS; i++) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
        const statusRes = await api.get(`/optimizer/result/${job_id}`);
        const { status } = statusRes.data;

        if (status === 'completed') {
          const reportRes = await api.get(`/optimizer/report/${job_id}`);
          report = reportRes.data;
          break;
        } else if (status === 'failed') {
          throw new Error('Analysis job failed on the server. Check backend logs.');
        }
      }

      if (!report) {
        throw new Error('Analysis timed out. The job is still running — try again later.');
      }

      // Navigate directly to the report page on success
      const hasJdVal = mode === 'jd' && !!jdText.trim();
      navigate('/report', {
        state: {
          report: {
            ...report,
            job_id,
            filename: resumeFile.name,
            score: report.resume_score ?? report.ats_score ?? 0,
            has_jd_analysis: hasJdVal,
          },
          hasJd: hasJdVal,
        },
      });
    } catch (error) {
      console.error('Analysis failed:', error);
      alert(error.response?.data?.detail || error.message || 'An error occurred during analysis. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const canAnalyze =
    !isAnalyzing && resumeFile && (mode === 'normal' || jdText.trim().length > 0);

  return (
    <div
      className="min-h-screen flex flex-col relative overflow-x-hidden"
      style={{ background: 'linear-gradient(180deg, #060b16 0%, #0b1220 100%)' }}
    >
      {isAnalyzing && <ResumeAnalysisLoader />}

      <div className="fixed inset-0 z-0 pointer-events-none md:pointer-events-auto">
        <CursorGrid
          cellSize={85} color="#4CC9F0" radius={120} falloff="smooth"
          holdTime={300} fadeDuration={700} lineWidth={0.8} maxOpacity={0.4}
          fillOpacity={0} gridOpacity={0.05} cellRadius={8} clickPulse={false}
        />
      </div>
      <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] -z-10 pointer-events-none" />

      <NavBar />

      <main className="flex-1 flex flex-col items-center justify-center p-6 z-10 pt-24 pb-16">
        <motion.div variants={fadeUp} custom={0} initial="hidden" animate="show" className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Resume Optimization</h1>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Get a general resume review, or compare it against a specific job description.
          </p>
        </motion.div>

        <motion.div variants={fadeUp} custom={1} initial="hidden" animate="show" className="w-full max-w-2xl mx-auto space-y-6">
          <div className="flex gap-2 p-1 bg-slate-900/60 rounded-xl border border-slate-700/50 w-fit mx-auto">
            <button
              onClick={() => handleModeChange('normal')}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors ${
                mode === 'normal' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Normal Optimization
            </button>
            <button
              onClick={() => handleModeChange('jd')}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors ${
                mode === 'jd' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Match to Job Description
            </button>
          </div>

          <ResumeUpload onFileSelected={handleFileSelected} selectedFile={resumeFile} />

          {mode === 'jd' && (
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
            </div>
          )}

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
        </motion.div>
      </main>
    </div>
  );
}