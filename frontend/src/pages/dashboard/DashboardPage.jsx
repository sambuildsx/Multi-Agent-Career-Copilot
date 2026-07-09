import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Download, User, Activity, Search, BookOpen, Star, FileText, Percent, Target } from 'lucide-react';
import NavBar from '../../components/shared/NavBar';
import ScoreCard from '../../components/optimizer/ScoreCard';
import SkillGapBadges from '../../components/optimizer/SkillGapBadges';
import RecommendationList from '../../components/optimizer/RecommendationList';
import api from '../../api';

export default function DashboardPage() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [latestAnalysis, setLatestAnalysis] = useState(null);
  const [atsData, setAtsData] = useState(null);
  const [interviews, setInterviews] = useState([]);

  const initialResults = location.state?.results;

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const interviewsRes = await api.get('/interview/');
        setInterviews(interviewsRes.data);

        let jobId = initialResults?.job_id;
        
        if (!jobId) {
          const jobsRes = await api.get('/optimizer/');
          const completedJobs = jobsRes.data.filter(j => j.status === 'completed');
          if (completedJobs.length > 0) {
            jobId = completedJobs[0].job_id;
          }
        }

        if (jobId) {
          const [jobRes, reportRes] = await Promise.all([
            api.get(`/optimizer/result/${jobId}`),
            api.get(`/optimizer/report/${jobId}`).catch(() => ({ data: null }))
          ]);

          // Only meaningfully present when the job ran in JD-match mode —
          // ats_node never runs in "Normal Optimization" mode (see
          // routing.route_to_ats), so this will be null/undefined there.
          const atsResult = jobRes.data.agents?.ats?.data;
          const atsRan = atsResult && atsResult.status !== 'pending';
          setAtsData(atsRan ? atsResult : null);

          const finalReport = reportRes.data;
          
          setLatestAnalysis({
            jobId,
            filename: initialResults?.filename || "Resume.pdf",
            score: finalReport?.resume_score ?? atsResult?.overall_score ?? 0,
            hasAtsScore: atsRan && atsResult?.overall_score != null,
            analysis: finalReport || initialResults?.analysis || {},
          });
        }
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
        setError("Could not load dashboard data. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [initialResults]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <NavBar />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center">
            <div className="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mb-4" />
            <p className="text-slate-400 font-medium">Loading Dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  const analysis = latestAnalysis?.analysis || {};
  const missingSkills = analysis.missing_skills || atsData?.missing_skills || [];
  const recommendations = analysis.top_recommendations || [];
  const reportMarkdown = analysis.report_markdown;
  const score = latestAnalysis?.score || 0;

  // Only call this a "Match" when a JD was actually compared against.
  // In Normal Optimization mode (no ats_score), this is a resume quality
  // score, not a match score — the label should say so.
  const isMatchScore = Boolean(latestAnalysis?.hasAtsScore);
  const matchCategory = isMatchScore
    ? (score >= 80 ? 'Strong Match' : score >= 60 ? 'Potential Match' : 'Weak Match')
    : (score >= 80 ? 'Excellent Resume' : score >= 60 ? 'Good Resume' : 'Needs Improvement');

  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-12">
        
        {/* TOP SECTION: LATEST ANALYSIS */}
        <section>
          <header className="flex justify-between items-center mb-8">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                <User className="w-8 h-8 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold">Candidate Analysis</h1>
                <p className="text-slate-400">
                  {latestAnalysis ? `${latestAnalysis.filename} • Latest Assessment` : 'No analysis available'}
                </p>
              </div>
            </div>

            <div className="flex space-x-4">
              <button
                onClick={() => navigate('/analyze')}
                className="btn-primary flex items-center space-x-2"
              >
                <span>New Analysis</span>
              </button>
            </div>
          </header>

          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
              {error}
            </div>
          )}

          {!latestAnalysis && !error ? (
            <div className="glass-panel p-12 text-center flex flex-col items-center">
              <FileText className="w-16 h-16 text-slate-500 mb-4" />
              <h2 className="text-xl font-semibold mb-2">No Resume Analyzed Yet</h2>
              <p className="text-slate-400 mb-6">Upload your resume and a job description to get a comprehensive AI review.</p>
              <button onClick={() => navigate('/analyze')} className="btn-primary">
                Analyze Resume
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-[fadeIn_0.3s_ease-out]">
              <div className="lg:col-span-1 space-y-6">
                <ScoreCard score={score} category={matchCategory} />

                {atsData && (
                  <div className="glass-panel p-6">
                    <h3 className="text-lg font-semibold mb-4 text-slate-200 border-b border-slate-700/50 pb-2">ATS Sub-Scores</h3>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400 flex items-center gap-2"><Search className="w-4 h-4"/> Keyword Match</span>
                        <span className="font-semibold">{atsData.keyword_match_score}/100</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${atsData.keyword_match_score}%` }}></div>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400 flex items-center gap-2"><Target className="w-4 h-4"/> Required Skills</span>
                        <span className="font-semibold">{atsData.required_skills_match}/100</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${atsData.required_skills_match}%` }}></div>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400 flex items-center gap-2"><Star className="w-4 h-4"/> Preferred Skills</span>
                        <span className="font-semibold">{atsData.preferred_skills_match}/100</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: `${atsData.preferred_skills_match}%` }}></div>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400 flex items-center gap-2"><BookOpen className="w-4 h-4"/> Completeness</span>
                        <span className="font-semibold">{atsData.completeness_score}/100</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${atsData.completeness_score}%` }}></div>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400 flex items-center gap-2"><Activity className="w-4 h-4"/> Project Relevance</span>
                        <span className="font-semibold">{atsData.project_relevance_score}/100</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${atsData.project_relevance_score}%` }}></div>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400 flex items-center gap-2"><Percent className="w-4 h-4"/> Quantification</span>
                        <span className="font-semibold">{atsData.quantification_score}/100</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div className="bg-rose-500 h-1.5 rounded-full" style={{ width: `${atsData.quantification_score}%` }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="lg:col-span-2 flex flex-col space-y-6">
                <div className="glass-panel p-6">
                  <h3 className="text-lg font-semibold mb-4 text-slate-200">Coach's Assessment</h3>
                  <p className="text-slate-300 leading-relaxed text-sm whitespace-pre-wrap">
                    {reportMarkdown || "No detailed report available for this analysis."}
                  </p>
                </div>

                <SkillGapBadges
                  presentSkills={[]}
                  missingSkills={missingSkills}
                />

                <div className="flex-1 min-h-[300px]">
                  <RecommendationList recommendations={recommendations} />
                </div>
              </div>
            </div>
          )}
        </section>

        {/* BOTTOM SECTION: INTERVIEW HISTORY */}
        <section className="pt-6 border-t border-slate-800">
          <header className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Interview History</h2>
            <button
              onClick={() => navigate('/interview')}
              className="text-sm font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Start New Mock Interview &rarr;
            </button>
          </header>

          {interviews.length === 0 ? (
            <div className="glass-panel p-8 text-center">
              <p className="text-slate-400">You haven't completed any mock interviews yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {interviews.map((interview) => (
                <div key={interview.session_id} className="glass-card p-5 hover:border-indigo-500/50 transition-colors group">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-semibold text-lg text-slate-200 capitalize">{interview.domain}</h3>
                      <p className="text-xs text-slate-500 mt-1">
                        {new Date(interview.completed_at || Date.now()).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      interview.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      {interview.status}
                    </span>
                  </div>
                  
                  {interview.status === 'completed' && (
                    <div className="mt-4 flex items-center justify-between border-t border-slate-800/50 pt-4">
                      <span className="text-sm text-slate-400">Score</span>
                      <span className="text-lg font-bold text-white">{interview.overall_score || '--'}/100</span>
                    </div>
                  )}
                  
                  {interview.status === 'completed' && (
                    <button 
                      onClick={() => navigate('/report', { state: { report: { overall_score: interview.overall_score } }})}
                      className="mt-4 w-full py-2 text-sm font-medium text-center bg-slate-800/50 hover:bg-slate-800 rounded-lg transition-colors"
                    >
                      View Report
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

      </main>
    </div>
  );
}