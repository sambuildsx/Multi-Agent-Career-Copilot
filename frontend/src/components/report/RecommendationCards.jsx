import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2 } from 'lucide-react';

export default function RecommendationCards({ recommendations = [] }) {
  if (!recommendations || recommendations.length === 0) return null;

  // Cap to 4 concise cards; trim long text
  const items = recommendations.slice(0, 4);

  return (
    <div className="glass-panel p-6">
      <h3 className="font-semibold text-lg mb-4 text-slate-200">Actionable Recommendations</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {items.map((rec, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.35, delay: idx * 0.06 }}
            className="rounded-[18px] p-4 border border-white/[0.06] flex items-start gap-2.5"
            style={{ background: 'rgba(255,255,255,0.04)', backdropFilter: 'blur(12px)' }}
          >
            <CheckCircle2 className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
            <p className="text-sm text-slate-300 leading-snug line-clamp-3">{rec}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}