import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { Loader2, CalendarPlus, Cpu, RefreshCw, Trash2, Edit2, Play, Users, FileText, CheckCircle2, X } from 'lucide-react';
import { Email, EmailCard } from '../components/EmailCard';

interface Meeting {
  id: string;
  title: string;
  organizer: string;
  meeting_url: string;
  platform: string;
  meeting_date: string;
  start_time: string;
  end_time: string;
  status: string;
  bot_joined: boolean;
  transcript: string;
}

export default function Meetings() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  
  const [loadingEmails, setLoadingEmails] = useState(true);
  const [loadingMeetings, setLoadingMeetings] = useState(true);
  const [error, setError] = useState('');

  // Modals state
  const [transcriptModal, setTranscriptModal] = useState<string | null>(null);
  const [editModal, setEditModal] = useState<Meeting | null>(null);
  const [reformatting, setReformatting] = useState(false);

  const fetchInbox = useCallback(async () => {
    try {
      const res = await axios.get('/api/inbox');
      const filtered = res.data.filter((e: Email) => 
        e.category?.toLowerCase() === 'meeting' || 
        e.category?.toLowerCase() === 'schedule'
      );
      setEmails(filtered);
    } catch {
      console.error('Failed to fetch inbox records.');
    } finally {
      setLoadingEmails(false);
    }
  }, []);

  const fetchMeetings = useCallback(async () => {
    try {
      const res = await axios.get('/api/meetings');
      setMeetings(res.data);
    } catch {
      setError('Failed to fetch active meetings.');
    } finally {
      setLoadingMeetings(false);
    }
  }, []);

  useEffect(() => { 
    fetchInbox(); 
    fetchMeetings();
  }, [fetchInbox, fetchMeetings]);

  // Actions
  const addToBotMeetings = async (email: Email, research?: any) => {
    try {
      let r_date = null;
      let r_time = null;
      if (research?.important_dates && research.important_dates.length > 0) {
          const dt = research.important_dates[0];
          r_date = dt.date;
          r_time = dt.time;
      }
      
      let meetingUrl = email.meeting_link;
      if (!meetingUrl && research?.urls) {
        meetingUrl = research.urls.find((u: string) => /meet\.google|zoom\.us|teams\.microsoft|webex/i.test(u));
      }
      if (!meetingUrl) {
          const m = (email.body || email.email_body || '').match(/https?:\/\/(meet\.google\.com|zoom\.us|teams\.microsoft\.com)\/[^\s"'>]+/);
          if (m) meetingUrl = m[0];
      }
      
      const payload = {
        title: email.title || email.subject || 'Watcher Extracted Meeting',
        meeting_url: meetingUrl || 'https://meet.google.com/test-bot',
        organizer: email.sender,
        status: 'scheduled',
        meeting_date: r_date,
        start_time: r_time
      };
      await axios.post('/api/meetings', payload);
      await fetchMeetings(); // reload active meetings
      alert("Successfully pushed email into Autonomous Bot schedule!");
    } catch (err: any) {
      alert("Failed saving to bot DB: " + (err.response?.data?.detail || err.message));
    }
  }

  const triggerBot = async (meetingId: string) => {
    try {
      await axios.post(`/api/meetings/${meetingId}/trigger`);
      alert("Bot spawn triggered! Check terminal logs.");
      fetchMeetings();
    } catch(err:any) {
      alert("Trigger failed: " + (err.response?.data?.detail || err.message));
    }
  }

  const identifyNames = async (meetingId: string) => {
    setReformatting(true);
    try {
      await axios.post(`/api/meetings/${meetingId}/reformat`);
      alert("Speaker identification complete.");
      fetchMeetings();
      setTranscriptModal(null);
    } catch(err:any) {
      alert("Identification failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setReformatting(false);
    }
  }

  const deleteMeeting = async (meetingId: string) => {
    if(!window.confirm("Delete meeting?")) return;
    try {
      await axios.delete(`/api/meetings/${meetingId}`);
      fetchMeetings();
    } catch(err) {
      alert("Delete failed.");
    }
  }



  const saveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if(!editModal) return;
    try {
      await axios.put(`/api/meetings/${editModal.id}`, editModal);
      setEditModal(null);
      fetchMeetings();
    } catch(err) {
      alert("Failed updating meeting.");
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'scheduled': return 'bg-blue-500/20 text-blue-400 border border-blue-500/40';
      case 'joining': return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40';
      case 'in_progress': return 'bg-green-500/20 text-green-400 border border-green-500/40 animate-pulse';
      case 'completed': return 'bg-purple-500/20 text-purple-400 border border-purple-500/40';
      case 'failed': return 'bg-red-500/20 text-red-400 border border-red-500/40';
      default: return 'bg-slate-500/20 text-slate-400 border border-slate-500/40';
    }
  };

  const getPlatformIcon = (platform: string) => {
    const p = platform?.toLowerCase() || '';
    if (p.includes('zoom')) return '🔵 Zoom';
    if (p.includes('teams')) return '🟣 Teams';
    if (p.includes('meet')) return '🟢 GMeet';
    return '🌐 Web';
  };

  const completedCount = meetings.filter(m => m.status === 'completed').length;
  const inProgressCount = meetings.filter(m => m.status === 'in_progress').length;
  const scheduledCount = meetings.filter(m => m.status === 'scheduled').length;

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Meetings Agent Hub</h1>
          <p className="text-slate-400 text-sm">
            Autonomous joining, transcript analysis, and inbox integration
          </p>
        </div>
        <div className="flex gap-3">

          <button onClick={fetchMeetings} className="flex items-center space-x-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg text-sm font-semibold transition-colors">
            {loadingMeetings ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            <span>Refresh Dashboard</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* STATS ROW */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Meetings', val: meetings.length, color: 'text-white' },
          { label: 'Scheduled', val: scheduledCount, color: 'text-blue-400' },
          { label: 'In Progress', val: inProgressCount, color: 'text-green-400' },
          { label: 'Completed', val: completedCount, color: 'text-purple-400' },
        ].map(s => (
          <div key={s.label} className="glass-panel p-5 rounded-xl text-center">
            <div className={`text-3xl font-bold ${s.color} mb-1`}>{s.val}</div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-widest">{s.label}</div>
          </div>
        ))}
      </div>

      {/* ACTIVE BOTS GRID */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-primary" /> Active Bot Assignments
        </h2>
        
        {loadingMeetings ? (
          <div className="flex justify-center p-8"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
        ) : meetings.length === 0 ? (
          <div className="text-center p-12 glass-panel rounded-xl text-slate-400">
            <Play className="w-10 h-10 mx-auto mb-4 opacity-40 text-blue-400" />
            <p>No active meetings in bots database. Add from inbox below.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {meetings.map(m => (
              <div key={m.id} className="glass-panel rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-bold text-lg text-white truncate pr-2">{m.title}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getStatusBadge(m.status)}`}>
                      {m.status}
                    </span>
                  </div>
                  
                  <div className="space-y-2 text-sm text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Platform:</span>
                      <span className="font-medium bg-slate-800/80 px-2 py-0.5 rounded">{getPlatformIcon(m.platform)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Organizer:</span>
                      <span className="truncate max-w-[200px]">{m.organizer || 'Unknown'}</span>
                    </div>
                    {(m.meeting_date || m.start_time) && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Scheduled:</span>
                        <span>{m.meeting_date} {m.start_time}</span>
                      </div>
                    )}
                    <div className="flex flex-col mt-2">
                      <span className="text-slate-500 text-xs mb-1">Meeting URL:</span>
                      <a href={m.meeting_url} target="_blank" className="text-blue-400 hover:underline truncate bg-slate-900/50 p-2 rounded-md font-mono text-xs border border-slate-800">
                        {m.meeting_url}
                      </a>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-5 pt-4 border-t border-slate-800/50">
                  <button onClick={() => triggerBot(m.id)} className="flex-1 flex justify-center items-center gap-2 bg-primary/20 hover:bg-primary/30 text-primary px-3 py-2 rounded-lg text-sm font-semibold transition-colors">
                    <Play className="w-4 h-4" /> Join Bot
                  </button>
                  <button onClick={() => setTranscriptModal(m.id)} className="flex-1 flex justify-center items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-3 py-2 rounded-lg text-sm font-semibold transition-colors">
                    <FileText className="w-4 h-4" /> Transcript
                  </button>
                  <button onClick={() => setEditModal(m)} className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors">
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button onClick={() => deleteMeeting(m.id)} className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* CLASSIFIED EMAILS SECTION */}
      <div className="pt-8 border-t border-slate-800">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <CalendarPlus className="w-5 h-5 text-emerald-400" /> Watcher Inbox (Suggested Meetings)
        </h2>
        
        {loadingEmails ? (
           <div className="flex text-slate-400 items-center justify-center p-8"><Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading suggested emails...</div>
        ) : (
          <div className="space-y-3">
            {emails.map((email, i) => (
              <EmailCard 
                 key={email.id || i} 
                 email={email} 
                 showMeetingTrigger={true} 
                 onMeetingStart={addToBotMeetings} 
              />
            ))}
            {emails.length === 0 && (
              <div className="text-center p-8 glass-panel rounded-xl text-slate-400">
                <CheckCircle2 className="w-8 h-8 mx-auto mb-3 opacity-40 text-emerald-400" />
                <p>No meeting communication detected in inbox.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* TRANSCRIPT MODAL */}
      {transcriptModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" /> Meeting Transcript
              </h3>
              <button onClick={() => setTranscriptModal(null)} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            
            <div className="p-5 flex-1 overflow-y-auto min-h-[300px]">
              {(() => {
                const trn = meetings.find(m => m.id === transcriptModal)?.transcript;
                if (!trn) return <div className="text-center text-slate-500 py-10 italic">No transcript recorded yet. Wait for bot to complete.</div>;
                
                return (
                  <div className="space-y-4">
                    {trn.split('\n\n').map((chunk, i) => {
                      if (!chunk.trim()) return null;
                      
                      const match = chunk.match(/^\[(.*?)\] (.*?): (.*)/s);
                      if (match) {
                         const [, time, speaker, text] = match;
                        const isBot = speaker.includes('Bot') || speaker.includes('AI');
                         const spkColor = isBot ? 'text-primary' : (speaker.includes('Speaker') ? 'text-slate-400' : 'text-emerald-400');
                         return (
                           <div key={i} className="flex gap-3 text-sm">
                             <div className="text-slate-600 font-mono text-xs pt-1 whitespace-nowrap">[{time}]</div>
                             <div className="flex-1 bg-slate-800/30 p-3 rounded-lg border border-slate-800/50">
                               <div className={`font-bold mb-1 ${spkColor}`}>{speaker}</div>
                               <div className="text-slate-300 leading-relaxed">{text}</div>
                             </div>
                           </div>
                         );
                      }
                      
                      const inlineMatch = chunk.match(/^([^:]+):\s*(.*)/is);
                      if (inlineMatch) {
                         const [, speaker, text] = inlineMatch;
                         const isBot = speaker.includes('Bot') || speaker.includes('AI');
                         const spkColor = isBot ? 'text-primary' : (speaker.includes('Speaker') ? 'text-slate-400' : 'text-purple-400');
                         return (
                           <div key={i} className="flex gap-3 text-sm">
                             <div className="text-slate-600 font-mono text-xs pt-1 w-12 text-center">-</div>
                             <div className="flex-1 bg-slate-800/30 p-3 rounded-lg border border-slate-800/50">
                               <div className={`font-bold mb-1 ${spkColor}`}>{speaker.trim()}</div>
                               <div className="text-slate-300 leading-relaxed">{text.trim()}</div>
                             </div>
                           </div>
                         );
                      }

                      return <div key={i} className="text-sm text-slate-400 p-2 bg-slate-800/20 rounded">{chunk}</div>;
                    })}
                  </div>
                );
              })()}
            </div>
            
            <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex justify-between items-center">
              <span className="text-xs text-slate-500">Run Identify Names to resolve 'Speaker 1' to real names using Groq AI.</span>
              <button 
                onClick={() => identifyNames(transcriptModal)}
                disabled={reformatting || !meetings.find(m => m.id === transcriptModal)?.transcript}
                className="flex items-center gap-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 px-4 py-2 rounded-lg font-semibold text-sm transition-colors disabled:opacity-50"
              >
                {reformatting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Users className="w-4 h-4" />} 
                {reformatting ? 'Analyzing...' : 'Identify Names'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EDIT MODAL */}
      {editModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl p-5">
            <h3 className="font-bold text-white mb-4">Edit Meeting</h3>
            <form onSubmit={saveEdit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Meeting Date (YYYY-MM-DD)</label>
                <input 
                  type="text" 
                  value={editModal.meeting_date || ''} 
                  onChange={(e) => setEditModal({...editModal, meeting_date: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white text-sm"
                  placeholder="2026-07-31"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Start Time (HH:MM)</label>
                <input 
                  type="text" 
                  value={editModal.start_time || ''} 
                  onChange={(e) => setEditModal({...editModal, start_time: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white text-sm"
                  placeholder="14:30"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Meeting URL</label>
                <input 
                  type="text" 
                  value={editModal.meeting_url || ''} 
                  onChange={(e) => setEditModal({...editModal, meeting_url: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Platform</label>
                <select 
                  value={editModal.platform || ''} 
                  onChange={(e) => setEditModal({...editModal, platform: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white text-sm"
                >
                  <option value="">Auto-detect</option>
                  <option value="google_meet">Google Meet</option>
                  <option value="zoom">Zoom</option>
                  <option value="teams">Microsoft Teams</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Status</label>
                <select 
                  value={editModal.status || ''} 
                  onChange={(e) => setEditModal({...editModal, status: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white text-sm"
                >
                  <option value="scheduled">Scheduled</option>
                  <option value="joining">Joining</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setEditModal(null)} className="px-4 py-2 hover:bg-slate-800 text-slate-300 rounded-lg text-sm bg-transparent">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
