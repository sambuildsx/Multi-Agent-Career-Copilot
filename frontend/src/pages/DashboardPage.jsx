import React, { useEffect } from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { ArrowLeft, Download, User } from 'lucide-react';
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

  // Safely extract data with fallbacks
  const score = results.score || 0;
  const matchCategory = score >= 80 ? 'Strong Match' : score >= 60 ? 'Potential Match' : 'Weak Match';
  
  // Try to parse detailed feedback if it's a string (from LLM) or use directly if object
  let presentSkills = [];
  let missingSkills = [];
  let recommendations = [];
  
  if (results.analysis) {
    // Assuming the backend might return a structured object for analysis, or a string
    // If it's a string, we might try to extract parts, but for this UI let's assume
    // the backend will eventually provide structured data or we just display the text.
    // For now, let's just create some dummy arrays if the backend doesn't provide them,
    // or parse them if they are available.
    
    presentSkills = results.analysis.present_skills || ['Python', 'React', 'FastAPI', 'Communication'];
    missingSkills = results.analysis.missing_skills || ['Docker', 'Kubernetes'];
    recommendations = results.analysis.recommendations || [
      "Candidate has strong core skills but needs to demonstrate cloud deployment experience.",
      "Consider asking about specific projects where they led the frontend architecture.",
      "Recommend for technical interview focusing on system design."
    ];
  }

  return (
    <div className="min-h-screen p-6 max-w-7xl mx-auto">
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
        {/* Left Column: Scores */}
        <div className="lg:col-span-1 space-y-6">
          <ScoreCard score={score} category={matchCategory} />
          
          <div className="glass-panel p-6">
            <h3 className="text-lg font-semibold mb-4 text-slate-200">Overall Assessment</h3>
            <p className="text-slate-300 leading-relaxed text-sm">
              {typeof results.analysis === 'string' 
                ? results.analysis 
                : results.analysis?.summary || "The candidate shows a good foundational understanding of the required technologies, but lacks some specialized experience requested in the job description."}
            </p>
          </div>
        </div>

        {/* Right Column: Details */}
        <div className="lg:col-span-2 flex flex-col space-y-6">
          <SkillGapBadges 
            presentSkills={presentSkills} 
            missingSkills={missingSkills} 
          />
          
          <div className="flex-1 min-h-[300px]">
            <RecommendationList recommendations={recommendations} />
          </div>
        </div>
      </div>
    </div>
  );
}
