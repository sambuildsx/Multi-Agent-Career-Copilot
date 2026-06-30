import React from 'react';
import { Lightbulb, ArrowRight, BookOpen } from 'lucide-react';

export default function RecommendationList({ recommendations = [] }) {
  if (!recommendations || recommendations.length === 0) {
    return null;
  }

  return (
    <div className="glass-panel p-6 h-full flex flex-col">
      <div className="flex items-center space-x-2 mb-6">
        <Lightbulb className="w-5 h-5 text-amber-400" />
        <h3 className="text-lg font-semibold text-slate-200">Actionable Recommendations</h3>
      </div>
      
      <div className="space-y-4 flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {recommendations.map((rec, index) => (
          <div 
            key={index} 
            className="group relative bg-slate-900/40 hover:bg-slate-800/60 p-4 rounded-xl border border-slate-800/50 hover:border-amber-500/30 transition-all duration-300 flex flex-col sm:flex-row gap-4"
          >
            <div className="flex-shrink-0 mt-1">
              <div className="w-8 h-8 rounded-full bg-amber-500/10 flex items-center justify-center border border-amber-500/20 group-hover:scale-110 transition-transform">
                <BookOpen className="w-4 h-4 text-amber-400" />
              </div>
            </div>
            
            <div className="flex-1">
              <p className="text-sm text-slate-300 leading-relaxed mb-3">
                {rec}
              </p>
              
              <button className="flex items-center text-xs font-medium text-amber-400/80 hover:text-amber-400 transition-colors group/btn">
                <span>View Learning Resources</span>
                <ArrowRight className="w-3 h-3 ml-1 transform group-hover/btn:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
