import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import NavBar from '../../components/shared/NavBar';
import {
  ArrowLeft, Zap, ExternalLink, Briefcase, MapPin, Building2,
  ChevronRight, ChevronLeft, Loader2, Search,
  Wifi, WifiOff, DollarSign, Calendar
} from 'lucide-react';
import api from '../../api';



// ─────────────────────────────────────────────────────────────────────────────
// Job Card
// ─────────────────────────────────────────────────────────────────────────────
function JobCard({ job }) {
  const formatSalary = (min, max) => {
    if (!min && !max) return null;
    const fmt = (n) =>
      n >= 100000
        ? `₹${(n / 100000).toFixed(1)}L`
        : `₹${n.toLocaleString()}`;
    if (min && max) return `${fmt(min)} – ${fmt(max)}`;
    if (min) return `From ${fmt(min)}`;
    return `Up to ${fmt(max)}`;
  };

  const formatDate = (iso) => {
    if (!iso) return null;
    try {
      return new Date(iso).toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric',
      });
    } catch {
      return null;
    }
  };

  const salary = formatSalary(job.salary_min, job.salary_max);
  const posted = formatDate(job.created);

  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-700/50 hover:border-blue-500/40 transition-all duration-300 group hover:shadow-[0_0_24px_rgba(59,130,246,0.10)] flex flex-col gap-4">
      {/* Header */}
      <div className="flex-1">
        <h3 className="text-base font-bold text-white leading-snug group-hover:text-blue-300 transition-colors mb-2">
          {job.title || '—'}
        </h3>
        <div className="flex items-center gap-1.5 mb-1 text-sm text-slate-300">
          <Building2 className="w-3.5 h-3.5 shrink-0 text-slate-500" />
          <span className="truncate">{job.company || 'Unknown company'}</span>
        </div>
        <div className="flex items-center gap-1.5 mb-1 text-sm text-slate-500">
          <MapPin className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">{job.location || 'Location not specified'}</span>
        </div>
        {salary && (
          <div className="flex items-center gap-1.5 text-sm text-emerald-400">
            <DollarSign className="w-3.5 h-3.5 shrink-0" />
            <span>{salary}</span>
          </div>
        )}
      </div>

      {/* Description */}
      {job.description && (
        <p className="text-sm text-slate-400 leading-relaxed">
          {job.description}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-700/40 gap-3">
        {posted ? (
          <div className="flex items-center gap-1 text-xs text-slate-500">
            <Calendar className="w-3 h-3" />
            <span>{posted}</span>
          </div>
        ) : (
          <span />
        )}
        <button
          onClick={() => window.open(job.apply_now_url || job.redirect_url, "_blank")}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/15 border border-blue-500/30 text-blue-300 text-sm font-semibold hover:bg-blue-500/25 hover:border-blue-500/50 transition-all duration-200 group/btn shrink-0"
        >
          Apply
          <ExternalLink className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Roles available for no-JD career track selector
// ─────────────────────────────────────────────────────────────────────────────
const CAREER_TRACKS = [
  'Backend Developer',
  'Frontend Developer',
  'Full Stack Developer',
  'AI Engineer',
  'Data Scientist',
];

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────
export default function JobsPage() {
  const { jobId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  // Context passed from ReportPage
  const hasJd = location.state?.hasJd ?? false;

  // ── Filters ────────────────────────────────────────────────────────────────
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [remote, setRemote] = useState(false);
  const [locationInput, setLocationInput] = useState('');
  const [resultsPerPage] = useState(20);
  const [page, setPage] = useState(1);
  const [careerTrack, setCareerTrack] = useState('');

  // ── Data ───────────────────────────────────────────────────────────────────
  const [role, setRole] = useState('');
  const [secondaryRoles, setSecondaryRoles] = useState([]);
  const [apiJobs, setApiJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);

  // ── Fetch ──────────────────────────────────────────────────────────────────
  const fetchJobs = useCallback(
    async (overridePage = page) => {
      if (!jobId) return;
      setIsLoading(true);
      try {
        const params = {
          employment_type: selectedFilter === 'all' ? 'fulltime' : selectedFilter,
          remote,
          results_per_page: resultsPerPage,
          page: overridePage,
        };
        if (locationInput.trim()) params.location = locationInput.trim();
        if (careerTrack) params.career_track = careerTrack;

        const res = await api.get(`/jobs/${jobId}`, { params });

        setRole(res.data.role || '');
        setSecondaryRoles(res.data.secondary_roles || []);
        setApiJobs(res.data.jobs || []);
        setHasFetched(true);
      } catch (err) {
        // Fallback to demo mode quietly on error
        setHasFetched(true);
      } finally {
        setIsLoading(false);
      }
    },
    [jobId, selectedFilter, remote, resultsPerPage, page, locationInput, careerTrack]
  );

  // Initial fetch on mount only
  useEffect(() => {
    fetchJobs(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFind = () => {
    setPage(1);
    fetchJobs(1);
  };

  const goToPage = (newPage) => {
    if (newPage < 1) return;
    setPage(newPage);
    fetchJobs(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStartInterview = () => {
    navigate('/interview', {
      state: {
        interviewMode: hasJd ? 'Resume + JD Interview' : 'Resume-Based Interview',
        autoStart: true,
      },
    });
  };

  if (!jobId) {
    navigate('/analyze', { replace: true });
    return null;
  }

  // ── Filtering DEMO / Real jobs ─────────────────────────────────────────────
  const isDemo = hasFetched && apiJobs.length === 0;
  const currentJobs = isDemo ? DEMO_JOBS : apiJobs;

  const filteredJobs = currentJobs.filter((job) => {
    if (selectedFilter === "all") return true;
    if (job.type) return job.type === selectedFilter;
    return true; // Fallback for real API jobs without a type
  });

  // Real jobs default to recommended if featured is not explicitly false
  const recommendedJobs = filteredJobs.filter(job => job.featured !== false);
  const moreJobs = filteredJobs.filter(job => job.featured === false);

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-blue-500/8 rounded-full blur-[120px] -z-10 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-indigo-500/8 rounded-full blur-[120px] -z-10 pointer-events-none" />

      <NavBar />

      <main className="flex-1 p-6 z-10 max-w-7xl mx-auto w-full space-y-8 pt-20">

        {/* ── Header nav ── */}
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to Report</span>
          </button>
          <button
            id="btn-jobs-practice-interview"
            onClick={handleStartInterview}
            className="btn-primary flex items-center gap-2 py-2.5 px-5 text-sm"
          >
            <Zap className="w-4 h-4" />
            Practice Interview
            <ChevronRight className="w-4 h-4" />
          </button>
        </header>

        {/* ── Page title ── */}
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-blue-500/15 flex items-center justify-center border border-blue-500/25 shadow-[0_0_20px_rgba(59,130,246,0.15)]">
            <Briefcase className="w-8 h-8 text-blue-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Find Opportunities</h1>
            <p className="text-slate-400 text-sm mt-0.5">
              Matched to your resume {hasJd ? 'and job description' : 'profile'}
            </p>
          </div>
        </div>

        {/* ── Inferred role pills ── */}
        {(role || secondaryRoles.length > 0) && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-1.5 text-slate-400 text-sm">
              <Search className="w-3.5 h-3.5" />
              Inferred role:
            </span>
            {role && (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/15 border border-indigo-500/25 text-indigo-300">
                {role}
              </span>
            )}
            {secondaryRoles.map((r, i) => (
              <span
                key={i}
                className="px-3 py-1 rounded-full text-xs font-medium bg-slate-800/60 border border-slate-700/50 text-slate-400"
              >
                {r}
              </span>
            ))}
          </div>
        )}

        {/* ── Filters panel ── */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-700/40 space-y-6">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Filters</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {/* Employment type */}
            <div>
              <p className="text-xs font-medium text-slate-400 mb-2">Employment Type</p>
              <div className="flex gap-2">
                {[
                  { id: 'all', label: 'All' },
                  { id: 'full-time', label: 'Full-time' },
                  { id: 'internship', label: 'Internship' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setSelectedFilter(opt.id)}
                    className={`flex-1 py-2 rounded-xl border text-sm font-medium transition-all ${
                      selectedFilter === opt.id
                        ? 'border-blue-500 bg-blue-500/15 text-blue-300'
                        : 'border-slate-700/50 bg-slate-900/40 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Location */}
            <div>
              <p className="text-xs font-medium text-slate-400 mb-2">Location</p>
              <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-700/50 rounded-xl px-3 py-2.5 focus-within:border-blue-500/60 transition-colors">
                <MapPin className="w-4 h-4 text-slate-500 shrink-0" />
                <input
                  type="text"
                  placeholder="Bangalore, Mumbai, Remote…"
                  value={locationInput}
                  onChange={(e) => setLocationInput(e.target.value)}
                  className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600 focus:outline-none"
                />
              </div>
            </div>

            {/* Remote toggle */}
            <div>
              <p className="text-xs font-medium text-slate-400 mb-2">Work Mode</p>
              <button
                onClick={() => setRemote((v) => !v)}
                className={`flex items-center gap-2 w-full py-2.5 px-4 rounded-xl border text-sm font-medium transition-all ${
                  remote
                    ? 'border-emerald-500 bg-emerald-500/10 text-emerald-300'
                    : 'border-slate-700/50 bg-slate-900/40 text-slate-400 hover:border-slate-600'
                }`}
              >
                {remote ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                {remote ? 'Remote only' : 'Any mode'}
              </button>
            </div>
          </div>

          {/* Career track override (no-JD mode) */}
          {!hasJd && (
            <div>
              <p className="text-xs font-medium text-slate-400 mb-3">
                Recommended Career Tracks
                <span className="text-slate-600 ml-1">(pre-selected from your resume)</span>
              </p>
              <div className="flex flex-wrap gap-2">
                {CAREER_TRACKS.map((track) => {
                  const isActive = (careerTrack || role) === track;
                  return (
                    <label
                      key={track}
                      className={`flex items-center gap-2 cursor-pointer px-4 py-2 rounded-xl border text-sm font-medium transition-all ${
                        isActive
                          ? 'border-indigo-500 bg-indigo-500/15 text-indigo-300'
                          : 'border-slate-700/50 bg-slate-900/40 text-slate-400 hover:border-slate-600'
                      }`}
                    >
                      <input
                        type="radio"
                        name="career_track"
                        value={track}
                        checked={isActive}
                        onChange={() => setCareerTrack(track)}
                        className="sr-only"
                      />
                      {track}
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          {/* Find button */}
          <button
            id="btn-find-opportunities"
            onClick={handleFind}
            disabled={isLoading}
            className="btn-primary flex items-center gap-2 px-6 py-3 disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            Find Opportunities
          </button>
        </div>

        {/* ── LOADING ── */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-24 gap-4 text-slate-400">
            <Loader2 className="w-10 h-10 animate-spin text-blue-400" />
            <p className="text-sm font-medium">Finding relevant openings…</p>
            <p className="text-xs text-slate-600">Searching Adzuna for matching roles</p>
          </div>
        )}

        {/* ── Jobs grid ── */}
        {!isLoading && hasFetched && (
          <>
            <div>
              <p className="text-xs text-slate-500 mb-4">
                Showing {filteredJobs.length} result{filteredJobs.length !== 1 ? 's' : ''} for{' '}
                <span className="text-slate-300 font-medium">{role || careerTrack}</span>
                {selectedFilter === 'internship' ? ' internships' : (selectedFilter === 'full-time' ? ' full-time roles' : ' opportunities')}
                {locationInput ? ` in ${locationInput}` : ''}
                {remote ? ', remote' : ''}
                {isDemo && <span className="ml-2 px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px] font-bold tracking-wider uppercase">Demo Mode</span>}
              </p>
              
              {recommendedJobs.length > 0 && (
                <div className="mb-10">
                  <h2 className="text-xl font-bold text-white mb-5 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-amber-400" />
                    Recommended Jobs
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                    {recommendedJobs.map((job, i) => (
                      <JobCard key={`${job.redirect_url || job.apply_now_url}-${i}`} job={job} />
                    ))}
                  </div>
                </div>
              )}

              {moreJobs.length > 0 && (
                <div>
                  <h2 className="text-xl font-bold text-white mb-5 border-t border-slate-700/50 pt-8">
                    More Opportunities
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 opacity-80">
                    {moreJobs.map((job, i) => (
                      <JobCard key={`${job.redirect_url || job.apply_now_url}-${i}`} job={job} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* ── Pagination (Only if not demo) ── */}
            {!isDemo && (
              <div className="flex items-center justify-center gap-4 pt-4">
                <button
                  id="btn-prev-page"
                  onClick={() => goToPage(page - 1)}
                  disabled={page <= 1 || isLoading}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700/50 text-slate-400 text-sm font-medium hover:border-slate-600 hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>
                <span className="text-sm text-slate-500">Page {page}</span>
                <button
                  id="btn-next-page"
                  onClick={() => goToPage(page + 1)}
                  disabled={apiJobs.length < resultsPerPage || isLoading}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700/50 text-slate-400 text-sm font-medium hover:border-slate-600 hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
