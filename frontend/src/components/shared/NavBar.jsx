import React from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { LogOut } from 'lucide-react';

const NAV_LINKS = [
  { path: '/analyze', label: 'Analyze' },
  { path: '/github', label: 'GitHub' },
  { path: '/interview', label: 'Interview' },
  { path: '/dashboard', label: 'Dashboard' },
];

export default function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <header className="p-6 flex justify-between items-center z-10">
      <Link to="/analyze" className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
        Recruiter Copilot
      </Link>

      <nav className="flex items-center space-x-6">
        {NAV_LINKS.map((link) => {
          const isActive = location.pathname === link.path;
          return (
            <Link
              key={link.path}
              to={link.path}
              className={`text-sm font-medium transition-colors ${
                isActive ? 'text-blue-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {link.label}
            </Link>
          );
        })}

        <button
          onClick={handleLogout}
          className="flex items-center space-x-2 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span className="text-sm font-medium">Sign Out</span>
        </button>
      </nav>
    </header>
  );
}