import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Target, 
  Mic, 
  Briefcase, 
  ArrowRight, 
  Sparkles, 
  CheckCircle,
  TrendingUp,
  Award,
  Layers,
  ArrowUpRight
} from 'lucide-react';
import { HexagonBackground } from '@/components/animate-ui/components/backgrounds/hexagon';

export default function LandingPage() {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/dashboard');
    } else {
      navigate('/signup');
    }
  };

  const handleExploreDemo = () => {
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative overflow-hidden font-sans">
      {/* Subtle Hexagon Background Wrapper with radial glow mask */}
      <div className="absolute inset-0 z-0">
        <HexagonBackground 
          hexagonSize={64} 
          hexagonMargin={2} 
          className="absolute inset-0 bg-slate-950"
        />
        {/* Soft blue glow behind hero section */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none z-0" />
        <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none z-0" />
      </div>

      {/* Header / Navbar */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 py-6 flex justify-between items-center border-b border-white/[0.04] bg-slate-950/40 backdrop-blur-md">
        <div className="flex items-center space-x-3 group cursor-pointer" onClick={() => navigate('/')}>
          <div className="p-2 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform duration-300">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-black tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
            UPSTRIDE
          </span>
        </div>

        <div className="flex items-center space-x-4">
          <button 
            onClick={() => navigate('/login')}
            className="text-sm font-medium text-slate-300 hover:text-white px-4 py-2 rounded-lg transition-colors"
          >
            Login
          </button>
          <button 
            onClick={() => navigate('/signup')}
            className="text-sm font-medium bg-white/5 hover:bg-white/10 text-white border border-white/10 hover:border-white/20 px-5 py-2 rounded-lg transition-all shadow-md active:scale-95"
          >
            Sign Up
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto px-6 py-12 lg:py-24 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Hero Column */}
        <div className="lg:col-span-7 flex flex-col space-y-8 text-left">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold w-fit tracking-wide uppercase animate-pulse-slow">
            <Award className="w-3.5 h-3.5" />
            <span>Next-Gen Career Copilot</span>
          </div>

          <div className="space-y-4">
            <h1 className="text-6xl sm:text-7xl font-extrabold tracking-tight text-white leading-none">
              UPSTRIDE
            </h1>
            <p className="text-2xl sm:text-3xl font-medium text-slate-300 tracking-tight leading-relaxed max-w-xl">
              Everything You Need to Land Your Next Opportunity.
            </p>
          </div>

          <p className="text-base text-slate-400 max-w-lg leading-relaxed">
            Upload your resume, analyze alignment with job descriptions, run simulated mock interviews, and find highly relevant career paths driven by advanced AI agents.
          </p>

          <div className="flex flex-wrap gap-4 pt-2">
            <button 
              onClick={handleGetStarted}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all duration-300 hover:translate-y-[-2px] active:translate-y-[0px] flex items-center space-x-2 group"
            >
              <span>Get Started</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button 
              onClick={handleExploreDemo}
              className="px-8 py-4 bg-slate-900/80 hover:bg-slate-800/80 text-slate-200 hover:text-white font-semibold rounded-xl border border-slate-800 hover:border-slate-700 transition-all duration-300 hover:translate-y-[-2px] active:translate-y-[0px]"
            >
              Explore Demo
            </button>
          </div>
        </div>

        {/* Right Hero Column: Dashboard Preview Card */}
        <div className="lg:col-span-5 relative group">
          {/* Card outer glow */}
          <div className="absolute -inset-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl blur opacity-25 group-hover:opacity-35 transition duration-1000" />
          
          {/* Glass Card */}
          <div className="relative bg-slate-900/80 backdrop-blur-xl border border-white/[0.08] rounded-3xl p-8 shadow-2xl flex flex-col space-y-6 text-left">
            <div className="flex justify-between items-center pb-4 border-b border-white/[0.06]">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-xs font-mono text-slate-500 ml-2">dashboard_preview.json</span>
              </div>
              <span className="text-xs font-semibold bg-blue-500/10 text-blue-400 px-2.5 py-1 rounded-md">Live Preview</span>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-4">
              {/* ATS Score */}
              <div className="bg-white/[0.02] border border-white/[0.04] p-4 rounded-2xl flex flex-col items-center justify-center space-y-2 group/item hover:bg-white/[0.04] transition-colors">
                <span className="text-xs text-slate-400 font-medium">ATS Score</span>
                <div className="relative w-20 h-20 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="40" cy="40" r="34" className="stroke-slate-800" strokeWidth="6" fill="transparent" />
                    <circle cx="40" cy="40" r="34" className="stroke-blue-500 animate-pulse-slow" strokeWidth="6" fill="transparent" strokeDasharray="213.6" strokeDashoffset="32" strokeLinecap="round" />
                  </svg>
                  <span className="absolute text-xl font-bold text-white">85%</span>
                </div>
              </div>

              {/* Interview Readiness */}
              <div className="bg-white/[0.02] border border-white/[0.04] p-4 rounded-2xl flex flex-col items-center justify-center space-y-2 group/item hover:bg-white/[0.04] transition-colors">
                <span className="text-xs text-slate-400 font-medium">Readiness</span>
                <div className="relative w-20 h-20 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="40" cy="40" r="34" className="stroke-slate-800" strokeWidth="6" fill="transparent" />
                    <circle cx="40" cy="40" r="34" className="stroke-emerald-500" strokeWidth="6" fill="transparent" strokeDasharray="213.6" strokeDashoffset="42" strokeLinecap="round" />
                  </svg>
                  <span className="absolute text-xl font-bold text-white">80%</span>
                </div>
              </div>
            </div>

            {/* Opportunities Found */}
            <div className="bg-white/[0.02] border border-white/[0.04] p-4 rounded-2xl flex items-center justify-between hover:bg-white/[0.04] transition-colors">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-blue-500/10 rounded-xl text-blue-400">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-slate-400 font-medium">Opportunities Found</span>
                  <span className="text-base font-bold text-white">12 Match Matches</span>
                </div>
              </div>
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1 hover:text-white cursor-pointer">
                View All <ArrowUpRight className="w-3 h-3" />
              </span>
            </div>

            {/* Resume Insights */}
            <div className="space-y-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Resume Insights</span>
              <div className="space-y-2">
                <div className="flex items-start space-x-2.5 text-xs text-slate-300">
                  <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span>Strong technical skills matching modern stack (React, Node, PyTorch)</span>
                </div>
                <div className="flex items-start space-x-2.5 text-xs text-slate-300">
                  <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span>Quantifiable achievements listed in leadership sections</span>
                </div>
                <div className="flex items-start space-x-2.5 text-xs text-slate-300">
                  <CheckCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                  <span>Enhance project details for Cloud Deployment architectures</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Feature Flow Section */}
      <section className="relative z-10 w-full max-w-7xl mx-auto px-6 py-16 lg:py-24 border-t border-white/[0.04]">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mb-3">
            Accelerated Job Search Pipeline
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-sm sm:text-base">
            Our multi-agent system runs sequentially to align your profile from draft to offer.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
          {/* Step 1 */}
          <div className="bg-slate-900/60 backdrop-blur border border-white/[0.05] p-6 rounded-2xl flex flex-col items-center text-center space-y-4 hover:border-blue-500/30 hover:bg-slate-900/80 transition-all duration-300 group">
            <div className="p-3 bg-blue-500/10 rounded-2xl text-blue-400 group-hover:scale-110 transition-transform">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">📄 Resume Analysis</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Deep semantic scan extracting key achievements and credentials.
            </p>
          </div>

          {/* Step 2 */}
          <div className="bg-slate-900/60 backdrop-blur border border-white/[0.05] p-6 rounded-2xl flex flex-col items-center text-center space-y-4 hover:border-blue-500/30 hover:bg-slate-900/80 transition-all duration-300 group">
            <div className="p-3 bg-blue-500/10 rounded-2xl text-blue-400 group-hover:scale-110 transition-transform">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">🎯 ATS Optimization</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Compare directly to job description keywords and scoring weights.
            </p>
          </div>

          {/* Step 3 */}
          <div className="bg-slate-900/60 backdrop-blur border border-white/[0.05] p-6 rounded-2xl flex flex-col items-center text-center space-y-4 hover:border-blue-500/30 hover:bg-slate-900/80 transition-all duration-300 group">
            <div className="p-3 bg-blue-500/10 rounded-2xl text-blue-400 group-hover:scale-110 transition-transform">
              <Mic className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">🎤 Mock Interview</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Interactive simulator to refine responses based on target role JDs.
            </p>
          </div>

          {/* Step 4 */}
          <div className="bg-slate-900/60 backdrop-blur border border-white/[0.05] p-6 rounded-2xl flex flex-col items-center text-center space-y-4 hover:border-blue-500/30 hover:bg-slate-900/80 transition-all duration-300 group">
            <div className="p-3 bg-blue-500/10 rounded-2xl text-blue-400 group-hover:scale-110 transition-transform">
              <Briefcase className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">💼 Job Opportunities</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Tailored match rankings with live links to hiring platforms.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 w-full max-w-7xl mx-auto px-6 py-8 mt-auto border-t border-white/[0.04] flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500">
        <span>© {new Date().getFullYear()} Upstride. All rights reserved.</span>
        <div className="flex space-x-6 mt-4 sm:mt-0">
          <a href="#" className="hover:text-slate-300 transition-colors">Privacy Policy</a>
          <a href="#" className="hover:text-slate-300 transition-colors">Terms of Service</a>
          <a href="#" className="hover:text-slate-300 transition-colors">Contact</a>
        </div>
      </footer>
    </div>
  );
}
