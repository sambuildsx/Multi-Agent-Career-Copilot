import React from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { ArrowLeft, Target, Trophy, Award, BookOpen, AlertTriangle } from 'lucide-react';
import NavBar from '../../components/shared/NavBar';
import ScoreCard from '../../components/optimizer/ScoreCard';
import RecommendationList from '../../components/optimizer/RecommendationList';
import SkillGapBadges from '../../components/optimizer/SkillGapBadges';

export default function ReportPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const report = location.state?.report;

  // Redirect if accessed directly without report data
  if (!report) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

      <NavBar />

      <main className="flex-1 p-6 z-10 max-w-7xl mx-auto w-full space-y-8">
        <header className="flex justify-between items-center mb-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center space-x-2 text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back</span>
          </button>
        </header>

        <div className="flex items-center space-x-4 mb-4">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
            <Trophy className="w-8 h-8 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Career Report</h1>
            <p className="text-slate-400">Comprehensive AI Evaluation</p>
          </div>
        </div>

        {/* Top Scores Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {report.overall_score !== null && report.overall_score !== undefined && (
             <div className="glass-card p-5 border-t-2 border-t-indigo-500 flex flex-col items-center justify-center">
               <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">Overall</span>
               <span className="text-4xl font-bold text-white">{report.overall_score}</span>
             </div>
          )}
          {report.interview_score !== null && report.interview_score !== undefined && (
             <div className="glass-card p-5 border-t-2 border-t-blue-500 flex flex-col items-center justify-center">
               <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">Interview</span>
               <span className="text-4xl font-bold text-white">{report.interview_score}</span>
             </div>
          )}
          {report.resume_score !== null && report.resume_score !== undefined && (
             <div className="glass-card p-5 border-t-2 border-t-emerald-500 flex flex-col items-center justify-center">
               <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">Resume</span>
               <span className="text-4xl font-bold text-white">{report.resume_score}</span>
             </div>
          )}
          {report.github_score !== null && report.github_score !== undefined && (
             <div className="glass-card p-5 border-t-2 border-t-purple-500 flex flex-col items-center justify-center">
               <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">GitHub</span>
               <span className="text-4xl font-bold text-white">{report.github_score}</span>
             </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-panel p-6">
              <h3 className="text-xl font-semibold mb-4 text-slate-200">Coach Summary</h3>
              <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                {report.markdown || "No summary provided."}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="glass-panel p-6 border-l-4 border-l-emerald-500">
                <h3 className="font-semibold text-emerald-400 mb-3 flex items-center gap-2">
                  <Award className="w-5 h-5" /> Strengths
                </h3>
                <ul className="space-y-2 text-sm text-slate-300">
                  {report.strengths?.map((item, idx) => (
                    <li key={idx} className="flex gap-2">
                      <span className="text-emerald-500 mt-0.5">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                  {(!report.strengths || report.strengths.length === 0) && (
                    <li className="italic text-slate-500">No strengths identified.</li>
                  )}
                </ul>
              </div>

              <div className="glass-panel p-6 border-l-4 border-l-rose-500">
                <h3 className="font-semibold text-rose-400 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" /> Areas to Improve
                </h3>
                <ul className="space-y-2 text-sm text-slate-300">
                  {report.weaknesses?.map((item, idx) => (
                    <li key={idx} className="flex gap-2">
                      <span className="text-rose-500 mt-0.5">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                  {(!report.weaknesses || report.weaknesses.length === 0) && (
                    <li className="italic text-slate-500">No areas to improve identified.</li>
                  )}
                </ul>
              </div>
            </div>
            
            {report.learning_roadmap && report.learning_roadmap.length > 0 && (
              <div className="glass-panel p-6">
                <h3 className="font-semibold text-lg mb-4 text-slate-200 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-amber-400" /> Learning Roadmap
                </h3>
                <div className="space-y-4">
                  {report.learning_roadmap.map((step, idx) => (
                    <div key={idx} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-600 flex items-center justify-center text-sm font-bold text-slate-300">
                          {idx + 1}
                        </div>
                        {idx !== report.learning_roadmap.length - 1 && (
                          <div className="w-0.5 h-full bg-slate-800 mt-2"></div>
                        )}
                      </div>
                      <div className="bg-slate-900/60 p-4 rounded-xl flex-1 border border-slate-800/50">
                        <p className="text-slate-300 text-sm">{step}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-1 space-y-6">
            <SkillGapBadges 
               presentSkills={[]} 
               missingSkills={report.missing_skills || []} 
            />
            <div className="h-full min-h-[400px]">
              <RecommendationList recommendations={report.recommendations || []} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
