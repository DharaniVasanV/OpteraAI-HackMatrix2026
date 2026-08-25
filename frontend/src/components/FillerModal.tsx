import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { Zap, ExternalLink, Activity, CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';

interface Question {
  id: number;
  question_text: string;
  field_type: string;
  options: string[];
  is_required: boolean;
  proposed_answer: string;
  is_missing: boolean;
  user_answer?: string;
}

interface Session {
  id: string;
  form_url: string;
  title: string;
  status: string;
  questions: Question[];
}

export function FillerModal({ sessionId, onClose }: { sessionId: string; onClose: () => void }) {
  const [session, setSession] = useState<Session | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [fillMode, setFillMode] = useState<'auto' | 'manual'>('auto');
  const [status, setStatus] = useState<'loading' | 'review' | 'executing' | 'success' | 'error'>('loading');
  const [errorObj, setErrorObj] = useState<any>(null);
  const [executionLog, setExecutionLog] = useState<any[]>([]);

  useEffect(() => {
    fetchSession();
  }, [sessionId]);

  const fetchSession = async () => {
    try {
      const res = await axios.get(`/api/filler/session/${sessionId}`);
      setSession(res.data);
      const initAns: Record<number, string> = {};
      res.data.questions.forEach((q: Question) => {
        initAns[q.id] = q.user_answer || q.proposed_answer || '';
      });
      setAnswers(initAns);
      setStatus(res.data.status === 'executing' ? 'executing' : 'review');
      if (res.data.status === 'executing') {
        startExecutionStream();
      }
    } catch (e: any) {
      console.error(e);
      setStatus('error');
      setErrorObj(e.message || "Failed to load session");
    }
  };

  const startExecutionStream = () => {
    setStatus('executing');
    const source = new EventSource(`/api/filler/execution/${sessionId}/stream`);
    
    source.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.ping) return;
      if (data.completed) {
        source.close();
        if (data.redirect_url) {
          setStatus('success');
        }
      } else if (Array.isArray(data)) {
        setExecutionLog(prev => {
           // Merge lines
           const merged = [...prev];
           data.forEach(d => {
             const idx = merged.findIndex(m => m.step_name === d.step_name);
             if (idx >= 0) merged[idx] = d;
             else merged.push(d);
           });
           return merged;
        });
      }
    };
    source.onerror = (e) => {
      console.error('SSE Error:', e);
      source.close();
      setStatus('error');
      setErrorObj('Execution stream interrupted.');
    };
  };

  useEffect(() => {
    if (status === 'success') {
      const timer = setTimeout(() => {
        onClose();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [status, onClose]);

  const handleStartAutomation = async () => {
    try {
      setStatus('loading');
      await axios.post(`/api/filler/review/${sessionId}`, {
        fill_mode: fillMode,
        question_updates: answers
      });
      
      if (fillMode === 'manual') {
        window.open(session?.form_url, '_blank');
        setStatus('success');
      } else {
        startExecutionStream();
      }
    } catch (e: any) {
      console.error(e);
      setStatus('error');
      setErrorObj("Failed to trigger execution.");
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-md p-4 sm:p-6 text-gray-600 dark:text-gray-300 text-sm sm:text-base transition-opacity">
      <div className="glass-card w-full max-w-5xl max-h-[100dvh] md:max-h-[85vh] flex flex-col overflow-hidden relative shadow-2xl">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 backdrop-blur-sm relative z-20">
          <h3 className="font-extrabold text-xl flex items-center gap-2 text-gray-900 dark:text-gray-100">
            <Zap className="w-6 h-6 text-[#0066FF] fill-[#0066FF]/20" /> OpteraAI Application Agent
          </h3>
          <div className="flex items-center gap-3">
            <button onClick={onClose} className="text-slate-400 dark:text-slate-400 hover:text-gray-900 dark:text-gray-100 transition-colors bg-white dark:bg-slate-800 p-2.5 rounded-full shadow-sm hover:shadow-md border border-slate-200 dark:border-slate-700">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8 scroll-smooth custom-scrollbar bg-slate-50 dark:bg-slate-900/70">
          
          {status === 'loading' && (
             <div className="flex flex-col items-center justify-center h-full gap-5 text-slate-400 dark:text-slate-400">
                <Activity className="w-12 h-12 animate-spin text-[#0066FF]" />
                <p className="font-semibold text-gray-600 dark:text-gray-300">Loading Agent Data...</p>
             </div>
          )}

          {status === 'error' && (
            <div className="flex flex-col items-center justify-center h-full gap-5 text-[#C5192D]">
              <AlertTriangle className="w-14 h-14" />
              <p className="font-bold text-lg">{errorObj}</p>
              <button className="px-6 py-2.5 btn-primary-custom rounded-full mt-4" onClick={fetchSession}>Retry</button>
            </div>
          )}

          {status === 'review' && session && (
            <div className="max-w-4xl mx-auto space-y-10 animate-in fade-in slide-in-from-bottom-6 duration-700">
               <div className="text-center md:text-left mb-6">
                 <h2 className="text-3xl font-extrabold mb-3 text-gray-900 dark:text-gray-100">Review Form Data</h2>
                 <p className="text-gray-600 dark:text-gray-300 text-base">Target Form: <a href={session.form_url} target="_blank" rel="noreferrer" className="text-[#0066FF] font-semibold hover:underline inline-flex items-center gap-1.5">{session.title} <ExternalLink className="w-4 h-4"/></a></p>
               </div>

               <div className="space-y-6">
                 {session.questions.map((q, idx) => {
                   const val = answers[q.id] || '';
                   return (
                     <div key={q.id} className="p-5 md:p-6 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm focus-within:border-[#0066FF]/40 focus-within:ring-4 focus-within:ring-[#0066FF]/10 transition-all">
                       <label className="block mb-3 flex flex-col md:flex-row md:justify-between md:items-center gap-2">
                         <span className="text-gray-900 dark:text-gray-100 font-bold text-lg">{idx + 1}. {q.question_text} {q.is_required && <span className="text-[#C5192D] ml-1">*</span>}</span>
                         {q.is_missing && <span className="text-xs bg-[#FCC30B]/10 text-[#d97706] font-bold px-3 py-1 rounded-full flex items-center gap-1.5 border border-[#FCC30B]/30"><AlertCircle className="w-3.5 h-3.5"/> Missing Info</span>}
                       </label>
                       
                       {q.field_type === 'textarea' ? (
                         <textarea
                           value={val}
                           onChange={e => setAnswers({...answers, [q.id]: e.target.value})}
                           className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 text-gray-900 dark:text-gray-100 min-h-[120px] outline-none focus:bg-white dark:bg-slate-800 transition-colors resize-y font-medium text-base shadow-inner place-content-start"
                         />
                       ) : q.options?.length > 0 ? (
                         <div className="grid sm:grid-cols-2 gap-3 mt-4">
                           {q.options.map((opt, i) => (
                             <label key={i} className="flex items-start gap-4 p-4 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 cursor-pointer hover:bg-[#0066FF]/5 hover:border-[#0066FF]/30 transition-all font-medium text-gray-900 dark:text-gray-100">
                               <input 
                                 type={q.field_type === 'checkbox' ? 'checkbox' : 'radio'}
                                 name={`q_${q.id}`}
                                 checked={q.field_type === 'checkbox' ? val.split(',').map(s=>s.trim()).includes(opt) : val === opt}
                                 onChange={(e) => {
                                   if (q.field_type === 'checkbox') {
                                     let current = val ? val.split(',').map(s=>s.trim()).filter(Boolean) : [];
                                     if (e.target.checked) current.push(opt);
                                     else current = current.filter(c => c !== opt);
                                     setAnswers({...answers, [q.id]: current.join(', ')});
                                   } else {
                                     setAnswers({...answers, [q.id]: opt});
                                   }
                                 }}
                                 className="w-5 h-5 mt-0.5 text-[#0066FF] border-[#cbd5e1] focus:ring-[#0066FF] bg-white dark:bg-slate-800 cursor-pointer"
                               />
                               <span className="leading-tight">{opt}</span>
                             </label>
                           ))}
                         </div>
                       ) : (
                         <input
                           type="text"
                           value={val}
                           onChange={e => setAnswers({...answers, [q.id]: e.target.value})}
                           className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 text-gray-900 dark:text-gray-100 outline-none focus:bg-white dark:bg-slate-800 transition-colors font-medium text-base shadow-inner"
                         />
                       )}
                     </div>
                   );
                 })}
               </div>

               <div className="sticky bottom-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6 rounded-2xl flex flex-col md:flex-row items-center justify-between shadow-[0_-10px_40px_rgba(0,0,0,0.06)] mt-8 z-30">
                 <div className="mb-4 md:mb-0 text-center md:text-left">
                   <h4 className="font-extrabold text-xl text-gray-900 dark:text-gray-100">Execution Mode</h4>
                   <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 font-medium">Choose how the form should be submitted.</p>
                 </div>
                 <div className="flex flex-col sm:flex-row gap-4 items-center w-full md:w-auto">
                   <select 
                      value={fillMode} 
                      onChange={e => setFillMode(e.target.value as any)}
                      className="w-full sm:w-auto bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 font-semibold rounded-xl p-3 text-base text-gray-900 dark:text-gray-100 outline-none focus:border-[#0066FF]/50 shadow-inner"
                   >
                     <option value="auto">Auto Fill & Submit</option>
                     <option value="draft">Draft Only (Review)</option>
                     <option value="manual">Manual Entry in Browser</option>
                   </select>
                   <button 
                     onClick={handleStartAutomation}
                     className="w-full sm:w-auto btn-primary-custom font-extrabold px-8 py-3.5 rounded-xl shadow-lg transition-transform flex items-center justify-center gap-3 text-base"
                   >
                     <Zap className="w-5 h-5 fill-white/20"/> Launch Agent
                   </button>
                 </div>
               </div>
            </div>
          )}

          {status === 'executing' && (
             <div className="max-w-3xl mx-auto py-12 px-4">
               <div className="text-center mb-12">
                 <div className="inline-flex items-center justify-center w-20 h-20 bg-[#0066FF]/10 text-[#0066FF] rounded-full mb-6 relative">
                    <div className="absolute inset-0 bg-[#0066FF]/20 rounded-full animate-ping"></div>
                    <Activity className="w-10 h-10 relative z-10"/>
                 </div>
                 <h2 className="text-4xl font-extrabold text-gray-900 dark:text-gray-100">Execution in Progress</h2>
                 <p className="text-gray-600 dark:text-gray-300 mt-3 font-medium text-lg">OpteraAI autonomous Playwright agent is controlling the browser.</p>
               </div>
               
               <div className="space-y-4">
                 {executionLog.map((log, i) => (
                    <div key={i} className={cn(
                      "p-5 rounded-2xl border-2 flex items-center gap-5 transition-all duration-300 transform",
                      log.status === 'success' ? "border-[#2E9A47]/30 bg-[#2E9A47]/5 shadow-sm" :
                      log.status === 'error' ? "border-[#C5192D]/30 bg-[#C5192D]/5 shadow-sm" :
                      "border-[#0066FF]/40 bg-[#0066FF]/5 shadow-[0_0_20px_rgba(0,102,255,0.1)] scale-[1.02]"
                    )}>
                       <div className="flex-shrink-0">
                         {log.status === 'success' ? <CheckCircle className="w-8 h-8 text-[#2E9A47]"/> : 
                          log.status === 'error' ? <AlertTriangle className="w-8 h-8 text-[#C5192D]"/> :
                          <Activity className="w-8 h-8 text-[#0066FF] animate-pulse"/>}
                       </div>
                       <div>
                          <p className={cn("font-bold text-lg", log.status === 'success' ? "text-[#2E9A47]" : log.status === 'error' ? "text-[#C5192D]" : "text-[#0066FF]")}>{log.step_name}</p>
                          <p className="text-[15px] font-medium text-gray-600 dark:text-gray-300 mt-1 pr-4">{log.message}</p>
                       </div>
                    </div>
                 ))}
               </div>
             </div>
          )}

          {status === 'success' && (
             <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8 slide-in-from-bottom-12 animate-in text-center p-6">
                <div className="relative">
                  <div className="absolute inset-0 bg-[#2E9A47]/20 rounded-full blur-xl scale-150"></div>
                  <div className="w-28 h-28 rounded-full bg-gradient-to-tr from-[#2E9A47] to-[#4ade80] text-white flex items-center justify-center border-4 border-white shadow-2xl relative z-10 transform hover:rotate-12 transition-transform duration-500">
                    <CheckCircle className="w-14 h-14" strokeWidth={2.5}/>
                  </div>
                </div>
                <div>
                   <h2 className="text-4xl sm:text-5xl font-extrabold text-gray-900 dark:text-gray-100 tracking-tight">Application Complete!</h2>
                   <p className="text-gray-600 dark:text-gray-300 mt-4 max-w-lg mx-auto text-lg font-medium leading-relaxed">The Application Form has been successfully finalized. All records have been persisted to knowledge store.</p>
                </div>
                <button onClick={onClose} className="mt-4 px-10 py-4 bg-[#222222] hover:bg-black text-white font-extrabold text-lg rounded-full transition-all shadow-xl hover:shadow-2xl hover:-translate-y-1">
                   Return to Inbox
                </button>
             </div>
          )}
        </div>
      </div>
    </div>
  );
}
