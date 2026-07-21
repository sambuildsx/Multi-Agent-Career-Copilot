import React from 'react';
import {
  AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, Radar,
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid
} from 'recharts';
import { TrendingUp, Radar as RadarIcon, BarChart3, Gauge } from 'lucide-react';

const TooltipBox = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/95 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 shadow-xl">
        {label && <div className="text-slate-400 mb-0.5">{label}</div>}
        <span className="font-semibold text-cyan-400">{payload[0].value}</span>
      </div>
    );
  }
  return null;
};

function CardShell({ icon: Icon, title, children }) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-cyan-400" />
        <h4 className="text-sm font-semibold text-slate-200">{title}</h4>
      </div>
      <div className="flex-1 min-h-[140px]">{children}</div>
    </div>
  );
}

export function ScoreTrendCard({ title = 'ATS Score Trend', data, dataKey = 'score', color = '#4CC9F0' }) {
  return (
    <CardShell icon={TrendingUp} title={title}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${dataKey}-${title}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.25} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(255,255,255,0.03)" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} domain={[0, 100]} />
          <Tooltip content={<TooltipBox />} cursor={{ stroke: `${color}30`, strokeWidth: 1 }} />
          <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} fill={`url(#grad-${dataKey}-${title})`} dot={{ fill: color, r: 3, strokeWidth: 0 }} />
        </AreaChart>
      </ResponsiveContainer>
    </CardShell>
  );
}

export function SkillsRadarCard({ data }) {
  return (
    <CardShell icon={RadarIcon} title="Skills Distribution">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="70%">
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis dataKey="skill" tick={{ fill: '#94a3b8', fontSize: 10 }} />
          <Radar dataKey="value" stroke="#38BDF8" fill="#38BDF8" fillOpacity={0.25} strokeWidth={2} />
          <Tooltip content={<TooltipBox />} />
        </RadarChart>
      </ResponsiveContainer>
    </CardShell>
  );
}

export function CompletenessBarCard({ data }) {
  return (
    <CardShell icon={BarChart3} title="Resume Completeness">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 12, left: 0, bottom: 0 }}>
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis dataKey="section" type="category" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} width={90} />
          <Tooltip content={<TooltipBox />} cursor={{ fill: 'rgba(76,201,240,0.05)' }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]} fill="#4CC9F0" />
        </BarChart>
      </ResponsiveContainer>
    </CardShell>
  );
}

export function CompletenessRingCard({ percentage = 0 }) {
  const r = 46;
  const circ = 2 * Math.PI * r;
  const offset = circ - (percentage / 100) * circ;
  return (
    <CardShell icon={Gauge} title="Overall Completeness">
      <div className="relative flex items-center justify-center h-full">
        <svg width={120} height={120} className="rotate-[-90deg]">
          <circle cx={60} cy={60} r={r} fill="none" stroke="#1e293b" strokeWidth={10} />
          <circle
            cx={60} cy={60} r={r} fill="none" stroke="#4CC9F0" strokeWidth={10}
            strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease' }}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-2xl font-bold text-white">{Math.round(percentage)}%</span>
      </div>
    </CardShell>
  );
}