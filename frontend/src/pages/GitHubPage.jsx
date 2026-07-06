import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GitBranch, Search, Code, Activity, Star } from 'lucide-react';
import NavBar from '../components/NavBar';
import api from '../api';
import ScoreCard from '../components/ScoreCard';

export default function GitHubPage() {
  const [repoUrl, setRepoUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setIsAnalyzing(true);
    setError(null);
    setResults(null);

    try {
      // The backend expects /github/?repo_url=...
      const res = await api.get(`/github/?repo_url=${encodeURIComponent(repoUrl.trim())}`);
      setResults(res.data);
    } catch (err) {
      console.error('GitHub analysis failed:', err);
      setError(err.response?.data?.detail || 'Failed to analyze repository.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

      <NavBar />

      <main className="flex-1 p-6 z-10 max-w-7xl mx-auto w-full">
        <div className="text-center mb-10">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 flex items-center justify-center gap-3">
            <GitBranch className="w-10 h-10" />
            GitHub Portfolio Review
          </h1>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Analyze your GitHub repository to see how recruiters and engineering managers evaluate your open-source presence.
          </p>
        </div>

        <div className="max-w-2xl mx-auto mb-12">
          <form onSubmit={handleAnalyze} className="flex gap-4">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-slate-500" />
              </div>
              <input
                type="url"
                required
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/username/repository"
                className="glass-input w-full pl-12 py-4 text-lg"
              />
            </div>
            <button
              type="submit"
              disabled={isAnalyzing || !repoUrl.trim()}
              className="btn-primary px-8 flex items-center justify-center whitespace-nowrap"
            >
              {isAnalyzing ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                'Analyze Repo'
              )}
            </button>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
              {error}
            </div>
          )}
        </div>

        {results && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-[fadeIn_0.3s_ease-out]">
            <div className="space-y-6">
              <ScoreCard score={results.overall_github_score} category="Overall Portfolio Score" />
              
              <div className="glass-panel p-6">
                <h3 className="font-semibold text-lg mb-4 text-slate-200">Repository Details</h3>
                <div className="space-y-4 text-sm">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                    <span className="text-slate-400">Owner</span>
                    <span className="font-medium">{results.username}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                    <span className="text-slate-400">Repositories Analyzed</span>
                    <span className="font-medium">{results.repos?.length || 0}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-2 space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="glass-card p-4 flex flex-col items-center justify-center text-center">
                  <Code className="w-8 h-8 text-blue-400 mb-2" />
                  <span className="text-2xl font-bold">{results.repo_quality_score}/100</span>
                  <span className="text-xs text-slate-400 uppercase tracking-wider mt-1">Code Quality</span>
                </div>
                <div className="glass-card p-4 flex flex-col items-center justify-center text-center">
                  <Activity className="w-8 h-8 text-emerald-400 mb-2" />
                  <span className="text-2xl font-bold">{results.activity_score}/100</span>
                  <span className="text-xs text-slate-400 uppercase tracking-wider mt-1">Activity Level</span>
                </div>
                <div className="glass-card p-4 flex flex-col items-center justify-center text-center">
                  <Star className="w-8 h-8 text-amber-400 mb-2" />
                  <span className="text-2xl font-bold">{results.readme_quality_score}/100</span>
                  <span className="text-xs text-slate-400 uppercase tracking-wider mt-1">Documentation</span>
                </div>
              </div>

              <div className="glass-panel p-6">
                <h3 className="font-semibold text-lg mb-4 text-slate-200">Language Distribution</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(results.languages || {}).map(([lang, percentage]) => (
                    <span key={lang} className="px-3 py-1 bg-slate-800 rounded-full text-sm font-medium border border-slate-700">
                      {lang}: {percentage}%
                    </span>
                  ))}
                  {Object.keys(results.languages || {}).length === 0 && (
                    <span className="text-slate-500 italic">No language data available.</span>
                  )}
                </div>
              </div>

              <div className="glass-panel p-6">
                <h3 className="font-semibold text-lg mb-4 text-slate-200">Recruiter Feedback</h3>
                <ul className="space-y-3">
                  {results.portfolio_feedback?.map((feedback, index) => (
                    <li key={index} className="flex items-start gap-3 text-slate-300">
                      <span className="text-purple-400 mt-0.5">•</span>
                      <span>{feedback}</span>
                    </li>
                  ))}
                  {(!results.portfolio_feedback || results.portfolio_feedback.length === 0) && (
                    <li className="text-slate-500 italic">No specific feedback provided.</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
