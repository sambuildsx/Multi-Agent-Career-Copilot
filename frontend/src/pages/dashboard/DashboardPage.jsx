import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FileText, Mic, Briefcase,
  TrendingUp, CheckCircle, Clock, Award,
  Search, BookOpen, Star, Activity, Target, Percent,
  ChevronRight, ArrowUpRight, Zap
} from 'lucide-react';
import {
  RadialBarChart, RadialBar, ResponsiveContainer,
  AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';
import NavBar from '../../components/shared/NavBar';
import CursorGrid from '../../components/shared/CursorGrid';
import ScoreCard from '../../components/optimizer/ScoreCard';
import SkillGapBadges from '../../components/optimizer/SkillGapBadges';
import RecommendationList from '../../components/optimizer/RecommendationList';
import api from '../../api';

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.5, delay: i * 0.08, ease: [0.25, 0.46, 0.45, 0.94] }
  })
};

const QUICK_ACTIONS = [
  {
    icon: FileText,
    label: 'Analyze Resume',
    desc: 'Upload and score your resume against a job description',
    href: '/analyze',
    accent: '#4CC9F0',
    bg: 'from-cyan-500/10 to-blue-600/5',
    border: 'border-cyan-500/20 hover:border-cyan-400/40',
    glow: '0 0 20px rgba(76,201,240,0.12)',
  },
  {
    icon: Mic,
    label: 'Practice Interview',
    desc: 'Simulate a mock interview with AI-driven feedback',
    href: '/interview',
    accent: '#38BDF8',
    bg: 'from-sky-500/10 to-blue-500/5',
    border: 'border-sky-500/20 hover:border-sky-400/40',
    glow: '0 0 20px rgba(56,189,248,0.12)',
  },
  {
    icon: Briefcase,
    label: 'Find Opportunities',
    desc: 'Browse curated job listings matched to your profile',
    href: '/dashboard',
    accent: '#4CC9F0',
    bg: 'from-blue-500/10 to-indigo-600/5',
    border: 'border-blue-500/20 hover:border-blue-400/40',
    glow: '0 0 20px rgba(76,201,240,0.12)',
  },
];

// Placeholder chart data
const activityData = [
  { day: 'Mon', score: 42 }, { day: 'Tue', score: 58 }, { day: 'Wed', score: 55 },
  { day: 'Thu', score: 71 }, { day: 'Fri', score: 68 }, { day: 'Sat', score: 82 }, { day: 'Sun', score: 79 },
];

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/90 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-200 shadow-xl backdrop-blur">
        <span className="font-semibold text-cyan-400">{payload[0].value}</span>
        <span className="text-slate-400 ml-1">pts</span>
      </div>
    );
  }
  return null;
};

