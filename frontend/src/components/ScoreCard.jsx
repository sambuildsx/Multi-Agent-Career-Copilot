import React from 'react';
import { Target, TrendingUp, AlertTriangle } from 'lucide-react';

export default function ScoreCard({ score, category = "Overall Match" }) {
  // Determine colors based on score
  let scoreColor = "from-red-500 to-rose-600";
  let bgGlow = "shadow-red-500/20";
  let Icon = AlertTriangle;
  
  if (score >= 80) {
    scoreColor = "from-emerald-400 to-teal-500";
    bgGlow = "shadow-emerald-500/20";
    Icon = Target;
  } else if (score >= 60) {
    scoreColor = "from-amber-400 to-orange-500";
    bgGlow = "shadow-amber-500/20";
    Icon = TrendingUp;
  }

  return (
    <div className={`glass-card p-6 flex flex-col items-center justify-center relative overflow-hidden group`}>
      {/* Background glow effect */}
      <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 rounded-full blur-3xl opacity-20 bg-gradient-to-tr ${scoreColor} transition-opacity duration-500 group-hover:opacity-40`}></div>
      
      <div className="relative z-10 flex flex-col items-center">
        <div className="flex items-center space-x-2 mb-2 text-slate-400">
          <Icon className="w-4 h-4" />
          <span className="text-sm font-medium uppercase tracking-wider">{category}</span>
        </div>
        
        <div className="flex items-baseline space-x-1">
          <span className={`text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r ${scoreColor}`}>
            {score}
          </span>
          <span className="text-xl text-slate-500 font-medium">/100</span>
        </div>
        
        {/* Simple Progress Bar */}
        <div className="w-full h-1.5 bg-slate-800 rounded-full mt-4 overflow-hidden">
          <div 
            className={`h-full bg-gradient-to-r ${scoreColor} rounded-full transition-all duration-1000 ease-out`}
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
    </div>
  );
}
