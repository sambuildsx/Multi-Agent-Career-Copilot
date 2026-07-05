import React, { useState } from 'react';
import api from '../api';
import NavBar from '../components/NavBar';
import { Send } from 'lucide-react';

const DOMAINS = [
  { id: 'backend', label: 'Backend' },
  { id: 'frontend', label: 'Frontend' },
  { id: 'system_design', label: 'System Design' },
  { id: 'dsa', label: 'DSA' },
];

export default function InterviewPage() {
  const [domain, setDomain] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const startInterview = async (selectedDomain) => {
    setIsLoading(true);
    try {
      const res = await api.post('/interview/start', { domain: selectedDomain });
      setDomain(selectedDomain);
      setSessionId(res.data.session_id);
      setCurrentQuestion(res.data.question);
      setTranscript([]);
      setSummary(null);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to start interview.');
    } finally {
      setIsLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!answerText.trim()) return;
    setIsLoading(true);
    try {
      const res = await api.post(`/interview/${sessionId}/answer`, { answer: answerText.trim() });

      setTranscript((prev) => [
        ...prev,
        {
          question: currentQuestion,
          answer: answerText.trim(),
          score: res.data.last_evaluation.score,
          feedback: res.data.last_evaluation.feedback,
        },
      ]);
      setAnswerText('');

      if (res.data.status === 'completed') {
        setSummary(res.data.summary);
        setCurrentQuestion('');
      } else {
        setCurrentQuestion(res.data.question);
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to submit answer.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetInterview = () => {
    setDomain(null);
    setSessionId(null);
    setTranscript([]);
    setCurrentQuestion('');
    setSummary(null);
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

      <NavBar />

      <main className="flex-1 flex flex-col items-center p-6 z-10">
        {!domain && (
          <div className="flex flex-col items-center justify-center flex-1">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 text-center">AI Interview</h1>
            <p className="text-slate-400 text-lg max-w-xl mx-auto text-center mb-10">
              Pick a domain and the AI will ask adaptive questions based on how you answer.
            </p>
            <div className="grid grid-cols-2 gap-4 w-full max-w-md">
              {DOMAINS.map((d) => (
                <button
                  key={d.id}
                  onClick={() => startInterview(d.id)}
                  disabled={isLoading}
                  className="btn-secondary py-4 disabled:opacity-40"
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {domain && !summary && (
          <div className="w-full max-w-2xl mx-auto space-y-4">
            {transcript.map((t, i) => (
              <div key={i} className="glass-panel p-4 rounded-xl border border-slate-700/50">
                <p className="text-sm text-slate-400 mb-1">Q{i + 1}: {t.question}</p>
                <p className="text-slate-200 mb-2">{t.answer}</p>
                <p className="text-xs text-indigo-400">Score: {t.score}/100 — {t.feedback}</p>
              </div>
            ))}

            {currentQuestion && (
              <div className="glass-panel p-6 rounded-2xl border border-slate-700">
                <p className="text-sm text-slate-400 mb-2">Question {transcript.length + 1}</p>
                <p className="text-lg font-medium text-slate-100 mb-4">{currentQuestion}</p>
                <textarea
                  value={answerText}
                  onChange={(e) => setAnswerText(e.target.value)}
                  placeholder="Type your answer..."
                  rows={5}
                  className="w-full bg-slate-900/80 border border-slate-700/50 rounded-xl p-4 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none mb-4"
                />
                <button
                  onClick={submitAnswer}
                  disabled={isLoading || !answerText.trim()}
                  className="btn-primary w-full flex items-center justify-center space-x-2 disabled:opacity-40"
                >
                  <Send className="w-4 h-4" />
                  <span>{isLoading ? 'Evaluating...' : 'Submit Answer'}</span>
                </button>
              </div>
            )}
          </div>
        )}

        {summary && (
          <div className="w-full max-w-2xl mx-auto space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-indigo-500/50 text-center">
              <h2 className="text-2xl font-bold mb-2">Interview Complete</h2>
              <p className="text-4xl font-bold text-indigo-400 mb-4">{summary.overall_score}/100</p>
              <p className="text-slate-300 whitespace-pre-wrap">{summary.summary_markdown}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="glass-panel p-4 rounded-xl border border-slate-700/50">
                <h3 className="font-semibold text-green-400 mb-2">Strengths</h3>
                <ul className="text-sm text-slate-300 space-y-1">
                  {summary.key_strengths.map((s, i) => <li key={i}>• {s}</li>)}
                </ul>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-slate-700/50">
                <h3 className="font-semibold text-amber-400 mb-2">Areas to Improve</h3>
                <ul className="text-sm text-slate-300 space-y-1">
                  {summary.key_areas_to_improve.map((s, i) => <li key={i}>• {s}</li>)}
                </ul>
              </div>
            </div>

            <button onClick={resetInterview} className="btn-secondary w-full">
              Start Another Interview
            </button>
          </div>
        )}
      </main>
    </div>
  );
}