import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ResumeUpload from '../components/ResumeUpload';
import api from '../api';
import { LogOut } from 'lucide-react';

export default function AnalyzePage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const navigate = useNavigate();

  const handleUpload = async (file) => {
    setIsAnalyzing(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/api/v1/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Pass results to dashboard via route state
      navigate('/dashboard', { state: { results: response.data } });
    } catch (error) {
      console.error("Analysis failed:", error);
      alert(error.response?.data?.detail || "An error occurred during analysis. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Background ambient light */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
      
      <header className="p-6 flex justify-between items-center z-10">
        <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
          Recruiter Copilot
        </h2>
        <button 
          onClick={handleLogout}
          className="flex items-center space-x-2 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span className="text-sm font-medium">Sign Out</span>
        </button>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 z-10">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Analyze Candidate</h1>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Upload a candidate's resume to instantly evaluate their fit for the current job description using our AI agents.
          </p>
        </div>

        <div className="w-full relative">
          <ResumeUpload onUpload={handleUpload} isLoading={isAnalyzing} />
          
          {isAnalyzing && (
            <div className="absolute -bottom-16 left-1/2 -translate-x-1/2 flex items-center space-x-3 text-blue-400">
              <span className="flex h-3 w-3 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
              </span>
              <span className="text-sm font-medium">AI Agents are reviewing the profile...</span>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
