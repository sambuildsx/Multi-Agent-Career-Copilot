import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle, Loader, AlertCircle, Clock } from 'lucide-react';

const STATUS_ICON = {
  completed: <CheckCircle size={15} className="text-emerald-400 shrink-0" />,
  running: <Loader size={15} className="text-blue-400 animate-spin shrink-0" />,
  failed: <AlertCircle size={15} className="text-red-400 shrink-0" />,
  pending: <Clock size={15} className="text-slate-500 shrink-0" />,
};

const STATUS_LABEL_CLASSES = {
  completed: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  running: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  failed: 'text-red-400 bg-red-500/10 border-red-500/20',
  pending: 'text-slate-400 bg-slate-800/50 border-slate-700/50',
};

export default function AgentSection({ title, status = 'pending', icon: Icon, accentColor = 'blue', children }) {
  const [open, setOpen] = useState(false);
  const isComplete = status === 'completed';

  const accentBorder = {
    blue: 'border-blue-500/30 hover:border-blue-500/50',
    indigo: 'border-indigo-500/30 hover:border-indigo-500/50',
    purple: 'border-purple-500/30 hover:border-purple-500/50',
    emerald: 'border-emerald-500/30 hover:border-emerald-500/50',
    amber: 'border-amber-500/30 hover:border-amber-500/50',
  };

  const accentIcon = {
    blue: 'text-blue-400',
    indigo: 'text-indigo-400',
    purple: 'text-purple-400',
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
  };

  return (
    <div className={`glass-card border ${accentBorder[accentColor] || accentBorder.blue} transition-all duration-300`}>
      <button
        onClick={() => isComplete && setOpen(!open)}
        className={`w-full flex items-center gap-3 p-4 text-left ${isComplete ? 'cursor-pointer' : 'cursor-default'}`}
      >
        {Icon && (
          <span className={`shrink-0 ${accentIcon[accentColor]}`}>
            <Icon size={18} />
          </span>
        )}
        <span className="flex-1 font-semibold text-slate-200 text-sm">{title}</span>

        {/* Status badge */}
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${STATUS_LABEL_CLASSES[status] || STATUS_LABEL_CLASSES.pending} flex items-center gap-1.5`}>
          {STATUS_ICON[status]}
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>

        {isComplete && (
          <span className="text-slate-500 ml-1">
            {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </span>
        )}
      </button>

      {open && isComplete && children && (
        <div className="px-5 pb-5 pt-1 border-t border-slate-800/60 animate-[fadeIn_0.2s_ease-out]">
          {children}
        </div>
      )}
    </div>
  );
}
