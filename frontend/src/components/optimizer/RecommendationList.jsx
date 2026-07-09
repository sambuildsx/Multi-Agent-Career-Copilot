import React from 'react';
import { Lightbulb, ArrowRight, BookOpen, Zap, TrendingUp } from 'lucide-react';

/**
 * RecommendationList — renders a list of career recommendations.
 *
 * Supports two data shapes (backward-compatible):
 *   1. recommendation_cards: Array<{ current: string, better: string, impact: string }>
 *      Rendered as structured "Current → Better" upgrade cards.
 *
 *   2. recommendations: Array<string>
 *      Rendered as plain text cards (legacy / fallback format).
 *
 * Props:
 *   cards           – structured card objects (preferred)
 *   recommendations – plain-text string array (fallback)
 */
export default function RecommendationList({ cards = [], recommendations = [] }) {
  const hasCards = cards && cards.length > 0;
  const hasPlain = recommendations && recommendations.length > 0;

  if (!hasCards && !hasPlain) return null;

  /* ── Structured card renderer ── */
  if (hasCards) {
    return (
      <div className="glass-panel p-6 h-full flex flex-col">
        <div className="flex items-center space-x-2 mb-6">
          <TrendingUp className="w-5 h-5 text-amber-400" />
          <h3 className="text-lg font-semibold text-slate-200">Actionable Recommendations</h3>
          <span className="ml-auto text-xs text-slate-500 font-medium">{cards.length} improvements</span>
        </div>

        <div className="space-y-4 flex-1 overflow-y-auto pr-2 custom-scrollbar">
          {cards.map((card, index) => (
            <div
              key={index}
              className="group relative rounded-xl border border-slate-800/60 hover:border-amber-500/40 transition-all duration-300 overflow-hidden"
            >
              {/* Priority badge */}
              <div className="absolute top-3 right-3 flex items-center space-x-1 bg-amber-500/10 border border-amber-500/20 rounded-full px-2 py-0.5">
                <Zap className="w-2.5 h-2.5 text-amber-400" />
                <span className="text-[10px] font-semibold text-amber-400 uppercase tracking-wide">
                  #{index + 1}
                </span>
              </div>

              {/* Current state */}
              <div className="bg-rose-500/5 border-b border-slate-800/40 px-4 py-3">
                <p className="text-[11px] font-bold text-rose-400 uppercase tracking-widest mb-1">Current</p>
                <p className="text-sm text-slate-400 leading-relaxed pr-10">
                  {card.current || '—'}
                </p>
              </div>

              {/* Better version */}
              <div className="bg-emerald-500/5 border-b border-slate-800/40 px-4 py-3 flex items-start space-x-2">
                <ArrowRight className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-[11px] font-bold text-emerald-400 uppercase tracking-widest mb-1">Better</p>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {card.better || '—'}
                  </p>
                </div>
              </div>

              {/* Impact */}
              <div className="bg-slate-900/40 px-4 py-2 flex items-center space-x-2">
                <TrendingUp className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                <p className="text-xs text-indigo-300 font-medium">
                  {card.impact || '—'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  /* ── Plain-text fallback renderer ── */
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
