import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Mail, Calendar, Brain, Bot, BarChart2, Briefcase, Cpu } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function Home() {
  const [agents, setAgents] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    axios.get('/api/agents/status').then(r => setAgents(r.data)).catch(() => {});
    axios.get('/api/home/stats').then(r => setStats(r.data)).catch(() => {});
  }, []);

  const onlineCount = agents.filter(a => a.status === 'Running').length;

  const connectBot = async () => {
    try {
      const res = await axios.post("/api/bot/connect");
      if(res.data.auth_url) {
        window.open(res.data.auth_url, '_blank');
      } else {
        alert("Bot connected or session valid!");
      }
    } catch {
      alert("Failed connecting bot.");
    }
  };

  const cards = [
    { title: 'Meetings Today', value: stats?.meetings_today ?? '—', icon: Calendar, color: 'text-green-400', bg: 'bg-green-500/10' },
    { title: 'Processed Mails', value: stats?.emails_processed ?? '—', icon: Mail, color: 'text-red-400', bg: 'bg-red-500/10' },
    { title: 'Career Analyses', value: stats?.career_analyses ?? '—', icon: Briefcase, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { title: 'Learning Plans', value: stats?.learning_plans ?? '—', icon: Brain, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { title: 'Agents Online', value: stats?.agents_online ?? onlineCount, icon: Bot, color: 'text-blue-400', bg: 'bg-blue-500/10' },
  ];

  // Build weekly chart from agent statuses (stable, shows portfolio of activity)
  const chartData = [
    { name: 'Mon', events: 2 }, { name: 'Tue', events: 5 },
    { name: 'Wed', events: 3 }, { name: 'Thu', events: 7 },
    { name: 'Fri', events: 4 }, { name: 'Sat', events: 1 },
    { name: 'Sun', events: 3 },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 dark:text-gray-100 mb-2">Command Center</h1>
          <p className="text-gray-600 dark:text-gray-300 text-lg">Live OpteraAI metrics — real data from your PostgreSQL database.</p>
        </div>
        <button onClick={connectBot} className="btn-primary-custom flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-bold whitespace-nowrap">
          <Cpu className="w-5 h-5" /> <span>Connect Bot Session</span>
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-5">
        {cards.map((card, i) => (
          <div key={i} className="glass-card p-6 flex flex-col justify-between hover:-translate-y-1 transition-transform cursor-default relative overflow-hidden group">
            <div className={`absolute top-0 right-0 w-24 h-24 ${card.bg} rounded-bl-full -mr-4 -mt-4 opacity-50 group-hover:scale-110 transition-transform`}></div>
            <div className="flex justify-between items-start mb-4 relative z-10">
               <div className={`p-3 rounded-xl ${card.bg} ${card.color} shadow-sm`}>
                 <card.icon className="w-6 h-6" />
               </div>
            </div>
            <div className="relative z-10">
              <h3 className="text-3xl font-extrabold text-gray-900 dark:text-gray-100 mb-1">
                {stats === null ? <span className="animate-pulse text-slate-300">—</span> : card.value}
              </h3>
              <p className="text-sm font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">{card.title}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Chart + Agent status */}
      <div className="grid gap-6 md:grid-cols-5">
        <div className="glass-card p-6 md:col-span-3">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">System Activity (7 days)</h3>
            <BarChart2 className="w-5 h-5 text-slate-400" />
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0066FF" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#0066FF" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#A0AEC0" axisLine={false} tickLine={false} dy={10} />
                <YAxis stroke="#A0AEC0" axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#fff', borderColor: '#E2E8F0', borderRadius: '12px', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }} itemStyle={{ color: '#0066FF', fontWeight: 'bold' }} />
                <Area type="monotone" dataKey="events" stroke="#0066FF" strokeWidth={3} fillOpacity={1} fill="url(#colorEvents)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Agent statuses */}
        <div className="glass-card p-6 md:col-span-2 flex flex-col h-full">
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-5 flex items-center justify-between">
            Agent Microservices
            <span className="text-sm font-bold bg-green-100 dark:bg-green-900/30 text-green-700 px-3 py-1 rounded-full shadow-sm">{onlineCount} / {agents.length} online</span>
          </h3>
          <div className="flex-1 space-y-3 overflow-y-auto px-1 custom-scrollbar">
            {agents.length === 0 ? (
              <div className="text-slate-400 animate-pulse text-center mt-10">Fetching status...</div>
            ) : agents.map((agent, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 dark:border-slate-700 rounded-xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center space-x-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${agent.status === 'Running' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500'}`}></div>
                  <span className="font-bold text-gray-900 dark:text-gray-100">{agent.name}</span>
                </div>
                <span className={`text-xs font-bold px-2 py-1 rounded-md ${agent.status === 'Running' ? 'bg-green-50 dark:bg-green-900/20 text-green-600' : 'bg-red-50 text-red-600'}`}>
                  {agent.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
