import React, { useState } from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Trophy, Award, AlertTriangle, Zap, LayoutDashboard, ChevronRight,
  Cpu, Monitor, BrainCircuit, Code2, Briefcase, BarChart3,
} from 'lucide-react';
import NavBar from '../../components/shared/NavBar';
import CursorGrid from '../../components/shared/CursorGrid';
import SkillGapBadges from '../../components/optimizer/SkillGapBadges';
import RecommendationCards from '../../components/report/RecommendationCards';
import LearningRoadmap from '../../components/report/LearningRoadmap';
import MagicBento from '../../components/shared/MagicBento';
import {
  ScoreTrendCard, SkillsRadarCard, CompletenessBarCard, CompletenessRingCard,
} from '../../components/report/AnalyticsCards';

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.45, delay: i * 0.06, ease: [0.25, 0.46, 0.45, 0.94] },
  }),
};

const DEFAULT_ROADMAP = [
  'Resume Analysis',
  'Missing Skills',
  'Recommended Projects',
  'Mock Interviews',
  'Apply for Jobs',
];

export default function ReportPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const report = location.state?.report;
  const jobId = location.state?.jobId ?? report?.job_id;
  const hasJd = location.state?.hasJd ?? Boolean(report?.has_jd_analysis);

  const DOMAINS = [
    { id: 'Backend Engineer', label: 'Backend', icon: Cpu },
    { id: 'Frontend Engineer', label: 'Frontend', icon: Monitor },
    { id: 'System Design', label: 'System Design', icon: BrainCircuit },
    { id: 'Data Structures & Algorithms', label: 'DSA', icon: Code2 },
  ];

  const [selectedMode, setSelectedMode] = useState(hasJd ? 'Resume + JD Interview' : 'Resume-Based Interview');
  const [selectedDomain, setSelectedDomain] = useState('Backend Engineer');

  const INTERVIEW_MODES = [
    { id: 'Generic Interview', label: 'Generic Mock', desc: 'Standard technical interview by domain' },
    { id: 'Resume-Based Interview', label: 'Resume-Based', desc: 'Questions based on your resume projects & skills' },
    ...(hasJd ? [{ id: 'Resume + JD Interview', label: 'Resume + JD', desc: 'Prioritizes ATS gaps & role-specific skills' }] : []),
  ];

  const handleStartInterview = () => {
    navigate('/interview', {
      state: {
        interviewMode: selectedMode,
        targetDomain: selectedMode === 'Generic Interview' ? selectedDomain : null,
        autoStart: true,
      },
    });
  };

  // Redirect if accessed directly without report data
  if (!report) {
    return <Navigate to="/dashboard" replace />;
  }

  const presentSkills = report.matched_technologies || report.present_skills || [];
  const missingSkills = report.missing_skills || [];
  const roadmapSteps = report.learning_roadmap?.length > 0 ? report.learning_roadmap : DEFAULT_ROADMAP;

  const scoreBreakdown = [
    { label: 'Overall', score: report.overall_score ?? 0 },
    { label: 'Resume', score: report.resume_score ?? 0 },
    { label: 'Interview', score: report.interview_score ?? 0 },
  ].filter((d) => d.score !== null && d.score !== undefined);

  const radarData = [
    { skill: 'Keywords', value: report.keyword_match_score ?? report.resume_score ?? 0 },
    { skill: 'Required Skills', value: report.required_skills_match ?? (presentSkills.length ? Math.min(100, presentSkills.length * 12) : 0) },
    { skill: 'Completeness', value: report.completeness_score ?? report.overall_score ?? 0 },
    { skill: 'Relevance', value: report.project_relevance_score ?? report.resume_score ?? 0 },
  ];

  const sectionBars = [
    { section: 'Strengths', value: Math.min(100, (report.strengths?.length || 0) * 20) },
    { section: 'Skills Matched', value: Math.min(100, presentSkills.length * 12) },
    { section: 'Gaps to Close', value: Math.min(100, missingSkills.length * 12) },
    { section: 'Recommendations', value: Math.min(100, (report.recommendations?.length || 0) * 20) },
  ];

  const overallPct = report.overall_score ?? report.resume_score ?? 0;

  const bentoCards = [
    { content: <ScoreTrendCard title="Score Breakdown" data={scoreBreakdown.map(d => ({ label: d.label, score: d.score }))} /> },
    { content: <SkillsRadarCard data={radarData} /> },
    { content: <CompletenessBarCard data={sectionBars} /> },
    { content: <CompletenessRingCard percentage={overallPct} /> },
  ];

  return (
    <div
      className="min-h-screen text-slate-100 relative overflow-x-hidden"
      style={{ background: 'linear-gradient(180deg, #060b16 0%, #0b1220 100%)' }}
    >
      <div className="fixed inset-0 z-0 pointer-events-none md:pointer-events-auto">
        <CursorGrid
          cellSize={85} color="#4CC9F0" radius={120} falloff="smooth"
          holdTime={300} fadeDuration={700} lineWidth={0.8} maxOpacity={0.4}
          fillOpacity={0} gridOpacity={0.05} cellRadius={8} clickPulse={false}
        />
      </div>
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-blue-600/5 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="fixed bottom-0 right-0 w-[500px] h-[400px] bg-indigo-600/5 rounded-full blur-[100px] pointer-events-none z-0" />

      <NavBar />

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 pt-24 pb-16 space-y-8">
        <motion.header variants={fadeUp} custom={0} initial="hidden" animate="show" className="flex justify-between items-center">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center space-x-2 text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back</span>
          </button>
        </motion.header>

        <motion.div variants={fadeUp} custom={1} initial="hidden" animate="show" className="flex items-center space-x-4">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
            <Trophy className="w-8 h-8 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Career Report</h1>
            <p className="text-slate-400">Comprehensive AI Evaluation</p>
          </div>
        </motion.div>

        {/* ── Main grid: scores/strengths/weaknesses (left) + interview & jobs CTA (right) ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div variants={fadeUp} custom={2} initial="hidden" animate="show" className="lg:col-span-2 space-y-6">
            {/* Scores */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Overall', value: report.overall_score, border: 'border-t-indigo-500' },
                { label: 'Resume', value: report.resume_score, border: 'border-t-emerald-500' },
                { label: 'ATS', value: report.ats_score ?? report.keyword_match_score, border: 'border-t-cyan-500' },
              ].filter(s => s.value !== null && s.value !== undefined).map(s => (
                <div key={s.label} className={`glass-card p-5 border-t-2 ${s.border} flex flex-col items-center justify-center`}>
                  <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">{s.label}</span>
                  <span className="text-4xl font-bold text-white">{s.value}</span>
                </div>
              ))}
            </div>

            {report.markdown && (
              <div className="glass-panel p-6">
                <h3 className="text-xl font-semibold mb-4 text-slate-200">Coach Summary</h3>
                <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">{report.markdown}</p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="glass-panel p-6 border-l-4 border-l-emerald-500">
                <h3 className="font-semibold text-emerald-400 mb-3 flex items-center gap-2">
                  <Award className="w-5 h-5" /> Strengths
                </h3>
                <ul className="space-y-2 text-sm text-slate-300">
                  {report.strengths?.map((item, idx) => (
                    <li key={idx} className="flex gap-2"><span className="text-emerald-500 mt-0.5">•</span><span>{item}</span></li>
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
                    <li key={idx} className="flex gap-2"><span className="text-rose-500 mt-0.5">•</span><span>{item}</span></li>
                  ))}
                  {(!report.weaknesses || report.weaknesses.length === 0) && (
                    <li className="italic text-slate-500">No areas to improve identified.</li>
                  )}
                </ul>
              </div>
            </div>

            <SkillGapBadges presentSkills={presentSkills} missingSkills={missingSkills} hasJd={Boolean(report.has_jd_analysis)} />
          </motion.div>

          {/* ── Right sidebar: Start Interview + Find Jobs ── */}
          <motion.div variants={fadeUp} custom={3} initial="hidden" animate="show" className="lg:col-span-1 space-y-4">
            <div className="glass-panel p-6 border border-indigo-500/20 rounded-2xl space-y-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                  <Zap className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                  <h2 className="text-base font-bold">Ready for your interview?</h2>
                  <p className="text-xs text-slate-400">Choose a mode, then launch</p>
                </div>
              </div>

              <div className="space-y-2">
                {INTERVIEW_MODES.map((m) => {
                  const active = selectedMode === m.id;
                  return (
                    <button
                      key={m.id}
                      id={`mode-${m.id.replace(/\s+/g, '-').toLowerCase()}`}
                      onClick={() => setSelectedMode(m.id)}
                      className={`w-full p-3 rounded-xl border text-left transition-all ${
                        active
                          ? 'border-indigo-500 bg-indigo-500/10 shadow-[0_0_15px_rgba(99,102,241,0.15)]'
                          : 'border-slate-700/50 bg-slate-900/40 hover:border-slate-600'
                      }`}
                    >
                      <p className={`font-semibold text-xs ${active ? 'text-indigo-300' : 'text-slate-200'}`}>{m.label}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">{m.desc}</p>
                    </button>
                  );
                })}
              </div>

              {selectedMode === 'Generic Interview' && (
                <div className="flex flex-wrap gap-2">
                  {DOMAINS.map((d) => {
                    const Icon = d.icon;
                    const active = selectedDomain === d.id;
                    return (
                      <button
                        key={d.id}
                        id={`domain-${d.id.replace(/\s+/g, '-').toLowerCase()}`}
                        onClick={() => setSelectedDomain(d.id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                          active
                            ? 'border-indigo-500 bg-indigo-500/15 text-indigo-300'
                            : 'border-slate-700/50 bg-slate-900/40 text-slate-400 hover:border-slate-600'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        {d.label}
                      </button>
                    );
                  })}
                </div>
              )}

              <button
                id="btn-start-interview"
                onClick={handleStartInterview}
                className="btn-primary w-full flex items-center justify-center gap-2 py-3"
              >
                <Zap className="w-4 h-4" />
                Start Interview
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {jobId && (
              <button
                id="btn-find-opportunities"
                onClick={() => navigate(`/jobs/${jobId}`, { state: { hasJd } })}
                className="btn-secondary w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl"
              >
                <Briefcase className="w-4 h-4" />
                Find Opportunities
              </button>
            )}

            <button
              id="btn-skip-interview"
              onClick={() => navigate('/dashboard')}
              className="btn-secondary w-full flex items-center justify-center gap-2 py-3 rounded-2xl"
            >
              <LayoutDashboard className="w-4 h-4" />
              Skip to Dashboard
            </button>
          </motion.div>
        </div>

        {/* ── Actionable recommendations ── */}
        <motion.div variants={fadeUp} custom={4} initial="hidden" animate="show">
          <RecommendationCards recommendations={report.recommendations || []} />
        </motion.div>

        {/* ── Learning roadmap ── */}
        <motion.div variants={fadeUp} custom={5} initial="hidden" animate="show">
          <LearningRoadmap steps={roadmapSteps} />
        </motion.div>

        {/* ── Graphs / Analytics ── */}
        <motion.div variants={fadeUp} custom={6} initial="hidden" animate="show">
          <h3 className="font-semibold text-lg mb-4 text-slate-200 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" /> Analytics
          </h3>
          <MagicBento
            cards={bentoCards}
            enableStars
            enableSpotlight
            enableBorderGlow
            clickEffect
            spotlightRadius={250}
            particleCount={8}
            glowColor="76, 201, 240"
          />
        </motion.div>
      </main>
    </div>
  );
}