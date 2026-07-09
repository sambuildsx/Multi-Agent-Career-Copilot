import React from 'react';
import { Check, X } from 'lucide-react';

export default function SkillGapBadges({ presentSkills = [], missingSkills = [] }) {
  return (
    <div className="glass-panel p-6">
      <h3 className="text-lg font-semibold mb-4 text-slate-200">Skill Analysis</h3>
      
      <div className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-emerald-400 flex items-center">
              <Check className="w-4 h-4 mr-1.5" />
              Matched Skills
            </h4>
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded-full">
              {presentSkills.length} found
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {presentSkills.length > 0 ? (
              presentSkills.map((skill, index) => (
                <span 
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                >
                  {skill}
                </span>
              ))
            ) : (
              <p className="text-sm text-slate-500 italic">No matched skills found.</p>
            )}
          </div>
        </div>

        <div className="w-full h-px bg-slate-800/50"></div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-rose-400 flex items-center">
              <X className="w-4 h-4 mr-1.5" />
              Missing Requirements
            </h4>
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded-full">
              {missingSkills.length} missing
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {missingSkills.length > 0 ? (
              missingSkills.map((skill, index) => (
                <span 
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20"
                >
                  {skill}
                </span>
              ))
            ) : (
              <p className="text-sm text-slate-500 italic">All required skills met!</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
