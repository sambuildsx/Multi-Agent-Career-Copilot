import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, LogOut } from 'lucide-react';
import GooeyNav from './GooeyNav';

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Analyze', href: '/analyze' },
  { label: 'Interview', href: '/interview' },
];

export default function NavBar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    navigate('/login');
  };

  return (
    <header className="fixed top-4 left-4 right-4 md:left-6 md:right-6 z-50 flex items-center justify-between px-6 py-3 rounded-2xl bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 shadow-xl shadow-black/30">
      {/* Logo */}
      <div
        className="flex items-center space-x-2 cursor-pointer flex-shrink-0"
        onClick={() => navigate('/dashboard')}
      >
        <div className="p-1.5 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-lg shadow shadow-blue-500/20">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <span className="text-sm font-black tracking-widest text-white hidden sm:block">UPSTRIDE</span>
      </div>

      {/* Centered GooeyNav */}
      <div className="absolute left-1/2 -translate-x-1/2">
        <GooeyNav
          items={NAV_ITEMS}
          particleCount={6}
          particleDistances={[70, 8]}
          particleR={80}
          animationTime={600}
          timeVariance={150}
          colors={[1, 1, 2, 2, 3, 3]}
        />
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="flex items-center space-x-1.5 text-slate-400 hover:text-slate-200 transition-colors flex-shrink-0 text-sm font-medium"
      >
        <LogOut className="w-4 h-4" />
        <span className="hidden sm:block">Sign Out</span>
      </button>
    </header>
  );
}