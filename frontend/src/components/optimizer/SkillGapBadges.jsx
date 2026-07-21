import React from 'react';
import { Check, X, Info } from 'lucide-react';

export default function SkillGapBadges({ presentSkills = [], missingSkills = [], hasJd = false }) {
  if (!hasJd) {
    return (
      <div className="glass-panel p-6">
        <h3 className="text-lg font-semibold mb-4 text-slate-200">ATS Resume Analysis</h3>
        <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
          <Info className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-slate-300">ATS Scoring based on standard technical skills.</p>
            <p className="text-sm text-slate-500 mt-1">
              Your resume was evaluated for general ATS compatibility without a job description. Upload a specific JD to see targeted matched and missing skills.
            </p>
          </div>
        </div>

        {presentSkills.length > 0 && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-emerald-400 flex items-center">
                <Check className="w-4 h-4 mr-1.5" />
                Parsed ATS Skills
              </h4>
              <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded-full">
                {presentSkills.length} found
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {presentSkills.map((skill, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="glass-panel p-6">
      <h3 className="text-lg font-semibold mb-4 text-slate-200">ATS Skill Match Analysis</h3>

      <div className="space-y-6">
        {/* Matched Skills */}
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

        {/* Missing Skills */}
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

          {missingSkills.length > 0 ? (
            <>
              <p className="text-xs text-slate-500 mb-2">
                {missingSkills.length} skill{missingSkills.length !== 1 ? 's' : ''} required by the JD not found in your resume:{' '}
                <span className="text-slate-400 font-medium">{missingSkills.join(', ')}</span>
              </p>
              <div className="flex flex-wrap gap-2">
                {missingSkills.map((skill, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500 italic">All required skills met!</p>
          )}
        </div>
      </div>
    </div>
  );
}
