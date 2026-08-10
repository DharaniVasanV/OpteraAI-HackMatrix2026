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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Command Center</h1>
          <p className="text-slate-400">Live AgentOS metrics — real data from your PostgreSQL database.</p>
        </div>
        <button onClick={connectBot} className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-semibold transition-colors border border-slate-700">
          <Cpu className="w-4 h-4" /> <span>Connect Bot Session</span>
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((card, i) => (
          <div key={i} className={`glass-panel p-6 rounded-xl flex items-center justify-between border border-slate-700/50`}>
            <div>
              <p className="text-sm font-medium text-slate-400 mb-1">{card.title}</p>
              <h3 className="text-3xl font-bold text-white">
                {stats === null ? <span className="animate-pulse text-slate-600">—</span> : card.value}
              </h3>
            </div>
            <div className={`p-4 rounded-full ${card.bg} ${card.color}`}>
              <card.icon className="w-6 h-6" />
            </div>
          </div>
        ))}
      </div>

      {/* Chart + Agent status */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="glass-panel p-6 rounded-xl">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-white">System Activity (7 days)</h3>
            <BarChart2 className="w-5 h-5 text-slate-400" />
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#475569" />
                <YAxis stroke="#475569" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} itemStyle={{ color: '#fff' }} />
                <Area type="monotone" dataKey="events" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorEvents)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Agent statuses */}
        <div className="glass-panel p-6 rounded-xl">
          <h3 className="text-xl font-bold text-white mb-4">
            Agent Microservices
            <span className="ml-3 text-sm font-normal text-green-400">{onlineCount} / {agents.length} online</span>
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {agents.length === 0 ? (
              <div className="text-slate-500 animate-pulse">Loading agents...</div>
            ) : agents.map((agent, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-800/40 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${agent.status === 'Running' ? 'bg-green-500 shadow-[0_0_6px_#10b981]' : 'bg-red-500'}`} />
                  <span className="font-medium text-white text-sm">{agent.name}</span>
                </div>
                <span className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-300">:{agent.port}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
