import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { interviewAPI } from '../../services/interviewService';
import NavBar from '../../components/shared/NavBar';
import CursorGrid from '../../components/shared/CursorGrid';
import {
  Send, Mic, MicOff, Volume2, VolumeX, Cpu, Monitor, BrainCircuit, Code2,
  FileUser, Zap, Layers, StopCircle, CheckCircle, BarChart2, MessageSquare,
  ChevronDown, ChevronUp, Briefcase, ArrowLeft, Timer as TimerIcon,
} from 'lucide-react';

const TOTAL_QUESTIONS = 7;
const QUESTION_TIME_SECONDS = 120;

const DOMAINS = [
  { id: 'Backend Engineer', label: 'Backend', icon: Cpu },
  { id: 'Frontend Engineer', label: 'Frontend', icon: Monitor },
  { id: 'System Design', label: 'System Design', icon: BrainCircuit },
  { id: 'Data Structures & Algorithms', label: 'DSA', icon: Code2 },
];

const INTERVIEW_MODES = [
  { id: 'Generic Interview', label: 'Generic Interview', desc: 'Standard questions for any candidate', icon: Zap, color: 'blue' },
  { id: 'Resume-Based Interview', label: 'Resume-Based', desc: 'Tailored to your resume projects & skills', icon: FileUser, color: 'emerald' },
  { id: 'Resume + JD Interview', label: 'Resume + JD', desc: 'Targets ATS gaps & role-specific skills', icon: Layers, color: 'indigo', requiresJd: true },
];

function scoreColour(score, max = 100) {
  const pct = (score / max) * 100;
  if (pct >= 75) return 'text-emerald-400';
  if (pct >= 50) return 'text-amber-400';
  return 'text-red-400';
}

function CircleProgress({ percentage, size = 120, stroke = 10 }) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (percentage / 100) * circ;
  const colour = percentage >= 75 ? '#34d399' : percentage >= 50 ? '#fbbf24' : '#f87171';

  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1e293b" strokeWidth={stroke} />
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={colour} strokeWidth={stroke}
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.8s ease' }}
      />
    </svg>
  );
}

