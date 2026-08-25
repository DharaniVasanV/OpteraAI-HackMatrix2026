import React, { useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import {
  Mail, AlertCircle, CheckCircle2, CalendarPlus, ExternalLink,
  ChevronDown, ChevronUp, Loader2, Link2, Clock, Users,
  Building2, Tag, Lightbulb, RefreshCw, Cpu, ShieldAlert,
  Trophy, FileText, Zap, Info, BookOpen, Send, Folder, User, Calendar as CalendarIcon, X
} from 'lucide-react';
import { cn } from '../lib/utils';
import { FillerModal } from './FillerModal';

export const sentimentColor = (s: string) => {
  if (!s) return 'text-gray-600 dark:text-gray-300 font-medium';
  const l = s.toLowerCase();
  if (l === 'positive') return 'text-green-400';
  if (l === 'negative') return 'text-red-400';
  if (l === 'mixed') return 'text-yellow-400';
  return 'text-gray-600 dark:text-gray-300 font-medium';
};

export function Section({ icon: Icon, label, color = 'text-gray-600 dark:text-gray-300 font-medium', children }: {
  icon: any; label: string; color?: string; children: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm/60 rounded-xl p-4">
      <h4 className={`text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5 ${color}`}>
        <Icon className="w-4 h-4" />{label}
      </h4>
      {children}
    </div>
  );
}

export interface ResearchData {
  content_type?: string;
  title?: string;
  summary?: string;
  key_points?: string[];
  people?: { name: string; role: string }[];
  organizations?: string[];
  technologies?: string[];
  urls?: string[];
  important_dates?: { event: string; date: string; time: string; description: string }[];
  tasks?: { task: string; assigned_to?: string | null; deadline?: string | null; priority?: string | null; status?: string | null; description?: string }[];
  decisions?: { decision: string; reason: string; impact: string }[];
  risks?: string[];
  opportunities?: string[];
  keywords?: string[];
  categories?: string[];
  missing_information?: string[];
  recommended_next_agent?: string[];
  sentiment?: string;
  confidence?: number;
  provider_used?: string;
}

export interface Email {
  id: string;
  title?: string;
  subject?: string;
  sender: string;
  date: string;
  category: string;
  priority: string;
  priority_score: number;
  body?: string;
  email_body?: string;
  meeting_link?: string;
  tasks?: string[];
  research_id?: string;
  timestamp?: string;
}

export type StatusState = 'idle' | 'loading' | 'done' | 'error';

export const priorityColor = (score: number) =>
  score > 80 ? 'bg-red-500/20 text-red-400' :
  score > 50 ? 'bg-yellow-500/20 text-yellow-400' :
  'bg-green-500/20 text-green-400';

export function EmailCard({ 
    email, 
    showAutoApply = false,
    showMeetingTrigger = false,
    onMeetingStart = () => {}
}: { 
    email: Email, 
    showAutoApply?: boolean,
    showMeetingTrigger?: boolean,
    onMeetingStart?: (m: Email, r?: ResearchData) => void,
}) {
  const [showModal, setShowModal] = useState(false);
  const [research, setResearch] = useState<ResearchData | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  
  const [calendarStatus, setCalendarStatus] = useState<StatusState>('idle');
  const [calendarMsg, setCalendarMsg] = useState('');
  
  const [applyStatus, setApplyStatus] = useState<StatusState>('idle');
  const [applyMsg, setApplyMsg] = useState('');
  
  const [showFillerModal, setShowFillerModal] = useState(false);
  const [fillerUrl, setFillerUrl] = useState('');
  
  const [activeTab, setActiveTab] = useState<'mail' | 'research'>('mail');

  const body = email.body || email.email_body || '';

  const hasFormUrl = /(docs\.google\.com\/forms|forms\.gle|forms\.microsoft\.com|forms\.office\.com|typeform\.com|unstop\.com|devpost\.com|hackerearth\.com)/i.test(body + ' ' + (email.meeting_link || ''));
  const isFormCategory = email.category?.toLowerCase() === 'form' || email.category?.toLowerCase() === 'hackathon';
  const isForm = hasFormUrl || isFormCategory;
  const canAutoApply = isForm; 

  const getPlatform = () => {
     if(hasFormUrl) {
         if (body.includes("google.com/forms") || body.includes("forms.gle")) return 'Google Forms';
         if (body.includes("unstop.com")) return 'Unstop';
         if (body.includes("devpost.com")) return 'Devpost';
         return 'Web Form';
     }
     if(email.category?.toLowerCase() === 'meeting') return 'Google Meet';
     return email.category || 'General';
  }

  const analyzeWithResearch = useCallback(async () => {
    if (!body.trim()) return;
    setAnalyzing(true);
    try {
      if ((email as any).research_id) {
        try {
          const res = await axios.get(`/api/research/analyses/${(email as any).research_id}`);
          setResearch(res.data.analysis || res.data.structured_data || res.data);
          setAnalyzing(false);
          return;
        } catch (err) {
          console.error('Failed to load existing research, re-analyzing:', err);
        }
      }
      
      const res = await axios.post('/api/research/analyze', { content: body, email_id: email.id });
      setResearch(res.data.analysis || res.data);
    } catch (err) {
      console.error('Research failed:', err);
    } finally {
      setAnalyzing(false);
    }
  }, [body, email]);

  const openModal = () => {
    setShowModal(true);
    if (!research && body) analyzeWithResearch();
  };

  const addToCalendar = async () => {
    setCalendarStatus('loading');
    const title = email.title || email.subject || 'Email Event';
    const dates = research?.important_dates?.[0];

    const payload = {
      title,
      description: research?.summary || body.slice(0, 500),
      event_type: email.category || 'Email',
      start_datetime: dates?.date || email.date || email.timestamp || new Date().toISOString(),
      end_datetime: dates?.date || email.date || email.timestamp || new Date(Date.now() + 3600000).toISOString(),
      location: null,
      meeting_link: email.meeting_link || null,
      source: 'Watcher',
      ai_created: true,
    };

    try {
      await axios.post('/api/calendar/add', payload);
      setCalendarStatus('done');
      setCalendarMsg('Added to Google Calendar!');
    } catch (err: any) {
      setCalendarStatus('error');
      setCalendarMsg(err.response?.data?.detail || 'Calendar agent unavailable');
    }
  };

  const triggerAutoApply = async () => {
    setApplyStatus('loading');
    
    let targetUrl = '';
    if (research?.urls && research.urls.length > 0) {
      targetUrl = research.urls[0];
    } else if (email.meeting_link) {
      targetUrl = email.meeting_link;
    } else {
      const urlMatch = body.match(/https?:\/\/[^\s"'><]+/);
      targetUrl = urlMatch ? urlMatch[0] : '';
    }

    if (!targetUrl) {
      setApplyStatus('error');
      setApplyMsg('No form URL found in email.');
      return;
    }

    try {
      const res = await axios.post('/api/filler/start-form', { 
        form_url: targetUrl
      });
      if (res.data.session_id) {
        setFillerUrl(`${res.data.session_id}`);
        setShowFillerModal(true);
      }
      setApplyStatus('done');
      setApplyMsg('Application Started!');
    } catch (err: any) {
      setApplyStatus('error');
      setApplyMsg(err.response?.data?.detail || 'Filler failed');
    }
  };

  return (
    <>
      <div 
        className="glass-card flex flex-col bg-white dark:bg-[#0b1021] border border-slate-200 dark:border-[#1e293b]/80 hover:border-[#0066FF]/40 rounded-2xl overflow-hidden cursor-pointer shadow-sm dark:shadow-black/20 hover:shadow-md dark:hover:shadow-black/40 transition-all duration-300 relative group"
        onClick={openModal}
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-violet-500 rounded-full blur-[70px] opacity-[0.03] group-hover:opacity-10 transition-opacity"></div>
        
        {/* Badges / Header Row */}
        <div className="px-4 py-4 pb-2 flex flex-wrap gap-2 items-center text-[10px] uppercase font-bold tracking-wider">
          <span className="px-2.5 py-1 bg-violet-100 dark:bg-[#8B5CF6]/10 text-violet-700 dark:text-violet-400 rounded flex gap-1.5 items-center border border-violet-200 dark:border-violet-500/20">
            <Folder className="w-3 h-3" /> {email.category || 'General'}
          </span>
          <span className="px-2.5 py-1 bg-blue-50 dark:bg-[#0066FF]/10 text-blue-700 dark:text-blue-400 rounded flex gap-1.5 items-center border border-blue-200 dark:border-[#0066FF]/20">
            <img src="/logo.png" className="w-3 h-3 opacity-90" alt="" /> {getPlatform()}
          </span>
          <span className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-400 rounded flex gap-1.5 items-center border border-slate-200 dark:border-slate-700/50">
            Flag: {email.priority_score}%
          </span>
        </div>

        {/* Content Block */}
        <div className="px-4 py-2 flex-col flex-1 flex">
          <h3 className="font-extrabold text-slate-900 dark:text-blue-50 text-[15px] leading-tight mb-2 line-clamp-2">
            {email.title || email.subject || 'Untitled'}
          </h3>
          <p className="text-slate-600 dark:text-slate-400 text-xs line-clamp-2 leading-relaxed">
            {body || "No additional description provided."}
          </p>
        </div>

        {/* Separator */}
        <div className="mx-4 my-3 border-t border-slate-200 dark:border-slate-800/80"></div>

        {/* Table Details */}
        <div className="px-4 pb-4 space-y-2.5 text-xs">
          <div className="flex justify-between items-center text-slate-700 dark:text-slate-300">
            <span className="flex items-center gap-2 text-slate-500 font-medium"><User className="w-3.5 h-3.5" /> Sender</span>
            <span className="font-bold truncate max-w-[150px]">{email.sender}</span>
          </div>
          <div className="flex justify-between items-center text-slate-700 dark:text-slate-300">
            <span className="flex items-center gap-2 text-slate-500 font-medium"><CalendarIcon className="w-3.5 h-3.5" /> Last Date</span>
            <span className="font-bold truncate">{email.date || email.timestamp || 'Not Specified'}</span>
          </div>
          {(email.meeting_link || hasFormUrl) && (
            <div className="flex justify-between items-center">
              <span className="flex items-center gap-2 text-blue-600 dark:text-blue-400/80 font-medium"><Folder className="w-3.5 h-3.5" /> Link</span>
              <a 
                href={email.meeting_link || targetUrlFallback(body)} 
                target="_blank" 
                onClick={(e) => e.stopPropagation()} 
                className="font-bold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 hover:underline truncate max-w-[130px]"
              >
                {email.meeting_link || targetUrlFallback(body)}
              </a>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-4 pb-4 pt-1 flex gap-2">
          <a 
            href={email.meeting_link || targetUrlFallback(body) || '#'} 
            target="_blank"
            onClick={(e) => e.stopPropagation()}
            className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800/80 dark:hover:bg-slate-700/80 dark:text-slate-300 border border-slate-200 dark:border-slate-700/50 rounded-lg py-2 flex items-center justify-center gap-1.5 text-xs font-bold transition-all"
          >
           <ExternalLink className="w-3.5 h-3.5" /> Open Manually
          </a>
          
          {canAutoApply && (
            <button 
              onClick={(e) => { e.stopPropagation(); triggerAutoApply(); }} 
              disabled={applyStatus !== 'idle'} 
              className="flex-1 bg-[#0066FF] hover:bg-blue-600 border border-blue-500 rounded-lg py-2 flex items-center justify-center gap-1.5 text-xs text-white font-extrabold transition-all shadow-md shadow-blue-500/20"
            >
              {applyStatus === 'loading' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 text-yellow-300" />} AI Auto-Fill
            </button>
          )}

          <button onClick={(e) => { e.stopPropagation(); openModal(); }} className="px-3 bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-500 dark:bg-slate-800/50 dark:hover:bg-slate-800 dark:border-slate-700/50 dark:hover:border-slate-600 rounded-lg flex items-center justify-center dark:text-slate-400 transition-colors">
            <Cpu className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Pop-up Modal overlay for Research Agent details via Portal to escape all z-index traps */}
      {showModal && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6" onClick={() => setShowModal(false)}>
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm"></div>
          
          <div className="bg-white dark:bg-[#0b1021] border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col relative z-10 shadow-2xl animate-in slide-in-from-bottom-4 zoom-in-95 duration-200" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header Tabs */}
            <div className="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-[#12182b]">
               <div className="flex gap-4 sm:gap-6 items-center overflow-x-auto custom-scrollbar pr-4">
                 <button onClick={() => setActiveTab('mail')} className={`text-sm sm:text-lg font-extrabold pb-1 border-b-2 transition-colors flex items-center gap-1.5 sm:gap-2 whitespace-nowrap ${activeTab === 'mail' ? 'border-[#0066FF] text-[#0066FF]' : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}`}>
                   <Mail className="w-4 h-4 sm:w-5 sm:h-5"/> Mail
                 </button>
                 <button onClick={() => { setActiveTab('research'); if(!research && !analyzing && body) analyzeWithResearch(); }} className={`text-sm sm:text-lg font-extrabold pb-1 border-b-2 transition-colors flex items-center gap-1.5 sm:gap-2 whitespace-nowrap ${activeTab === 'research' ? 'border-[#0066FF] text-[#0066FF]' : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}`}>
                   <Cpu className="w-4 h-4 sm:w-5 sm:h-5" /> Research Analysis
                 </button>
               </div>
               <button onClick={() => setShowModal(false)} className="p-2 flex-shrink-0 rounded-full hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors">
                 <X className="w-5 h-5"/>
               </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-8 custom-scrollbar">
               {/* Header Info (Always Visible) */}
               <div>
                  <h2 className="text-2xl font-black text-gray-900 dark:text-gray-100 mb-2">{email.title || email.subject}</h2>
                  <div className="flex items-center gap-3 text-sm font-semibold text-slate-500">
                    <span className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/50 px-2.5 py-1 rounded-md"><User className="w-4 h-4"/> {email.sender}</span>
                    <span className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/50 px-2.5 py-1 rounded-md"><CalendarIcon className="w-4 h-4"/> {email.date || email.timestamp}</span>
                    <span className="flex items-center gap-1.5 bg-violet-100/50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-400 px-2.5 py-1 rounded-md"><Folder className="w-4 h-4"/> {email.category}</span>
                  </div>
               </div>

               {/* Raw Email */}
               {activeTab === 'mail' && (
                 <div className="bg-slate-50 dark:bg-slate-900/50 p-5 rounded-xl border border-slate-200 dark:border-slate-800/50 animate-in fade-in">
                   <h4 className="text-sm font-extrabold text-gray-900 dark:text-gray-200 mb-3 uppercase tracking-wider">Raw Input Data</h4>
                   <div className="text-[14px] text-gray-600 dark:text-gray-400 whitespace-pre-wrap font-medium">
                     {body}
                   </div>
                 </div>
               )}

               {/* Research Section */}
               {activeTab === 'research' && (
                 <div className="animate-in fade-in">
                   {analyzing ? (
                     <div className="flex flex-col items-center justify-center py-12 text-[#0066FF] bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-900/20">
                       <Loader2 className="w-8 h-8 animate-spin mb-4" />
                       <span className="font-extrabold text-lg">Research Agent is constructing entity map...</span>
                     </div>
                   ) : research ? (
                     <div className="space-y-6">
                       <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
                         <h3 className="text-lg font-black text-gray-900 dark:text-gray-100 flex items-center gap-2">
                           <Zap className="w-5 h-5 text-yellow-500" /> Deep Analysis Results
                         </h3>
                         <div className="flex items-center gap-2 text-xs font-bold bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
                           <span className="text-slate-500">Confidence: </span>
                           <span className={research.confidence && research.confidence > 0.8 ? "text-[#2E9A47]" : "text-[#d97706]"}>
                             {research.confidence ? (research.confidence * 100).toFixed(0) : '?'}%
                           </span>
                         </div>
                       </div>

                       {research.summary && (
                         <div className="text-gray-900 dark:text-gray-200 font-semibold text-sm sm:text-[15px] leading-relaxed border-l-[3px] border-[#0066FF] pl-4 sm:pl-5 py-2 break-words">
                           {research.summary}
                         </div>
                       )}

                       <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                         {research.key_points && research.key_points.length > 0 && (
                           <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
                             <h4 className="text-xs font-black uppercase tracking-widest text-[#d97706] flex items-center gap-2 mb-4"><Lightbulb className="w-4 h-4"/> Key Takeaways</h4>
                             <ul className="space-y-3">
                               {research.key_points.map((p, i) => <li key={i} className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-start gap-3"><span className="text-[#FCC30B] mt-0.5">•</span> <span>{p}</span></li>)}
                             </ul>
                           </div>
                         )}

                         {research.important_dates && research.important_dates.length > 0 && (
                           <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
                             <h4 className="text-xs font-black uppercase tracking-widest text-[#2E9A47] flex items-center gap-2 mb-4"><Clock className="w-4 h-4"/> Strict Deadlines</h4>
                             <div className="space-y-3">
                               {research.important_dates.map((d, i) => (
                                 <div key={i} className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/50 rounded-lg p-3">
                                   <div className="font-extrabold text-[#2E9A47] mb-1">{d.date} {d.time}</div>
                                   <div className="text-sm text-gray-700 dark:text-gray-300 font-semibold">{d.event}</div>
                                 </div>
                               ))}
                             </div>
                           </div>
                         )}
                       </div>

                       <div className="flex flex-wrap gap-2 text-xs font-bold pt-2">
                         {research.people && research.people.map((p, i) => (
                           <span key={i} className="px-3 py-1.5 bg-blue-50 dark:bg-[#0066FF]/10 text-blue-600 dark:text-[#0066FF] rounded-lg flex items-center gap-2 border border-blue-100 dark:border-[#0066FF]/20">
                             <Users className="w-3.5 h-3.5" /> {p.name} {p.role && <span className="opacity-70 font-medium">({p.role})</span>}
                           </span>
                         ))}
                         {research.organizations && research.organizations.map((o, i) => (
                           <span key={i} className="px-3 py-1.5 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded-lg flex items-center gap-2 border border-purple-100 dark:border-purple-900/30">
                             <Building2 className="w-3.5 h-3.5" /> {o}
                           </span>
                         ))}
                       </div>
                     </div>
                   ) : (
                     <div className="flex flex-col items-center justify-center py-10 bg-slate-50 dark:bg-slate-900/30 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
                        <p className="text-slate-500 font-bold mb-4">Research Agent data unavailable.</p>
                        <button onClick={analyzeWithResearch} className="px-5 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-gray-900 dark:text-gray-100 font-bold rounded-lg transition-colors flex items-center gap-2 shadow-sm">
                          <RefreshCw className="w-4 h-4"/> Force Deep Dive
                        </button>
                     </div>
                   )}
                 </div>
               )}
            </div>

            {/* Modal Footer Actions */}
            <div className="px-4 sm:px-6 py-4 sm:py-5 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#12182b] flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              <button
                onClick={addToCalendar}
                disabled={calendarStatus === 'loading' || calendarStatus === 'done' || !research}
                className={cn(
                  'flex flex-1 sm:flex-none justify-center items-center space-x-2 px-4 sm:px-6 py-3 rounded-xl text-sm font-extrabold transition-all border shadow-sm',
                  calendarStatus === 'done' ? 'bg-[#2E9A47] text-white border-transparent' :
                  calendarStatus === 'error' ? 'bg-[#C5192D]/10 text-[#C5192D] border-[#C5192D]/30' :
                  'bg-white dark:bg-slate-800 text-[#0066FF] border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50'
                )}
              >
                {calendarStatus === 'loading' ? <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" /> : <CalendarPlus className="w-4 h-4 flex-shrink-0" />}
                <span className="truncate">{calendarStatus === 'done' ? 'Added!' : calendarStatus === 'error' ? 'Failed to Add' : 'Add to Calendar'}</span>
              </button>

              {showMeetingTrigger && (
                <button
                  onClick={() => onMeetingStart && onMeetingStart(email, research || undefined)}
                  className="flex flex-1 sm:flex-none justify-center items-center space-x-2 px-4 sm:px-6 py-3 bg-[#0066FF] text-white hover:bg-blue-600 rounded-xl text-sm font-extrabold transition-colors shadow-md shadow-blue-500/20"
                >
                  <Cpu className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate">Send to Meeting Bot</span>
                </button>
              )}
              
              <div className="flex-1 hidden sm:block"></div>
              {calendarMsg && calendarStatus === 'error' && (
                <span className="text-xs font-bold text-red-500 w-full text-center sm:text-right sm:ml-auto">{calendarMsg}</span>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}

      {showFillerModal && fillerUrl && (
        <FillerModal sessionId={fillerUrl} onClose={() => setShowFillerModal(false)} />
      )}
    </>
  );
}

function targetUrlFallback(body: string) {
  const m = body.match(/https?:\/\/[^\s"'><]+/);
  return m ? m[0] : '#';
}
