import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { interviewAPI } from '../../services/interviewService';
import NavBar from '../../components/shared/NavBar';
import { Send, Mic, MicOff, Volume2, VolumeX, Cpu, Monitor, BrainCircuit, Code2, FileUser, Zap, Layers } from 'lucide-react';

const DOMAINS = [
  { id: 'Backend Engineer', label: 'Backend', icon: Cpu },
  { id: 'Frontend Engineer', label: 'Frontend', icon: Monitor },
  { id: 'System Design', label: 'System Design', icon: BrainCircuit },
  { id: 'Data Structures & Algorithms', label: 'DSA', icon: Code2 },
];

const INTERVIEW_MODES = [
  {
    id: 'Generic Interview',
    label: 'Generic Interview',
    desc: 'Standard questions for any candidate',
    icon: Zap,
    color: 'blue',
  },
  {
    id: 'Resume-Based Interview',
    label: 'Resume-Based',
    desc: 'Tailored to your resume projects & skills',
    icon: FileUser,
    color: 'emerald',
  },
  {
    id: 'Resume + JD Interview',
    label: 'Resume + JD',
    desc: 'Targets ATS gaps & role-specific skills',
    icon: Layers,
    color: 'indigo',
    requiresJd: true,
  },
];

export default function InterviewPage() {
  const location = useLocation();
  // Pre-selections passed from ReportPage
  const fromReport = location.state?.autoStart === true;
  const initialMode = location.state?.interviewMode || 'Generic Interview';
  const initialDomain = location.state?.targetDomain || 'Backend Engineer';

  const [selectedMode, setSelectedMode] = useState(initialMode);
  const [selectedDomain, setSelectedDomain] = useState(initialDomain);

  const [sessionId, setSessionId] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStarted, setIsStarted] = useState(false);

  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const recognitionRef = useRef(null);

  // Auto-start if navigated from ReportPage with pre-selected mode/domain
  useEffect(() => {
    if (fromReport) {
      startInterview(initialMode, initialMode === 'Generic Interview' ? initialDomain : null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (currentQuestion && voiceEnabled) {
      speakText(currentQuestion);
    }
  }, [currentQuestion, voiceEnabled]);

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
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        setAnswerText((prev) => prev + (prev ? ' ' : '') + finalTranscript);
      }
    };
    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      setIsListening(false);
    };
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
      setReport(null);
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
    try {
      const res = await interviewAPI.submitAnswer(sessionId, answerText.trim());

      if (res.status === 'completed') {
        setReport(res.report);
        setCurrentQuestion('');
      } else {
        const fullTranscript = res.transcript || [];
        const answeredTurns = fullTranscript.filter((t) => t.answer !== null && t.answer !== undefined);
        setTranscript(
          answeredTurns.map((t) => ({
            question: t.question,
            answer: t.answer,
            technicalScore: t.technical_score,
            communicationScore: t.communication_score,
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

  const resetInterview = () => {
    setIsStarted(false);
    setSessionId(null);
    setTranscript([]);
    setCurrentQuestion('');
    setReport(null);
    window.speechSynthesis.cancel();
  };

  const modeColorMap = {
    blue: { active: 'border-blue-500 bg-blue-500/10', icon: 'text-blue-400' },
    emerald: { active: 'border-emerald-500 bg-emerald-500/10', icon: 'text-emerald-400' },
    indigo: { active: 'border-indigo-500 bg-indigo-500/10', icon: 'text-indigo-400' },
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

      <NavBar />

      <main className="flex-1 flex flex-col items-center p-6 z-10">

        {/* ── Selector: mode not yet started ── */}
        {!isStarted && !isLoading && (
          <div className="flex flex-col items-center justify-center flex-1 w-full max-w-2xl">
            <h1 className="text-4xl md:text-5xl font-bold mb-3 text-center">AI Interview</h1>
            <p className="text-slate-400 text-lg text-center mb-10">
              Pick a mode and domain. The AI will adapt its questions based on your answers.
            </p>

            {/* Interview Mode */}
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
                        active
                          ? `${colors.active} shadow-lg`
                          : 'border-slate-700/50 bg-slate-900/40 hover:border-slate-600'
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

            {/* Domain */}
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
          </div>
        )}

        {/* ── Loading spinner while starting ── */}
        {isLoading && !isStarted && (
          <div className="flex-1 flex flex-col items-center justify-center gap-4">
            <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
            <p className="text-slate-400">Preparing your interview...</p>
          </div>
        )}

        {/* ── Active interview ── */}
        {isStarted && !report && (
          <div className="w-full max-w-2xl mx-auto space-y-4">
            {transcript.map((t, i) => (
              <div key={i} className="glass-panel p-4 rounded-xl border border-slate-700/50">
                <p className="text-sm text-slate-400 mb-1">Q{i + 1}: {t.question}</p>
                <p className="text-slate-200 mb-2">{t.answer}</p>
                <p className="text-xs text-indigo-400">
                  Technical: {t.technicalScore}/100 · Communication: {t.communicationScore}/100
                </p>
              </div>
            ))}

            {currentQuestion && (
              <div className="glass-panel p-6 rounded-2xl border border-slate-700">
                <div className="flex justify-between items-center mb-2">
                  <p className="text-sm text-slate-400">Question {transcript.length + 1}</p>
                  <button
                    onClick={() => setVoiceEnabled(!voiceEnabled)}
                    className="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors"
                    title={voiceEnabled ? 'Mute Agent' : 'Unmute Agent'}
                  >
                    {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                  </button>
                </div>

                <p className="text-lg font-medium text-slate-100 mb-4">{currentQuestion}</p>

                <div className="relative mb-4">
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

        {/* ── Report ── */}
        {report && (
          <div className="w-full max-w-2xl mx-auto space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-indigo-500/50 text-center">
              <h2 className="text-2xl font-bold mb-2">Interview Complete</h2>
              <p className="text-4xl font-bold text-indigo-400 mb-4">
                {report.interview_score ?? report.overall_score ?? 0}/100
              </p>
              <p className="text-slate-300 whitespace-pre-wrap">{report.markdown}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="glass-panel p-4 rounded-xl border border-slate-700/50">
                <h3 className="font-semibold text-green-400 mb-2">Strengths</h3>
                <ul className="text-sm text-slate-300 space-y-1">
                  {(report.strengths || []).map((s, i) => <li key={i}>• {s}</li>)}
                </ul>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-slate-700/50">
                <h3 className="font-semibold text-amber-400 mb-2">Areas to Improve</h3>
                <ul className="text-sm text-slate-300 space-y-1">
                  {(report.weaknesses || []).map((s, i) => <li key={i}>• {s}</li>)}
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