import React, { useState } from 'react';
import { authAPI } from \'../../services/api\';
import { Briefcase, Lock, Mail, ArrowRight, User } from 'lucide-react';

export default function RegisterPage({ onLoginSuccess, navigateToLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) { setError('Please fill in all fields.'); return; }
    if (password.length < 6) { setError('Password must be at least 6 characters.'); return; }
    setError('');
    setLoading(true);
    try {
      await authAPI.register(email, password);
      onLoginSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Try a different email.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[85vh]">
      <div className="w-full max-w-md p-8 glass-panel">
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-indigo-600/10 rounded-2xl border border-indigo-500/20 text-indigo-400 mb-3 animate-pulse-slow">
            <User size={32} />
          </div>
          <h2 className="text-3xl font-extrabold text-white tracking-tight">Create Account</h2>
          <p className="text-sm text-slate-400 mt-2">Join CareerOS and boost your career</p>
        </div>

        {error && (
          <div className="p-3 mb-6 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400 text-sm">
            <span className="font-bold">Error:</span> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3 text-slate-500" size={18} />
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-11 glass-input"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3 text-slate-500" size={18} />
              <input
                type="password"
                placeholder="Min. 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-11 glass-input"
              />
            </div>
          </div>
          <button type="submit" disabled={loading} className="w-full btn-primary flex items-center justify-center gap-2 mt-4">
            {loading ? 'Creating account...' : 'Create Account'}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-slate-400">
          Already have an account?{' '}
          <button onClick={navigateToLogin} className="font-medium text-blue-400 hover:text-blue-300 transition-colors">
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
