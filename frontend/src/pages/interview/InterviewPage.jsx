import React, { useState, useEffect, useRef } from 'react';
import { interviewAPI } from '../../services/interviewService';
import NavBar from '../../components/shared/NavBar';
import { Send, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';

const ROLES = [
  { id: 'Backend Engineer', label: 'Backend' },
  { id: 'Frontend Engineer', label: 'Frontend' },
  { id: 'System Design', label: 'System Design' },
  { id: 'Data Structures & Algorithms', label: 'DSA' },
];

export default function InterviewPage() {
  const [role, setRole] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const recognitionRef = useRef(null);

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
      alert("Speech recognition is not supported in your browser.");
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
      console.error("Speech recognition error", event.error);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
    
    recognitionRef.current = recognition;
    recognition.start();
  };

  const startInterview = async (selectedRole) => {
    setIsLoading(true);
    try {
      const res = await interviewAPI.startInterview(selectedRole, null, null);
      setRole(selectedRole);
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
    setRole(null);
    setSessionId(null);
    setTranscript([]);
    setCurrentQuestion('');
    setReport(null);
    window.speechSynthesis.cancel();
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

      <NavBar />

      <main className="flex-1 flex flex-col items-center p-6 z-10">
        {!role && (
          <div className="flex flex-col items-center justify-center flex-1">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 text-center">AI Interview</h1>
            <p className="text-slate-400 text-lg max-w-xl mx-auto text-center mb-10">
              Pick a domain and the AI will ask adaptive questions based on how you answer.
            </p>
            <div className="grid grid-cols-2 gap-4 w-full max-w-md">
              {ROLES.map((r) => (
                <button
                  key={r.id}
                  onClick={() => startInterview(r.id)}
                  disabled={isLoading}
                  className="btn-secondary py-4 disabled:opacity-40"
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {role && !report && (
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
                    title={voiceEnabled ? "Mute Agent" : "Unmute Agent"}
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
                    title={isListening ? "Stop listening" : "Start speaking"}
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