export default function DashboardPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [latestAnalysis, setLatestAnalysis] = useState(null);
  const [atsData, setAtsData] = useState(null);
  const [interviews, setInterviews] = useState([]);

  const initialResults = location.state?.results;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

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
          if (completedJobs.length > 0) jobId = completedJobs[0].job_id;
        }

        if (jobId) {
          const [jobRes, reportRes] = await Promise.all([
            api.get(`/optimizer/result/${jobId}`),
            api.get(`/optimizer/report/${jobId}`).catch(() => ({ data: null }))
          ]);

          const atsResult = jobRes.data.agents?.ats?.data;
          const atsRan = atsResult && atsResult.status !== 'pending';
          setAtsData(atsRan ? atsResult : null);

          const finalReport = reportRes.data;
          setLatestAnalysis({
            jobId,
            filename: initialResults?.filename || 'Resume.pdf',
            score: finalReport?.resume_score ?? atsResult?.overall_score ?? 0,
            hasAtsScore: atsRan && atsResult?.overall_score != null,
            analysis: finalReport || initialResults?.analysis || {},
          });
        }
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError('Could not load dashboard data. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, [initialResults]);

  const analysis = latestAnalysis?.analysis || {};
  const hasJd = Boolean(analysis.has_jd_analysis) || Boolean(atsData);
  const missingSkills = analysis.missing_skills || atsData?.missing_skills || [];
  const presentSkills = analysis.matched_technologies || atsData?.matched_technologies || [];
  const recommendations = analysis.top_recommendations || [];
  const reportMarkdown = analysis.report_markdown;
  const score = latestAnalysis?.score || 0;
  const isMatchScore = Boolean(latestAnalysis?.hasAtsScore);
  const matchCategory = isMatchScore
    ? (score >= 80 ? 'Strong Match' : score >= 60 ? 'Potential Match' : 'Weak Match')
    : (score >= 80 ? 'Excellent Resume' : score >= 60 ? 'Good Resume' : 'Needs Improvement');

  // Stats for the grid
  const stats = [
    { label: 'Resume Score', value: score > 0 ? `${score}` : '--', unit: '/100', icon: Award, color: '#4CC9F0' },
    { label: 'Reports Run', value: latestAnalysis ? '1' : '0', unit: '', icon: FileText, color: '#38BDF8' },
    { label: 'Interviews', value: `${interviews.length}`, unit: '', icon: Mic, color: '#7C3AED' },
    { label: 'Jobs Found', value: '--', unit: '', icon: Briefcase, color: '#4CC9F0' },
  ];

  return (
    <div
      className="min-h-screen text-slate-100 relative overflow-x-hidden"
      style={{ background: 'linear-gradient(180deg, #060b16 0%, #0b1220 100%)' }}
    >
      {/* Interactive grid background — fixed, behind everything */}
      <div className="fixed inset-0 z-0 pointer-events-none md:pointer-events-auto">
        <CursorGrid
          cellSize={85}
          color="#4CC9F0"
          radius={120}
          falloff="smooth"
          holdTime={300}
          fadeDuration={700}
          lineWidth={0.8}
          maxOpacity={0.4}
          fillOpacity={0}
          gridOpacity={0.05}
          cellRadius={8}
          clickPulse={false}
        />
      </div>

      {/* Ambient glows */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-blue-600/5 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="fixed bottom-0 right-0 w-[500px] h-[400px] bg-violet-600/5 rounded-full blur-[100px] pointer-events-none z-0" />

      {/* Sticky Navbar */}
      <NavBar />

      {/* Main content — offset for fixed navbar */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 pt-24 pb-16 space-y-10">

        {/* ── Welcome Section ── */}
        <motion.section
          variants={fadeUp} custom={0} initial="hidden" animate="show"
          className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
        >
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              {greeting}, Sam 👋
            </h1>
            <p className="mt-1 text-slate-400 text-base">Ready to improve your career?</p>
          </div>
          <button
            onClick={() => navigate('/analyze')}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-cyan-500/20 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0"
          >
            <Zap className="w-4 h-4" />
            New Analysis
          </button>
        </motion.section>

        {/* ── Stats Grid ── */}
        <motion.section
          variants={fadeUp} custom={1} initial="hidden" animate="show"
          className="grid grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              variants={fadeUp} custom={i * 0.5 + 2} initial="hidden" animate="show"
              className="bg-slate-900/50 border border-white/[0.06] rounded-2xl p-5 flex flex-col gap-3 backdrop-blur-sm hover:border-white/10 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{stat.label}</span>
                <div className="p-1.5 rounded-lg" style={{ background: `${stat.color}15` }}>
                  <stat.icon className="w-3.5 h-3.5" style={{ color: stat.color }} />
                </div>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-bold text-white">{stat.value}</span>
                {stat.unit && <span className="text-sm text-slate-500 font-medium">{stat.unit}</span>}
              </div>
            </motion.div>
          ))}
        </motion.section>

        {/* ── Quick Actions ── */}
        <motion.section variants={fadeUp} custom={3} initial="hidden" animate="show">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4 text-cyan-400" /> Quick Actions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {QUICK_ACTIONS.map((action, i) => (
              <motion.button
                key={action.label}
                variants={fadeUp} custom={i * 0.4 + 4} initial="hidden" animate="show"
                onClick={() => navigate(action.href)}
                className={`group relative text-left p-5 rounded-2xl border bg-gradient-to-br ${action.bg} ${action.border} backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:scale-[1.02] focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50`}
                style={{ boxShadow: 'none' }}
                onMouseEnter={e => { e.currentTarget.style.boxShadow = action.glow; }}
                onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none'; }}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2.5 rounded-xl" style={{ background: `${action.accent}18` }}>
                    <action.icon className="w-5 h-5" style={{ color: action.accent }} />
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 transition-colors" />
                </div>
                <h3 className="text-sm font-bold text-white mb-1">{action.label}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{action.desc}</p>
              </motion.button>
            ))}
          </div>
        </motion.section>

        {/* ── Two-column: Recent Analysis + Activity Chart ── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

          {/* Recent Analysis / Career Progress */}
          <motion.div
            variants={fadeUp} custom={6} initial="hidden" animate="show"
            className="lg:col-span-3 bg-slate-900/50 border border-white/[0.06] rounded-2xl p-6 backdrop-blur-sm"
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" /> Career Progress
              </h2>
              {latestAnalysis && (
                <button
                  onClick={() => navigate('/report', { state: { jobId: latestAnalysis.jobId } })}
                  className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
                >
                  View Full Report <ChevronRight className="w-3 h-3" />
                </button>
              )}
            </div>

            {!latestAnalysis && !error ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="p-4 rounded-2xl bg-slate-800/50 mb-4">
                  <FileText className="w-8 h-8 text-slate-500" />
                </div>
                <p className="text-slate-400 text-sm mb-3">No resume analyzed yet</p>
                <button
                  onClick={() => navigate('/analyze')}
                  className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  Analyze your first resume →
                </button>
              </div>
            ) : (
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <ScoreCard score={score} category={matchCategory} />
                  {atsData && (
                    <div className="space-y-3">
                      {[
                        { label: 'Keyword Match', val: atsData.keyword_match_score, color: '#4CC9F0', icon: Search },
                        { label: 'Required Skills', val: atsData.required_skills_match, color: '#10B981', icon: Target },
                        { label: 'Completeness', val: atsData.completeness_score, color: '#F59E0B', icon: BookOpen },
                        { label: 'Project Relevance', val: atsData.project_relevance_score, color: '#8B5CF6', icon: Activity },
                      ].map(item => (
                        <div key={item.label}>
                          <div className="flex justify-between items-center text-xs mb-1">
                            <span className="text-slate-400 flex items-center gap-1">
                              <item.icon className="w-3 h-3" /> {item.label}
                            </span>
                            <span className="font-semibold text-white">{item.val}/100</span>
                          </div>
                          <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-700"
                              style={{ width: `${item.val}%`, background: item.color }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {reportMarkdown && (
                  <div className="border border-white/[0.05] rounded-xl p-4 bg-slate-950/40">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Coach's Assessment
                    </h3>
                    <p className="text-slate-300 text-xs leading-relaxed line-clamp-4 whitespace-pre-wrap">
                      {reportMarkdown}
                    </p>
                  </div>
                )}

                <SkillGapBadges presentSkills={presentSkills} missingSkills={missingSkills} hasJd={hasJd} />
              </div>
            )}

            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">{error}</div>
            )}
          </motion.div>

          {/* Activity Chart */}
          <motion.div
            variants={fadeUp} custom={7} initial="hidden" animate="show"
            className="lg:col-span-2 bg-slate-900/50 border border-white/[0.06] rounded-2xl p-6 backdrop-blur-sm flex flex-col"
          >
            <h2 className="text-base font-bold text-white mb-1 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" /> Weekly Activity
            </h2>
            <p className="text-xs text-slate-500 mb-5">Score trend over the past week</p>
            <div className="flex-1 min-h-[180px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={activityData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4CC9F0" stopOpacity={0.18} />
                      <stop offset="95%" stopColor="#4CC9F0" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.03)" vertical={false} />
                  <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} domain={[0, 100]} />
                  <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(76,201,240,0.15)', strokeWidth: 1 }} />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#4CC9F0"
                    strokeWidth={2}
                    fill="url(#areaGrad)"
                    dot={{ fill: '#4CC9F0', r: 3, strokeWidth: 0 }}
                    activeDot={{ fill: '#4CC9F0', r: 5, strokeWidth: 0 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        </div>

        {/* ── Interview History ── */}
        <motion.section variants={fadeUp} custom={8} initial="hidden" animate="show">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Mic className="w-4 h-4 text-violet-400" /> Interview History
            </h2>
            <button
              onClick={() => navigate('/interview')}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
            >
              Start New <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          {interviews.length === 0 ? (
            <div className="bg-slate-900/40 border border-white/[0.04] rounded-2xl p-8 text-center">
              <div className="p-4 rounded-2xl bg-slate-800/40 inline-flex mb-3">
                <Mic className="w-6 h-6 text-slate-500" />
              </div>
              <p className="text-slate-400 text-sm mb-2">No mock interviews yet</p>
              <button
                onClick={() => navigate('/interview')}
                className="text-xs font-semibold text-violet-400 hover:text-violet-300 transition-colors"
              >
                Start practicing →
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {interviews.map((interview, i) => (
                <motion.div
                  key={interview.session_id}
                  variants={fadeUp} custom={i * 0.3 + 9} initial="hidden" animate="show"
                  className="bg-slate-900/40 border border-white/[0.05] hover:border-violet-500/30 rounded-2xl p-5 transition-all duration-300 hover:-translate-y-0.5 group"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-sm text-white capitalize">{interview.domain}</h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {new Date(interview.completed_at || Date.now()).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      interview.status === 'completed'
                        ? 'bg-emerald-500/15 text-emerald-400'
                        : 'bg-amber-500/15 text-amber-400'
                    }`}>
                      {interview.status}
                    </span>
                  </div>
                  {interview.status === 'completed' && (
                    <>
                      <div className="flex items-center justify-between border-t border-white/[0.04] pt-3 mt-3">
                        <span className="text-xs text-slate-400">Score</span>
                        <span className="text-lg font-bold text-white">{interview.overall_score ?? '--'}<span className="text-slate-500 text-xs">/100</span></span>
                      </div>
                      <button
                        onClick={() => navigate('/report', { state: { report: { overall_score: interview.overall_score } } })}
                        className="mt-3 w-full py-2 text-xs font-medium text-center bg-slate-800/40 hover:bg-slate-700/40 rounded-xl transition-colors text-slate-300 hover:text-white"
                      >
                        View Report
                      </button>
                    </>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </motion.section>

        {/* ── AI Recommendations ── */}
        {recommendations.length > 0 && (
          <motion.section variants={fadeUp} custom={10} initial="hidden" animate="show">
            <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" /> AI Recommendations
            </h2>
            <div className="bg-slate-900/40 border border-white/[0.05] rounded-2xl p-6">
              <RecommendationList recommendations={recommendations} />
            </div>
          </motion.section>
        )}

      </main>
    </div>
  );
}