function QuestionCard({ item, index }) {
  const [open, setOpen] = useState(false);
  const techPct = item.technical_score ?? 0;
  const commPct = item.communication_score ?? 0;

  return (
    <div className="glass-panel rounded-xl border border-slate-700/50 overflow-hidden">
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-800/40 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-bold flex items-center justify-center">
            {index + 1}
          </span>
          <span className="text-sm text-slate-300 text-left line-clamp-1 max-w-[320px]">
            {item.question}
          </span>
        </div>
        <div className="flex items-center gap-4 shrink-0 ml-3">
          <span className={`text-sm font-semibold ${scoreColour(techPct)}`}>{techPct}/100</span>
          {open ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-slate-700/50 pt-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-slate-500 mb-1">Technical</p>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500" style={{ width: `${techPct}%`, background: techPct >= 75 ? '#34d399' : techPct >= 50 ? '#fbbf24' : '#f87171' }} />
              </div>
              <p className={`text-xs font-semibold mt-1 ${scoreColour(techPct)}`}>{techPct}/100</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1">Communication</p>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500" style={{ width: `${commPct}%`, background: commPct >= 75 ? '#34d399' : commPct >= 50 ? '#fbbf24' : '#f87171' }} />
              </div>
              <p className={`text-xs font-semibold mt-1 ${scoreColour(commPct)}`}>{commPct}/100</p>
            </div>
          </div>

          {item.technical_feedback && (
            <div>
              <p className="text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1"><BarChart2 className="w-3 h-3" /> Technical feedback</p>
              <p className="text-xs text-slate-300 leading-relaxed">{item.technical_feedback}</p>
            </div>
          )}
          {item.communication_feedback && (
            <div>
              <p className="text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1"><MessageSquare className="w-3 h-3" /> Communication feedback</p>
              <p className="text-xs text-slate-300 leading-relaxed">{item.communication_feedback}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Countdown timer for the current question ──────────────────────────────
function QuestionTimer({ questionKey, running }) {
  const [secondsLeft, setSecondsLeft] = useState(QUESTION_TIME_SECONDS);

  useEffect(() => {
    setSecondsLeft(QUESTION_TIME_SECONDS);
  }, [questionKey]);

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => {
      setSecondsLeft((s) => (s > 0 ? s - 1 : 0));
    }, 1000);
    return () => clearInterval(id);
  }, [running, questionKey]);

  const pct = Math.max(0, Math.min(100, (secondsLeft / QUESTION_TIME_SECONDS) * 100));
  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  const low = secondsLeft <= 20;

  return (
    <div className="flex items-center gap-2">
      <TimerIcon className={`w-3.5 h-3.5 ${low ? 'text-red-400' : 'text-slate-500'}`} />
      <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 linear"
          style={{ width: `${pct}%`, background: low ? '#f87171' : '#6366f1' }}
        />
      </div>
      <span className={`text-xs font-mono ${low ? 'text-red-400' : 'text-slate-500'}`}>
        {mins}:{secs.toString().padStart(2, '0')}
      </span>
    </div>
  );
}

export default function InterviewPage() {
  const location = useLocation();
  const fromReport = location.state?.autoStart === true;
  const initialMode = location.state?.interviewMode || 'Generic Interview';
  const initialDomain = location.state?.targetDomain || 'Backend Engineer';
  const report = location.state?.report;
  const hasJd = location.state?.hasJd;
  const jobId = report?.job_id || location.state?.jobId;
  const fromJobs = location.state?.fromJobs === true;
  const navigate = useNavigate();

  const [selectedMode, setSelectedMode] = useState(initialMode);
  const [selectedDomain, setSelectedDomain] = useState(initialDomain);

  const [sessionId, setSessionId] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStarted, setIsStarted] = useState(false);

  const [questionScores, setQuestionScores] = useState([]);
  const [lastResult, setLastResult] = useState(null);

  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const recognitionRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (fromReport) {
      startInterview(initialMode, initialMode === 'Generic Interview' ? initialDomain : null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (currentQuestion && voiceEnabled) speakText(currentQuestion);
  }, [currentQuestion, voiceEnabled]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript, lastResult, currentQuestion]);

  const speakText = (text) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
  };

  const toggleListening = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in your browser.');
      return;
    }
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (event) => {
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) final += event.results[i][0].transcript;
      }
      if (final) setAnswerText((prev) => prev + (prev ? ' ' : '') + final);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
    recognition.start();
  };

  const startInterview = async (mode, domain) => {
    setIsLoading(true);
    try {
      const res = await interviewAPI.startInterview(domain, mode, null, null);
      setIsStarted(true);
      setSessionId(res.session_id);
      setCurrentQuestion(res.question);
      setTranscript([]);
      setSummary(null);
      setQuestionScores([]);
      setLastResult(null);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to start interview.');
    } finally {
      setIsLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!answerText.trim()) return;
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    setIsLoading(true);
    setLastResult(null);
    try {
      const res = await interviewAPI.submitAnswer(sessionId, answerText.trim());

      if (res.last_question_result) {
        setQuestionScores((prev) => {
          const exists = prev.some((q) => q.question_number === res.last_question_result.question_number);
          if (exists) return prev;
          return [...prev, res.last_question_result];
        });
        setLastResult(res.last_question_result);
      }

      if (res.status === 'completed') {
        if (res.summary) setSummary(res.summary);
        setCurrentQuestion('');
        window.speechSynthesis?.cancel();
      } else {
        const fullTranscript = res.transcript || [];
        const answeredTurns = fullTranscript.filter((t) => t.answer !== null && t.answer !== undefined);
        setTranscript(
          answeredTurns.map((t) => ({
            question: t.question,
            answer: t.answer,
            technicalScore: t.technical_score,
            communicationScore: t.communication_score,
            turnNumber: t.turn_number,
          }))
        );
        setCurrentQuestion(res.question);
      }
      setAnswerText('');
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to submit answer.');
    } finally {
      setIsLoading(false);
    }
  };

  const endInterview = async () => {
    if (!sessionId) return;
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
    setIsLoading(true);
    try {
      const res = await interviewAPI.endInterview(sessionId);
      if (res.summary) setSummary(res.summary);
      setCurrentQuestion('');
      window.speechSynthesis?.cancel();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to end interview.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetInterview = () => {
    setIsStarted(false);
    setSessionId(null);
    setTranscript([]);
    setCurrentQuestion('');
    setSummary(null);
    setQuestionScores([]);
    setLastResult(null);
    window.speechSynthesis?.cancel();
  };

  const modeColorMap = {
    blue: { active: 'border-blue-500 bg-blue-500/10', icon: 'text-blue-400' },
    emerald: { active: 'border-emerald-500 bg-emerald-500/10', icon: 'text-emerald-400' },
    indigo: { active: 'border-indigo-500 bg-indigo-500/10', icon: 'text-indigo-400' },
  };

  const questionsAnswered = transcript.length;
  const progressPct = Math.round((questionsAnswered / TOTAL_QUESTIONS) * 100);

  return (
    <div
      className="min-h-screen flex flex-col relative overflow-x-hidden"
      style={{ background: 'linear-gradient(180deg, #060b16 0%, #0b1220 100%)' }}
    >
      <div className="fixed inset-0 z-0 pointer-events-none md:pointer-events-auto">
        <CursorGrid
          cellSize={85} color="#6366f1" radius={120} falloff="smooth"
          holdTime={300} fadeDuration={700} lineWidth={0.8} maxOpacity={0.4}
          fillOpacity={0} gridOpacity={0.05} cellRadius={8} clickPulse={false}
        />
      </div>
      <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none z-0" />

      <NavBar />

      <main className="flex-1 flex flex-col items-center p-6 z-10 pt-24 pb-16">

        {/* ── Mode / domain selector ── */}
        {!isStarted && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
            className="flex flex-col items-center justify-center flex-1 w-full max-w-2xl"
          >
            <h1 className="text-4xl md:text-5xl font-bold mb-3 text-center">AI Interview</h1>
            <p className="text-slate-400 text-lg text-center mb-10">
              Pick a mode and domain. The AI will adapt its questions based on your answers.
            </p>

            <div className="w-full mb-8">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Interview Mode</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {INTERVIEW_MODES.map((m) => {
                  const Icon = m.icon;
                  const active = selectedMode === m.id;
                  const colors = modeColorMap[m.color];
                  return (
                    <button
                      key={m.id}
                      id={`mode-${m.id.replace(/\s+/g, '-').toLowerCase()}`}
                      onClick={() => setSelectedMode(m.id)}
                      className={`p-4 rounded-2xl border text-left transition-all ${
                        active ? `${colors.active} shadow-lg` : 'border-slate-700/50 bg-slate-900/40 hover:border-slate-600'
                      }`}
                    >
                      <Icon className={`w-5 h-5 mb-2 ${active ? colors.icon : 'text-slate-500'}`} />
                      <p className={`font-semibold text-sm ${active ? 'text-slate-100' : 'text-slate-300'}`}>{m.label}</p>
                      <p className="text-xs text-slate-500 mt-1">{m.desc}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {selectedMode === 'Generic Interview' && (
              <div className="w-full mb-8">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Technical Domain</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {DOMAINS.map((d) => {
                    const Icon = d.icon;
                    const active = selectedDomain === d.id;
                    return (
                      <button
                        key={d.id}
                        id={`domain-${d.id.replace(/\s+/g, '-').toLowerCase()}`}
                        onClick={() => setSelectedDomain(d.id)}
                        className={`flex flex-col items-center gap-2 py-4 px-3 rounded-2xl border transition-all ${
                          active
                            ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300'
                            : 'border-slate-700/50 bg-slate-900/40 text-slate-400 hover:border-slate-600 hover:text-slate-300'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                        <span className="text-sm font-medium">{d.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            <button
              id="btn-start-interview"
              onClick={() => startInterview(selectedMode, selectedMode === 'Generic Interview' ? selectedDomain : null)}
              disabled={isLoading}
              className="btn-primary w-full py-4 text-lg font-semibold flex items-center justify-center gap-3 disabled:opacity-40"
            >
              <Zap className="w-5 h-5" />
              Start Interview
            </button>
          </motion.div>
        )}

        {/* ── Loading spinner while starting ── */}
        {isLoading && !isStarted && (
          <div className="flex-1 flex flex-col items-center justify-center gap-4">
            <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
            <p className="text-slate-400">Preparing your interview...</p>
          </div>
        )}

        {/* ── Active interview ── */}
        {isStarted && !summary && (
          <div className="w-full max-w-2xl mx-auto space-y-4">

            {/* Progress header with stats */}
            <div className="glass-panel p-4 rounded-2xl border border-slate-700/50 flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Progress</p>
                <p className="text-lg font-bold text-slate-100">
                  {questionsAnswered} / {TOTAL_QUESTIONS} answered
                  <span className="text-slate-500 text-sm font-normal ml-2">({progressPct}% complete)</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-indigo-500 rounded-full"
                    animate={{ width: `${progressPct}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                  />
                </div>
                <button
                  id="btn-end-interview"
                  onClick={endInterview}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-red-500/40 text-red-400 text-xs font-semibold hover:bg-red-500/10 transition-colors disabled:opacity-40"
                >
                  <StopCircle className="w-3.5 h-3.5" />
                  End Interview
                </button>
              </div>
            </div>

            {/* Answered turns */}
            <AnimatePresence initial={false}>
              {transcript.map((t, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="glass-panel p-4 rounded-xl border border-slate-700/50"
                >
                  <p className="text-sm text-slate-400 mb-1">Q{t.turnNumber ?? i + 1}: {t.question}</p>
                  <p className="text-slate-200 mb-2 text-sm">{t.answer}</p>
                  <div className="flex gap-4 text-xs">
                    <span className={scoreColour(t.technicalScore)}>Technical: {t.technicalScore}/100</span>
                    <span className={scoreColour(t.communicationScore)}>Communication: {t.communicationScore}/100</span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Previous feedback */}
            <AnimatePresence>
              {lastResult && !isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="glass-panel p-4 rounded-xl border border-indigo-500/30 bg-indigo-500/5 space-y-2"
                >
                  <p className="text-xs font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5" /> Feedback on Q{lastResult.question_number}
                  </p>
                  {lastResult.technical_feedback && (
                    <p className="text-xs text-slate-300">
                      <span className="text-slate-400 font-medium">Technical: </span>{lastResult.technical_feedback}
                    </p>
                  )}
                  {lastResult.communication_feedback && (
                    <p className="text-xs text-slate-300">
                      <span className="text-slate-400 font-medium">Communication: </span>{lastResult.communication_feedback}
                    </p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Current question card */}
            <AnimatePresence mode="wait">
              {currentQuestion && (
                <motion.div
                  key={currentQuestion}
                  initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -14 }}
                  transition={{ duration: 0.35, ease: 'easeOut' }}
                  className="glass-panel p-6 rounded-2xl border border-slate-700"
                >
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-sm text-slate-400">Question {transcript.length + 1} of {TOTAL_QUESTIONS}</p>
                    <button
                      onClick={() => setVoiceEnabled(!voiceEnabled)}
                      className="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors"
                      title={voiceEnabled ? 'Mute Agent' : 'Unmute Agent'}
                    >
                      {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                    </button>
                  </div>

                  <p className="text-lg font-medium text-slate-100 mb-4">{currentQuestion}</p>

                  {/* Answer box */}
                  <div className="relative mb-3">
                    <textarea
                      value={answerText}
                      onChange={(e) => setAnswerText(e.target.value)}
                      placeholder="Type your answer or use the microphone..."
                      rows={5}
                      className="w-full bg-slate-900/80 border border-slate-700/50 rounded-xl p-4 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none pr-12"
                    />
                    <button
                      onClick={toggleListening}
                      className={`absolute bottom-4 right-4 p-2 rounded-full transition-colors ${
                        isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-slate-800 text-slate-400 hover:text-white'
                      }`}
                      title={isListening ? 'Stop listening' : 'Start speaking'}
                    >
                      {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Timer */}
                  <div className="flex justify-end mb-4">
                    <QuestionTimer questionKey={currentQuestion} running={!isLoading} />
                  </div>

                  <button
                    onClick={submitAnswer}
                    disabled={isLoading || !answerText.trim()}
                    className="btn-primary w-full flex items-center justify-center space-x-2 disabled:opacity-40"
                  >
                    <Send className="w-4 h-4" />
                    <span>{isLoading ? 'Evaluating...' : 'Submit Answer'}</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {isLoading && isStarted && (
              <div className="flex items-center justify-center gap-3 py-4">
                <div className="w-5 h-5 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
                <p className="text-slate-400 text-sm">Evaluating answer...</p>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}

        {/* ── Summary / Report ── */}
        {summary && (
          <motion.div
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
            className="w-full max-w-2xl mx-auto space-y-6"
          >
            <div className="glass-panel p-8 rounded-2xl border border-indigo-500/40 text-center relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 pointer-events-none" />
              <h2 className="text-2xl font-bold mb-6">Interview Complete</h2>

              <div className="flex flex-col items-center gap-2 mb-6">
                <div className="relative">
                  <CircleProgress percentage={summary.percentage ?? 0} size={140} stroke={12} />
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-bold text-slate-100">{Math.round(summary.percentage ?? 0)}%</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-slate-800/60 rounded-xl p-3">
                  <p className="text-xs text-slate-500 mb-1">Questions</p>
                  <p className="text-xl font-bold text-slate-100">
                    {summary.questions_answered}<span className="text-slate-500 text-sm">/{summary.total_questions}</span>
                  </p>
                </div>
                <div className="bg-slate-800/60 rounded-xl p-3">
                  <p className="text-xs text-slate-500 mb-1">Total Score</p>
                  <p className={`text-xl font-bold ${scoreColour(summary.total_score, summary.max_score)}`}>
                    {summary.total_score}<span className="text-slate-500 text-sm">/{summary.max_score}</span>
                  </p>
                </div>
                <div className="bg-slate-800/60 rounded-xl p-3">
                  <p className="text-xs text-slate-500 mb-1">Percentage</p>
                  <p className={`text-xl font-bold ${scoreColour(summary.percentage ?? 0, 100)}`}>{summary.percentage ?? 0}%</p>
                </div>
              </div>
            </div>

            {summary.per_question?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Per-Question Breakdown</p>
                <div className="space-y-2">
                  {summary.per_question.map((item, i) => (
                    <QuestionCard key={i} item={item} index={i} />
                  ))}
                </div>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3">
              {report && !fromJobs && (
                <button onClick={() => navigate('/report', { state: { report, jobId, hasJd } })} className="btn-secondary flex-1 flex items-center justify-center gap-2 py-3">
                  <ArrowLeft className="w-4 h-4" /> Back to Report
                </button>
              )}
              {jobId && (
                <button onClick={() => navigate(`/jobs/${jobId}`, { state: { hasJd } })} className="btn-primary flex-1 flex items-center justify-center gap-2 py-3">
                  <Briefcase className="w-4 h-4" /> Find Opportunities
                </button>
              )}
              <button id="btn-start-another" onClick={resetInterview} className="btn-secondary flex-1 py-3">
                Start Another
              </button>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
}