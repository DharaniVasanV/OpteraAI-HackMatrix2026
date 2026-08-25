import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Outlet, Navigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Home, Inbox, Briefcase, Calendar, Video, FileText, 
  Map, MonitorPlay, FileCheck, CopyPlus, Bell, 
  Activity, Component, Settings, LogOut, Moon, Sun, Menu, X, ArrowUpRight, User as UserIcon,
  Bot, Maximize2, Send, Loader2, Sparkles, FileSearch
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  { name: 'Inbox', path: '/inbox', icon: Inbox },
  { name: 'Opportunities', path: '/opportunities', icon: Briefcase },
  { name: 'Meetings', path: '/meetings', icon: Video },
  { name: 'Career', path: '/career', icon: Map },
  { name: 'Learning', path: '/learning', icon: MonitorPlay },
];

export default function Layout() {
  const { user, isLoading, logout } = useAuth();
  const location = useLocation();
  const [isDark, setIsDark] = useState(false);
  const [menuOpen, setMenuOpen] = useState(window.innerWidth >= 1024);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifMenu, setShowNotifMenu] = useState(false);
  const [alerts, setAlerts] = useState<any[]>([]);

  // Chatbot State
  const [showChatbot, setShowChatbot] = useState(false);
  const [syncingChatbot, setSyncingChatbot] = useState(false);
  const [chatHistory, setChatHistory] = useState<any[]>([]);
  const [botQuery, setBotQuery] = useState('');
  const [botLoading, setBotLoading] = useState(false);

  // Inline markdown renderer: bold, bullet, numbered lists
  const renderAnswer = (text: string) => {
    const lines = text.split('\n');
    return (
      <div className="flex flex-col gap-1">
        {lines.map((line, i) => {
          const trimmed = line.trim();
          if (!trimmed) return null;

          // Bullet points: -, *, •
          const bulletMatch = trimmed.match(/^[-*•]\s+(.+)/);
          if (bulletMatch) {
            return (
              <div key={i} className="flex items-start gap-1.5">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-[#0066FF] flex-shrink-0" />
                <span dangerouslySetInnerHTML={{ __html: applyInline(bulletMatch[1]) }} />
              </div>
            );
          }

          // Numbered lists: 1. 2. etc
          const numMatch = trimmed.match(/^(\d+)\.\s+(.+)/);
          if (numMatch) {
            return (
              <div key={i} className="flex items-start gap-2">
                <span className="font-bold text-[#0066FF] flex-shrink-0 text-xs mt-0.5">{numMatch[1]}.</span>
                <span dangerouslySetInnerHTML={{ __html: applyInline(numMatch[2]) }} />
              </div>
            );
          }

          // Regular line
          return <p key={i} dangerouslySetInnerHTML={{ __html: applyInline(trimmed) }} />;
        })}
      </div>
    );
  };

  const applyInline = (text: string) =>
    text
      .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-gray-900 dark:text-gray-100">$1</strong>')
      .replace(/`(.+?)`/g, '<code class="bg-slate-100 dark:bg-slate-700 px-1 rounded text-xs font-mono">$1</code>');

  const handleOpenChatbot = async () => {
    setShowChatbot(true);
    setSyncingChatbot(true);
    try {
      await axios.post('/api/knowledge/sync');
    } catch (err) {
      console.error('Chatbot sync error', err);
    }
    setSyncingChatbot(false);
  };

  const handleBotAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!botQuery) return;
    setBotLoading(true);
    const currentQuery = botQuery;
    setBotQuery('');
    setChatHistory(prev => [...prev, { query: currentQuery, answer: null }]);
    try {
      const res = await axios.get(`/api/knowledge/ask?query=${encodeURIComponent(currentQuery)}`);
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist[newHist.length - 1].answer = res.data;
        return newHist;
      });
    } catch (err) {
      console.error(err);
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist[newHist.length - 1].answer = { answer: "Error connecting to the Knowledge Agent." };
        return newHist;
      });
    }
    setBotLoading(false);
  };

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  useEffect(() => {
    if (user) {
      axios.get('/api/notifications').then(res => {
        if (Array.isArray(res.data)) {
          setAlerts(res.data.filter(n => !n.read));
        }
      }).catch(err => console.log('Notif err', err));
    }
  }, [user]);

  if (isLoading) return <div className="h-screen w-screen flex items-center justify-center bg-background text-foreground">Loading...</div>;
  if (!user) return <Navigate to="/login" />;

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background font-sans text-gray-600 dark:text-gray-300">
      
      {/* Mobile Sidebar Overlay */}
      {menuOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/50 z-30 lg:hidden backdrop-blur-sm"
          onClick={() => setMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed lg:static top-0 left-0 w-64 border-r border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 dark:bg-[#0F172A] flex flex-col h-full shrink-0 shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-40 transition-all duration-300",
        menuOpen ? "translate-x-0 ml-0" : "-translate-x-full lg:translate-x-0 lg:-ml-64"
      )}>
        <div className="h-16 flex items-center justify-between px-6 border-b border-slate-200 dark:border-slate-700 dark:border-white/10">
          <div className="flex items-center">
            <img src="/logo.png" alt="OpteraAI Logo" className="w-10 h-10 mr-2 object-contain" />
            <span className="text-xl font-extrabold tracking-tight text-gray-900 dark:text-gray-100 dark:text-white">Optera<span className="text-[#0066FF]">AI</span></span>
          </div>
          <button className="text-slate-500 hover:text-[#0066FF] transition-colors" onClick={() => setMenuOpen(false)}>
            <X className="w-5 h-5"/>
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 custom-scrollbar">
          <ul className="space-y-1 px-3">
            {navItems.map((item) => {
              const active = location.pathname === item.path || 
                             (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <li key={item.name}>
                  <Link
                    to={item.path}
                    onClick={() => setMenuOpen(false)}
                    className={cn(
                      "flex items-center px-3 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200",
                      active ? "bg-[#0066FF]/10 text-[#0066FF] shadow-sm" : "text-gray-600 dark:text-gray-300 dark:text-[#94A3B8] hover:text-gray-900 dark:text-gray-100 dark:hover:text-white hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 dark:hover:bg-slate-800"
                    )}
                  >
                    <item.icon className={cn("w-5 h-5 mr-3 transition-colors", active ? "text-[#0066FF]" : "text-slate-400 dark:text-slate-400")} />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      {/* Main content wrapper */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top Navbar */}
        <header className="h-16 flex-shrink-0 flex items-center justify-between px-4 sm:px-8 border-b border-slate-200 dark:border-slate-700/60 dark:border-white/10 glass-panel z-40 w-full relative">
          <div className="flex items-center w-full max-w-md gap-3">
             {!menuOpen && (
               <div className="flex flex-shrink-0 items-center mr-1 animate-in fade-in zoom-in duration-300">
                 <button className="p-2 -ml-2 sm:-ml-4 text-slate-500 hover:text-[#0066FF] transition-colors z-[60] relative focus:outline-none" onClick={() => setMenuOpen(true)}>
                   <Menu className="w-6 h-6" />
                 </button>
                 <div className="flex items-center ml-1 sm:ml-3">
                   <img src="/logo.png" alt="OpteraAI Logo" className="w-8 h-8 mr-1.5 sm:mr-2 object-contain" />
                   <span className="text-lg sm:text-xl font-extrabold tracking-tight text-gray-900 dark:text-gray-100 hidden sm:block">Optera<span className="text-[#0066FF]">AI</span></span>
                 </div>
               </div>
             )}
             <div className="relative w-full group flex-1">
               <input 
                 type="text" 
                 placeholder="Search or jump to... (Ctrl+K)" 
                 className="w-full bg-white dark:bg-slate-800 dark:bg-slate-800 dark:text-white border border-slate-200 dark:border-slate-700 dark:border-white/10 shadow-sm rounded-full px-5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0066FF]/30 focus:border-[#0066FF] text-gray-900 dark:text-gray-100 transition-all group-hover:shadow-md"
               />
               <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono text-slate-400 dark:text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 dark:border-white/10 hidden sm:block">Ctrl K</div>
             </div>
          </div>
          <div className="flex items-center space-x-5 h-full">
             <button onClick={() => setIsDark(!isDark)} className="text-slate-400 dark:text-slate-400 hover:text-[#0066FF] transition-colors focus:outline-none flex items-center justify-center">
               {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
             </button>
             {/* Notifications Dropdown */}
             <div className="relative flex items-center justify-center h-full">
               <button onClick={() => setShowNotifMenu(!showNotifMenu)} className="text-slate-400 dark:text-slate-400 hover:text-[#0066FF] relative transition-colors focus:outline-none flex items-center justify-center">
                 <Bell className="w-5 h-5" />
                 {alerts.length > 0 && (
                   <span className="absolute -top-1 -right-0.5 w-2.5 h-2.5 bg-[#FF3A21] rounded-full border-2 border-white dark:border-slate-800 shadow-sm"></span>
                 )}
               </button>
               {showNotifMenu && (
                 <div className="absolute top-full right-0 mt-3 w-72 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/50 rounded-xl shadow-xl z-50 overflow-hidden">
                   <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700/50 flex justify-between items-center bg-slate-50 dark:bg-slate-900/50">
                     <span className="font-bold text-sm text-gray-900 dark:text-gray-100">Recent Alerts</span>
                     <Link to="/notifications" onClick={() => setShowNotifMenu(false)} className="text-slate-400 hover:text-blue-500 transition-colors">
                       <ArrowUpRight className="w-4 h-4" />
                     </Link>
                   </div>
                   <div className="p-0 max-h-64 overflow-y-auto custom-scrollbar">
                     {alerts.length > 0 ? (
                       alerts.map((alert, idx) => (
                         <div key={idx} className="px-4 py-3 border-b last:border-0 border-slate-100 dark:border-slate-700/30 hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-colors">
                           <p className="text-sm text-slate-800 dark:text-slate-200">{alert.message || alert.title}</p>
                           <span className="text-xs text-slate-400 mt-1 block">{alert.timestamp || 'Just now'}</span>
                         </div>
                       ))
                     ) : (
                       <p className="text-xs text-slate-500 text-center py-6">No new alerts.</p>
                     )}
                   </div>
                 </div>
               )}
             </div>

             <div className="flex items-center space-x-3 sm:pl-5 border-l border-transparent sm:border-slate-200 dark:sm:border-slate-700 dark:sm:border-white/10 relative">
                <div className="text-right hidden sm:block">
                   <p className="text-sm font-bold text-gray-900 dark:text-gray-100 dark:text-white leading-tight">{user.name}</p>
                   <p className="text-xs text-[#718096] dark:text-slate-400 font-medium leading-tight">Admin</p>
                </div>
                
                {/* Profile Dropdown */}
                <div className="relative">
                  <div onClick={() => setShowProfileMenu(!showProfileMenu)} className="w-9 h-9 rounded-full bg-gradient-to-tr from-[#0066FF] to-[#4299e1] flex items-center justify-center text-white font-bold shadow-md ring-2 ring-white cursor-pointer hover:scale-105 transition-transform">
                     {user.name.charAt(0)}
                  </div>
                  {showProfileMenu && (
                    <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/50 rounded-xl shadow-xl z-50 py-2">
                       <Link to="/settings" onClick={() => setShowProfileMenu(false)} className="flex items-center px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-sm font-semibold text-gray-700 dark:text-gray-300 transition-colors"><UserIcon className="w-4 h-4 mr-3 text-slate-400" /> My Profile</Link>
                       <Link to="/applications" onClick={() => setShowProfileMenu(false)} className="flex items-center px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-sm font-semibold text-gray-700 dark:text-gray-300 transition-colors"><CopyPlus className="w-4 h-4 mr-3 text-slate-400" /> My Applications</Link>
                       <Link to="/calendar" onClick={() => setShowProfileMenu(false)} className="flex items-center px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-sm font-semibold text-gray-700 dark:text-gray-300 transition-colors"><Calendar className="w-4 h-4 mr-3 text-slate-400" /> My Calendar</Link>
                       <Link to="/agents" onClick={() => setShowProfileMenu(false)} className="flex items-center px-4 py-2 border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-sm font-semibold text-gray-700 dark:text-gray-300 transition-colors"><Component className="w-4 h-4 mr-3 text-slate-400" /> AI Agents</Link>
                       
                       <button onClick={() => { setShowProfileMenu(false); logout(); }} className="w-full text-left flex items-center px-4 py-2 hover:bg-rose-50 dark:hover:bg-rose-900/20 text-sm font-bold text-rose-600 dark:text-rose-400 transition-colors mt-1"><LogOut className="w-4 h-4 mr-3" /> Log Out</button>
                    </div>
                  )}
                </div>
             </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto p-4 sm:p-8 scroll-smooth z-0">
          <div className="max-w-7xl mx-auto">
             <Outlet />
          </div>
        </main>
      </div>

      {/* Floating Chatbot Widget */}
      {!showChatbot && (
        <button 
          onClick={handleOpenChatbot}
          className="fixed bottom-6 right-6 w-14 h-14 bg-white dark:bg-slate-800 border-2 border-[#0066FF] text-[#0066FF] rounded-full shadow-2xl flex items-center justify-center hover:bg-[#0066FF] hover:text-white transition-all z-[9900] duration-300 animate-in fade-in zoom-in group"
        >
          <Bot className="w-7 h-7 group-hover:scale-110 transition-transform duration-300" />
          <span className="absolute -top-1 -right-0.5 w-3.5 h-3.5 bg-[#0066FF] rounded-full border-2 border-white dark:border-slate-900 shadow-sm animate-pulse"></span>
        </button>
      )}

      {showChatbot && (
        <div className="fixed bottom-4 right-4 w-[360px] max-w-[calc(100vw-2rem)] bg-white dark:bg-[#0b1021] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl z-[9900] flex flex-col animate-in slide-in-from-bottom-8 zoom-in-95 duration-200" style={{maxHeight: 'calc(100vh - 2rem)'}}>
          <div className="bg-gradient-to-r from-[#004bbd] to-[#0066FF] text-white px-4 py-3 flex items-center justify-between shadow-sm rounded-t-2xl flex-shrink-0">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 drop-shadow-sm shadow-white/30" />
              <span className="font-bold text-sm tracking-wide">OpteraAI Knowledge</span>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/knowledge" onClick={() => setShowChatbot(false)} className="hover:text-white/70 transition-colors" title="Expand to Dashboard">
                <Maximize2 className="w-4 h-4" />
              </Link>
              <button onClick={() => setShowChatbot(false)} className="hover:text-white/70 transition-colors" title="Close">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          
          <div className="flex-1 p-4 overflow-y-auto bg-slate-50 dark:bg-slate-900/50 flex flex-col space-y-4 custom-scrollbar" style={{minHeight: '200px', maxHeight: '420px'}}>
             {syncingChatbot ? (
               <div className="flex-1 flex flex-col items-center justify-center">
                 <Loader2 className="w-8 h-8 animate-spin text-[#0066FF] mb-3" />
                 <span className="text-xs text-slate-500 font-medium">Syncing Knowledge Base...</span>
               </div>
             ) : (
               <>
                 <div className="flex gap-2 w-11/12">
                   <div className="w-8 h-8 rounded-full bg-[#0066FF]/10 flex items-center justify-center flex-shrink-0 mt-1">
                     <Bot className="w-4 h-4 text-[#0066FF]" />
                   </div>
                   <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-3 rounded-2xl rounded-tl-sm text-sm text-gray-800 dark:text-gray-200 shadow-sm leading-relaxed">
                     Sync complete! How can I assist you with your knowledge data?
                   </div>
                 </div>
                 
                 {chatHistory.map((chat, idx) => (
                   <React.Fragment key={idx}>
                     <div className="flex gap-2 flex-row-reverse items-start w-full">
                        <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <UserIcon className="w-3.5 h-3.5 text-slate-600 dark:text-slate-300" />
                        </div>
                        <div className="bg-[#0066FF] text-white px-3 py-2 rounded-2xl rounded-tr-sm text-sm shadow-sm leading-relaxed max-w-[80%] break-words">
                         {chat.query}
                       </div>
                     </div>
                     {chat.answer && (
                       <div className="flex gap-2 items-start animate-in slide-in-from-bottom-2 fade-in max-w-full">
                          <div className="w-7 h-7 rounded-full bg-[#0066FF]/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <Bot className="w-3.5 h-3.5 text-[#0066FF]" />
                          </div>
                          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-2.5 rounded-2xl rounded-tl-sm text-sm text-gray-700 dark:text-gray-200 shadow-sm flex flex-col gap-1.5 flex-1 min-w-0">
                            <div className="leading-relaxed text-[13px] break-words">
                              {renderAnswer(chat.answer.answer || "")}
                            </div>
                           {chat.answer.retrieved_documents && chat.answer.retrieved_documents.length > 0 && (
                              <div className="mt-1 pt-2 border-t border-slate-100 dark:border-slate-700">
                                <span className="text-[10px] font-bold text-slate-400 uppercase flex items-center mb-1.5">
                                  <FileSearch className="w-3 h-3 mr-1"/>Sources
                                </span>
                                {chat.answer.retrieved_documents.slice(0,2).map((s:any, i:number) => (
                                  <div key={i} className="text-[11px] text-slate-500 flex items-center justify-between gap-1 mb-0.5 min-w-0">
                                    <span className="truncate flex-1">{s.document_name || s.title}</span>
                                    <span className="text-[#0066FF] font-semibold flex-shrink-0">
                                      {((s.similarity_score ?? s.relevance ?? 0)*100).toFixed(0)}%
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                       </div>
                     )}
                   </React.Fragment>
                 ))}

                 {botLoading && (
                   <div className="flex gap-2 items-center text-xs text-slate-400 font-medium ml-10">
                     <Sparkles className="w-3 h-3 animate-spin mr-1" /> Thinking...
                   </div>
                 )}
               </>
             )}
          </div>

          <div className="p-3 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700/50">
            <form onSubmit={handleBotAsk} className="relative flex items-center">
              <input 
                type="text" 
                value={botQuery}
                onChange={(e) => setBotQuery(e.target.value)}
                placeholder="Ask your assistant..." 
                className="w-full bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-full pl-4 pr-10 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-[#A0AEC0] focus:ring-2 focus:ring-[#0066FF]/50 outline-none transition-all shadow-inner"
              />
              <button 
                type="submit" 
                disabled={botLoading || syncingChatbot || !botQuery}
                className="absolute right-1.5 p-2 text-[#0066FF] hover:bg-[#0066FF]/10 rounded-full transition-colors disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
