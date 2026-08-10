import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Calendar as CalendarIcon, Clock, AlertCircle, ChevronLeft, ChevronRight, CheckCircle2 } from 'lucide-react';

export default function Calendar() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const res = await axios.get('/api/calendar/events');
      setEvents(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const deleteEvent = async (id: string) => {
    if (!confirm('Are you sure you want to cancel this event?')) return;
    try {
      await axios.delete(`/api/calendar/events/${id}`);
      fetchEvents();
    } catch (err) {
      console.error(err);
      alert('Failed to cancel event');
    }
  };

  const today = new Date();
  
  const isToday = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.getDate() === today.getDate() && d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear();
  };

  const getUpcomingDeadlines = () => {
    return events.filter(e => e.event_type === 'TASK_DEADLINE' && new Date(e.start_datetime) >= today).slice(0, 5);
  };

  const getTodayEvents = () => {
    return events.filter(e => isToday(e.start_datetime)).sort((a, b) => new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime());
  };

  const getDaysInMonth = (year: number, month: number) => new Date(year, month + 1, 0).getDate();
  const getFirstDayOfMonth = (year: number, month: number) => new Date(year, month, 1).getDay();

  const renderCalendarGrid = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    const blanks = Array.from({ length: firstDay });
    const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);

    return (
      <div className="grid grid-cols-7 gap-2">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
          <div key={d} className="text-center text-xs font-semibold text-slate-400 py-2">{d}</div>
        ))}
        {blanks.map((_, i) => <div key={`blank-${i}`} className="p-2" />)}
        {days.map(day => {
          const date = new Date(year, month, day);
          const dayEvents = events.filter(e => {
            const ed = new Date(e.start_datetime);
            return ed.getDate() === day && ed.getMonth() === month && ed.getFullYear() === year;
          });
          
          const isCurrentToday = day === today.getDate() && month === today.getMonth() && year === today.getFullYear();

          return (
            <div key={day} className={`p-2 min-h-[80px] rounded-lg border ${isCurrentToday ? 'border-primary bg-primary/10' : 'border-slate-800 bg-slate-900/50'} relative group hover:border-slate-500 transition-colors`}>
              <span className={`text-sm ${isCurrentToday ? 'text-primary font-bold' : 'text-slate-300'}`}>{day}</span>
              <div className="mt-1 flex flex-col gap-1">
                {dayEvents.slice(0, 3).map((e, idx) => (
                  <div key={idx} className="text-[10px] truncate bg-blue-500/20 text-blue-300 px-1 py-0.5 rounded cursor-pointer hover:bg-blue-500/50 flex justify-between group" title={e.title}>
                    <span onClick={() => { if(e.google_event_link) window.open(e.google_event_link, '_blank'); }}>{e.title}</span>
                    <span onClick={(ev) => { ev.stopPropagation(); deleteEvent(e.id); }} className="text-red-400 opacity-0 group-hover:opacity-100 px-0.5 hover:bg-red-500/20 rounded">
                      ✕
                    </span>
                  </div>
                ))}
                {dayEvents.length > 3 && (
                  <div className="text-[10px] text-slate-400">+{dayEvents.length - 3} more</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="p-8 text-white max-w-7xl mx-auto space-y-8 h-full overflow-y-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-extrabold mb-2 bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent flex items-center gap-3">
            <CalendarIcon className="w-10 h-10 text-blue-400" />
            Calendar Agent
          </h1>
          <p className="text-slate-400">AgentOS Multi-Agent Schedule & Event Synchronization Engine</p>
        </div>
        <div className="flex gap-4">
           <div className="flex items-center gap-2 bg-green-500/10 text-green-400 px-4 py-2 rounded-full border border-green-500/20">
             <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
             Google Synced
           </div>
           <button className="px-6 py-2 bg-primary text-white rounded-lg font-bold shadow hover:bg-blue-600 transition">
             ⚡ Force Sync
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column */}
        <div className="lg:col-span-1 space-y-6">
           
           {/* Summary Cards */}
           <div className="grid grid-cols-2 gap-4">
             <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
               <Clock className="w-6 h-6 text-blue-400 mb-2" />
               <p className="text-3xl font-bold">{getTodayEvents().length}</p>
               <p className="text-xs text-slate-400">Today's Events</p>
             </div>
             <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
               <AlertCircle className="w-6 h-6 text-rose-400 mb-2" />
               <p className="text-3xl font-bold">{getUpcomingDeadlines().length}</p>
               <p className="text-xs text-slate-400">Upcoming Deadlines</p>
             </div>
           </div>

           {/* Today's Events */}
           <div className="glass-panel p-6 rounded-xl">
              <h3 className="text-lg font-bold flex items-center gap-2 mb-4 border-b border-slate-800 pb-2">
                <Clock className="w-5 h-5 text-blue-400" /> Today's Schedule
              </h3>
              {loading ? (
                <div className="animate-pulse flex flex-col gap-2">
                  <div className="h-10 bg-slate-800 rounded"></div>
                  <div className="h-10 bg-slate-800 rounded"></div>
                </div>
              ) : getTodayEvents().length > 0 ? (
                <div className="space-y-3">
                  {getTodayEvents().map(e => (
                    <div key={e.id} className="flex gap-3 bg-slate-900/50 p-3 rounded-lg border-l-2 border-blue-500 justify-between items-center hover:bg-slate-800 transition group">
                       <div className="flex gap-3">
                         <div className="text-sm text-slate-400 whitespace-nowrap pt-1">
                           {new Date(e.start_datetime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                         </div>
                         <div>
                           <p className="font-semibold text-sm">{e.title}</p>
                           <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-blue-300">{e.event_type}</span>
                         </div>
                       </div>
                       <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition">
                          {e.google_event_link && (
                            <a href={e.google_event_link} target="_blank" rel="noreferrer" className="p-1.5 bg-blue-500/20 text-blue-400 hover:bg-blue-500/40 rounded">
                              View
                            </a>
                          )}
                          <button onClick={() => deleteEvent(e.id)} className="p-1.5 bg-red-500/20 text-red-400 hover:bg-red-500/40 rounded">
                            Cancel
                          </button>
                       </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 italic">No events scheduled for today.</p>
              )}
           </div>

           {/* Upcoming Deadlines */}
           <div className="glass-panel p-6 rounded-xl border border-rose-500/20 shadow-[0_0_15px_rgba(244,63,94,0.05)]">
              <h3 className="text-lg font-bold flex items-center gap-2 mb-4 border-b border-slate-800 pb-2">
                <AlertCircle className="w-5 h-5 text-rose-400" /> Upcoming Deadlines
              </h3>
              {getUpcomingDeadlines().length > 0 ? (
                <div className="space-y-3">
                  {getUpcomingDeadlines().map(e => (
                    <div key={e.id} className="bg-rose-500/10 p-3 rounded-lg border-l-2 border-rose-500 flex justify-between items-center group hover:bg-rose-500/20 transition">
                       <div>
                         <p className="font-semibold text-sm text-rose-100">{e.title}</p>
                         <p className="text-xs text-rose-300/70 mt-1">
                           Due: {new Date(e.start_datetime).toLocaleDateString()}
                         </p>
                       </div>
                       <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition">
                          {e.google_event_link && (
                            <a href={e.google_event_link} target="_blank" rel="noreferrer" className="p-1.5 bg-rose-500/20 text-rose-300 hover:bg-rose-500/40 rounded text-xs">
                              View
                            </a>
                          )}
                          <button onClick={() => deleteEvent(e.id)} className="p-1.5 bg-red-500/20 text-red-400 hover:bg-red-500/40 rounded text-xs">
                            Cancel
                          </button>
                       </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 italic">No upcoming deadlines.</p>
              )}
           </div>

        </div>

        {/* Right Column: Full Calendar */}
        <div className="lg:col-span-2">
           <div className="glass-panel p-6 rounded-xl h-full flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <CalendarIcon className="text-purple-400" /> Event Grid
                </h3>
                <div className="flex items-center gap-4 bg-slate-900 rounded-lg p-1">
                  <button 
                    onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1))}
                    className="p-1 hover:bg-slate-700 rounded"
                  >
                    <ChevronLeft />
                  </button>
                  <span className="font-bold min-w-[120px] text-center">
                    {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
                  </span>
                  <button 
                    onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))}
                    className="p-1 hover:bg-slate-700 rounded"
                  >
                    <ChevronRight />
                  </button>
                </div>
              </div>

              <div className="flex-1 bg-slate-950/50 rounded-xl p-4 border border-slate-800">
                 {renderCalendarGrid()}
              </div>
           </div>
        </div>

      </div>
    </div>
  );
}
