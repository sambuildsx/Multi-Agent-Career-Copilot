import React from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { ArrowLeft, Download, User } from 'lucide-react';
import NavBar from '../components/NavBar';
import ScoreCard from '../components/ScoreCard';
import SkillGapBadges from '../components/SkillGapBadges';
import RecommendationList from '../components/RecommendationList';

export default function DashboardPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const results = location.state?.results;

  // Redirect if accessed directly without results
  if (!results) {
    return <Navigate to="/analyze" replace />;
  }

  const score = results.score || 0;
  const matchCategory = score >= 80 ? 'Strong Match' : score >= 60 ? 'Potential Match' : 'Weak Match';

  // FinalReport (backend) only ever produces: resume_score, ats_score,
  // top_recommendations, missing_skills, report_markdown. There is no
  // present_skills or summary field from the backend yet — those stay as
  // placeholders until an agent actually produces them, rather than
  // silently faking data under a real-looking field name.
  const analysis = results.analysis || {};
  const missingSkills = analysis.missing_skills || [];
  const recommendations = analysis.top_recommendations || [];
  const reportMarkdown = analysis.report_markdown;

  return (
    <div className="min-h-screen">
      <NavBar />

      <div className="p-6 max-w-7xl mx-auto">
        <header className="flex justify-between items-center mb-8">
          <button
            onClick={() => navigate('/analyze')}
            className="flex items-center space-x-2 text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">New Analysis</span>
          </button>

          <div className="flex space-x-4">
            <button className="btn-secondary flex items-center space-x-2">
              <Download className="w-4 h-4" />
              <span>Export Report</span>
            </button>
          </div>
        </header>

        <div className="mb-8 flex items-center space-x-4">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
            <User className="w-8 h-8 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Candidate Analysis</h1>
            <p className="text-slate-400">{results.filename || "Resume.pdf"} • Processed Just Now</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <ScoreCard score={score} category={matchCategory} />

            <div className="glass-panel p-6">
              <h3 className="text-lg font-semibold mb-4 text-slate-200">Overall Assessment</h3>
              <p className="text-slate-300 leading-relaxed text-sm whitespace-pre-wrap">
                {reportMarkdown || "No detailed report available for this analysis."}
              </p>
            </div>
          </div>

          <div className="lg:col-span-2 flex flex-col space-y-6">
            <SkillGapBadges
              presentSkills={[]}
              missingSkills={missingSkills}
            />

            <div className="flex-1 min-h-[300px]">
              <RecommendationList recommendations={recommendations} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}