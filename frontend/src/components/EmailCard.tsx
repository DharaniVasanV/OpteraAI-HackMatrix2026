import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  Mail, AlertCircle, CheckCircle2, CalendarPlus, ExternalLink,
  ChevronDown, ChevronUp, Loader2, Link2, Clock, Users,
  Building2, Tag, Lightbulb, RefreshCw, Cpu, ShieldAlert,
  Trophy, FileText, Zap, Info, BookOpen, Send
} from 'lucide-react';
import { cn } from '../lib/utils';

export const sentimentColor = (s: string) => {
  if (!s) return 'text-slate-400';
  const l = s.toLowerCase();
  if (l === 'positive') return 'text-green-400';
  if (l === 'negative') return 'text-red-400';
  if (l === 'mixed') return 'text-yellow-400';
  return 'text-slate-400';
};

export function Section({ icon: Icon, label, color = 'text-slate-400', children }: {
  icon: any; label: string; color?: string; children: React.ReactNode;
}) {
  return (
    <div className="bg-slate-900/60 rounded-lg p-3">
      <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1 ${color}`}>
        <Icon className="w-3 h-3" />{label}
      </h4>
      {children}
    </div>
  );
}

export function Pill({ children, variant = 'default' }: { children: React.ReactNode; variant?: 'default' | 'primary' | 'green' | 'yellow' | 'red' }) {
  const cls = {
    default: 'bg-slate-800 text-slate-300',
    primary: 'bg-primary/10 text-primary',
    green: 'bg-green-500/10 text-green-400',
    yellow: 'bg-yellow-500/10 text-yellow-400',
    red: 'bg-red-500/10 text-red-400',
  }[variant];
  return <span className={`px-2 py-0.5 rounded-full text-xs ${cls}`}>{children}</span>;
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
  // old DB compatibility
  timestamp?: string;
}

// For Auto Apply status tracking
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
  const [expanded, setExpanded] = useState(false);
  const [research, setResearch] = useState<ResearchData | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  
  const [calendarStatus, setCalendarStatus] = useState<StatusState>('idle');
  const [calendarMsg, setCalendarMsg] = useState('');
  
  const [applyStatus, setApplyStatus] = useState<StatusState>('idle');
  const [applyMsg, setApplyMsg] = useState('');

  const body = email.body || email.email_body || '';

  // Determine if this is a form.
  const hasFormUrl = /(docs\.google\.com\/forms|forms\.gle|forms\.microsoft\.com|forms\.office\.com|typeform\.com)/i.test(body + ' ' + (email.meeting_link || ''));
  const isFormCategory = email.category?.toLowerCase() === 'form';
  const isForm = hasFormUrl || isFormCategory;
  const canAutoApply = isForm; // 1-click Auto Apply only for forms


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

  const toggle = () => {
    const next = !expanded;
    setExpanded(next);
    if (next && !research && body) analyzeWithResearch();
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
    
    // Find the best link to apply to
    let targetUrl = '';
    if (research?.urls && research.urls.length > 0) {
      targetUrl = research.urls[0];
    } else if (email.meeting_link) {
      targetUrl = email.meeting_link;
    } else {
      // Basic fallback to extract first http link from body
      const urlMatch = body.match(/https?:\/\/[^\s"'><]+/);
      targetUrl = urlMatch ? urlMatch[0] : '';
    }

    if (!targetUrl) {
      setApplyStatus('error');
      setApplyMsg('No form URL found in email. Please analyze out first.');
      return;
    }

    try {
      const res = await axios.post('/api/filler/start-form', { 
        form_url: targetUrl
      });
      if (res.data.redirect_url) {
        window.open(`http://localhost:8007${res.data.redirect_url}`, '_blank');
      }
      setApplyStatus('done');
      setApplyMsg('Application Started - Review Panel Opened!');
    } catch (err: any) {
      setApplyStatus('error');
      setApplyMsg(err.response?.data?.detail || 'Filler failed');
    }
  };

  return (
    <div className="glass-panel rounded-xl overflow-hidden transition-all">
      <div className="p-5 flex items-start justify-between cursor-pointer hover:bg-slate-800/30" onClick={toggle}>
        <div className="flex items-center space-x-4 flex-1 min-w-0">
          <div className="w-11 h-11 rounded-full bg-slate-800 flex-shrink-0 flex items-center justify-center">
            {email.category === 'Meeting' ? <CalendarPlus className="w-5 h-5 text-blue-400" /> :
             email.category === 'Internship' ? <Tag className="w-5 h-5 text-green-400" /> :
             email.category === 'Hackathon' ? <Lightbulb className="w-5 h-5 text-yellow-400" /> :
             <Mail className="w-5 h-5 text-slate-400" />}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg text-white truncate pr-4">
              {email.title || email.subject || 'Untitled Communication'}
            </h3>
            <div className="flex items-center space-x-3 text-sm text-slate-400 mt-1">
              <span className="truncate">{email.sender}</span>
              <span>•</span>
              <span className="whitespace-nowrap">{email.date || email.timestamp || 'Recent'}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-3 ml-4 flex-shrink-0">
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${priorityColor(email.priority_score)} border-current/20`}>
            Priority: {email.priority_score}%
          </span>
          <span className="px-3 py-1 bg-slate-800 text-slate-300 rounded-full text-xs font-medium">
            {email.category}
          </span>
          {expanded ? <ChevronUp className="w-5 h-5 text-slate-500" /> : <ChevronDown className="w-5 h-5 text-slate-500" />}
        </div>
      </div>

      {expanded && (
        <div className="p-5 border-t border-slate-800 bg-slate-900/30 space-y-5">
          <div className="bg-slate-900/60 p-4 rounded-lg">
            <h4 className="text-sm font-semibold text-slate-300 mb-2">Original Content</h4>
            <div className="text-sm text-slate-400 whitespace-pre-wrap max-h-60 overflow-y-auto custom-scrollbar">
              {body}
            </div>
          </div>

          {analyzing && (
            <div className="flex items-center justify-center py-6 text-primary">
              <Loader2 className="w-6 h-6 animate-spin mr-3" />
              <span className="font-medium">Research Agent is analyzing content...</span>
            </div>
          )}

          {research && !analyzing && (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-primary" /> Research Analysis
                </h3>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400">Confidence: </span>
                  <span className={research.confidence && research.confidence > 0.8 ? "text-green-400" : "text-yellow-400"}>
                    {research.confidence ? (research.confidence * 100).toFixed(0) : '?'}%
                  </span>
                  <span className="text-slate-600 mx-1">|</span>
                  <span className={sentimentColor(research.sentiment || '')}>{research.sentiment || 'Neutral'}</span>
                </div>
              </div>

              {research.summary && (
                <div className="text-slate-300 text-sm leading-relaxed border-l-2 border-primary pl-3 bg-slate-800/30 py-2">
                  {research.summary}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {research.key_points && research.key_points.length > 0 && (
                  <Section icon={Lightbulb} label="Key Points" color="text-yellow-400">
                    <ul className="space-y-1">
                      {research.key_points.map((p, i) => <li key={i} className="text-xs text-slate-300">• {p}</li>)}
                    </ul>
                  </Section>
                )}

                {research.important_dates && research.important_dates.length > 0 && (
                  <Section icon={Clock} label="Important Dates" color="text-emerald-400">
                    <div className="space-y-2">
                      {research.important_dates.map((d, i) => (
                        <div key={i} className="bg-slate-800 rounded p-2 text-xs">
                          <div className="font-bold text-emerald-400">{d.date} {d.time}</div>
                          <div className="text-slate-300">{d.event}</div>
                        </div>
                      ))}
                    </div>
                  </Section>
                )}
              </div>

              <div className="flex flex-wrap gap-2 text-xs">
                {research.people && research.people.map((p, i) => (
                  <span key={i} className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded-md flex items-center gap-1 border border-blue-500/20">
                    <Users className="w-3 h-3" /> {p.name} {p.role && `(${p.role})`}
                  </span>
                ))}
                {research.organizations && research.organizations.map((o, i) => (
                  <span key={i} className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded-md flex items-center gap-1 border border-purple-500/20">
                    <Building2 className="w-3 h-3" /> {o}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center flex-wrap gap-3 pt-2 border-t border-slate-800">
            {(!showMeetingTrigger) && (
              <button
                onClick={addToCalendar}
                disabled={calendarStatus === 'loading' || calendarStatus === 'done'}
                className={cn(
                  'flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  calendarStatus === 'done' ? 'bg-green-500/20 text-green-400' :
                  calendarStatus === 'error' ? 'bg-red-500/20 text-red-400' :
                  'bg-primary/10 text-primary hover:bg-primary/20'
                )}
              >
                {calendarStatus === 'loading' ? <Loader2 className="w-4 h-4 animate-spin" /> : <CalendarPlus className="w-4 h-4" />}
                <span>{calendarStatus === 'done' ? 'Added!' : calendarStatus === 'error' ? 'Failed' : calendarStatus === 'loading' ? 'Adding…' : 'Add to Calendar'}</span>
              </button>
            )}

            {calendarMsg && <span className="text-xs text-slate-400">{calendarMsg}</span>}

            {canAutoApply && (
              <button
                onClick={triggerAutoApply}
                disabled={applyStatus === 'loading' || applyStatus === 'done'}
                className={cn(
                  'flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  applyStatus === 'done' ? 'bg-green-500/20 text-green-400' :
                  applyStatus === 'error' ? 'bg-red-500/20 text-red-400' :
                  'bg-violet-600 hover:bg-violet-700 text-white shadow-[0_0_15px_rgba(139,92,246,0.3)]'
                )}
              >
                {applyStatus === 'loading' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                <span>{applyStatus === 'done' ? 'Filled!' : applyStatus === 'error' ? 'Failed' : applyStatus === 'loading' ? 'Auto-Filling…' : 'AI Auto-Fill'}</span>
              </button>
            )}

            {showMeetingTrigger && (
              <button
                onClick={() => onMeetingStart && onMeetingStart(email, research || undefined)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 rounded-lg text-sm font-medium transition-colors"
                title="Send this meeting directly to Meeting Agent Bot to join"
              >
                <Cpu className="w-4 h-4" />
                <span>Send to Meeting Bot</span>
              </button>
            )}

            {!research && !analyzing && body && (
              <button onClick={analyzeWithResearch} className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors">
                <RefreshCw className="w-4 h-4" /><span>Re-analyze</span>
              </button>
            )}

            {email.meeting_link && (
              <a href={email.meeting_link} target="_blank" rel="noreferrer" className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors">
                <ExternalLink className="w-4 h-4" /><span>Open Link</span>
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
