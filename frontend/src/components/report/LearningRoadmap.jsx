import React from 'react';
import { motion } from 'framer-motion';
import { FileSearch, Puzzle, Hammer, MessagesSquare, Send, ArrowRight, BookOpen } from 'lucide-react';

const DEFAULT_ICONS = [FileSearch, Puzzle, Hammer, MessagesSquare, Send];

export default function LearningRoadmap({ steps = [] }) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="glass-panel p-6">
      <h3 className="font-semibold text-lg mb-6 text-slate-200 flex items-center gap-2">
        <BookOpen className="w-5 h-5 text-amber-400" /> Learning Roadmap
      </h3>

      <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
        {steps.map((step, idx) => {
          const Icon = DEFAULT_ICONS[idx % DEFAULT_ICONS.length];
          const isLast = idx === steps.length - 1;
          return (
            <React.Fragment key={idx}>
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: idx * 0.1 }}
                className="flex-1 min-w-0 bg-slate-900/60 border border-slate-800/70 rounded-2xl p-4 flex flex-col items-center text-center gap-2 hover:border-cyan-500/30 transition-colors"
              >
                <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                  <Icon className="w-5 h-5 text-cyan-400" />
                </div>
                <p className="text-sm text-slate-200 font-medium leading-snug">{step}</p>
              </motion.div>

              {!isLast && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.6 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: idx * 0.1 + 0.15 }}
                  className="flex items-center justify-center shrink-0 self-center rotate-90 md:rotate-0"
                >
                  <ArrowRight className="w-5 h-5 text-slate-600" />
                </motion.div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}