import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart2, TrendingUp, Mail, Users, CheckSquare, Briefcase, Zap } from 'lucide-react';

const FILTERS = ['today', 'week', 'month'];

const ScoreRing = ({ score }: { score: number }) => {
  const pct = Math.min(100, Math.max(0, score));
  const r = 52;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;
  const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#f43f5e';
  return (
    <div className="relative flex items-center justify-center w-36 h-36">
      <svg width="144" height="144" viewBox="0 0 144 144">
        <circle cx="72" cy="72" r={r} fill="none" stroke="#1e293b" strokeWidth="12" />
        <circle cx="72" cy="72" r={r} fill="none" stroke={color} strokeWidth="12"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          transform="rotate(-90 72 72)" style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div className="absolute text-center">
        <p className="text-3xl font-extrabold" style={{ color }}>{pct.toFixed(0)}</p>
        <p className="text-xs text-slate-400">/ 100</p>
      </div>
    </div>
  );
};

const MetricCard = ({ icon: Icon, label, value, color }: any) => (
  <div className="glass-panel p-5 rounded-xl flex items-center gap-4">
    <div className={`p-3 rounded-lg ${color}`}>
      <Icon className="w-6 h-6 text-white" />
    </div>
    <div>
      <p className="text-2xl font-bold">{value ?? 0}</p>
      <p className="text-xs text-slate-400">{label}</p>
    </div>
  </div>
);

const DistBar = ({ label, value, max, color }: any) => {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-slate-300">{label}</span>
        <span className="font-bold">{value}</span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
};

export default function Analytics() {
  const [period, setPeriod] = useState('week');
  const [data, setData] = useState<any>(null);
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async (p: string) => {
    setLoading(true);
    try {
      const [dashRes, insRes] = await Promise.allSettled([
        axios.get(`/api/analytics/dashboard?filter_period=${p}`),
        axios.get(`/api/analytics/insights?filter_period=${p}`)
      ]);
      if (dashRes.status === 'fulfilled') setData(dashRes.value.data);
      if (insRes.status === 'fulfilled') setInsights(insRes.value.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(period); }, [period]);

  return (
    <div className="p-8 text-white max-w-7xl mx-auto h-full overflow-y-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-4xl font-extrabold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent flex items-center gap-3">
            <BarChart2 className="w-10 h-10 text-violet-400" /> Ecosystem Analytics
          </h1>
          <p className="text-slate-400 mt-1">Real-time productivity metrics from the Analytics Agent (Port 8013).</p>
        </div>
        <div className="flex gap-2 bg-slate-900 p-1 rounded-xl">
          {FILTERS.map(f => (
            <button key={f} onClick={() => setPeriod(f)}
              className={`px-5 py-2 rounded-lg text-sm font-semibold capitalize transition-all ${period === f ? 'bg-violet-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="animate-pulse grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => <div key={i} className="h-24 bg-slate-800 rounded-xl" />)}
        </div>
      ) : !data ? (
        <div className="glass-panel p-12 text-center text-slate-500 rounded-xl border border-dashed border-slate-700">
          <BarChart2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Analytics Agent is offline or no data yet. Start AgentOS and process some emails!</p>
        </div>
      ) : (
        <>
          {/* Top row: Score + Summary cards */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="glass-panel p-6 rounded-xl flex flex-col items-center justify-center gap-3 border border-violet-500/20 shadow-[0_0_20px_rgba(139,92,246,0.1)]">
              <p className="text-sm text-violet-300 font-semibold uppercase tracking-wider">Productivity Score</p>
              <ScoreRing score={data.productivity_score} />
              <p className="text-xs text-slate-400">{data.filter_period} · {data.start_date} → {data.end_date}</p>
            </div>
            <div className="lg:col-span-3 grid grid-cols-2 sm:grid-cols-3 gap-4">
              <MetricCard icon={Mail} label="Emails Processed" value={data.email?.total_processed} color="bg-blue-600" />
              <MetricCard icon={TrendingUp} label="Opportunities" value={data.email?.opportunities_detected} color="bg-emerald-600" />
              <MetricCard icon={Users} label="Meetings" value={data.meeting?.total_meetings} color="bg-indigo-600" />
              <MetricCard icon={CheckSquare} label="Tasks Completed" value={data.task?.completed} color="bg-green-600" />
              <MetricCard icon={Briefcase} label="Career Analyses" value={data.career?.career_activity_count} color="bg-rose-600" />
              <MetricCard icon={Zap} label="Applications" value={data.career?.applications_submitted} color="bg-violet-600" />
            </div>
          </div>

          {/* Middle row: Task breakdown + Meeting breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Task Distribution */}
            <div className="glass-panel p-6 rounded-xl">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-green-300">
                <CheckSquare className="w-5 h-5" /> Task Breakdown
              </h3>
              <div className="space-y-4">
                <DistBar label="Completed" value={data.task?.completed} max={data.task?.total} color="#10b981" />
                <DistBar label="Pending" value={data.task?.pending} max={data.task?.total} color="#f59e0b" />
                <DistBar label="Overdue" value={data.task?.overdue} max={data.task?.total} color="#f43f5e" />
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-3 text-center">
                <div><p className="text-lg font-bold text-green-400">{data.task?.completion_rate?.toFixed(0)}%</p><p className="text-xs text-slate-400">Completion Rate</p></div>
                <div><p className="text-lg font-bold">{data.task?.total}</p><p className="text-xs text-slate-400">Total Tasks</p></div>
                <div><p className="text-lg font-bold text-rose-400">{data.task?.overdue}</p><p className="text-xs text-slate-400">Overdue</p></div>
              </div>
            </div>

            {/* Meeting breakdown */}
            <div className="glass-panel p-6 rounded-xl">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-indigo-300">
                <Users className="w-5 h-5" /> Meeting Activity
              </h3>
              <div className="space-y-4">
                <DistBar label="User Attended" value={data.meeting?.user_attended} max={data.meeting?.total_meetings} color="#6366f1" />
                <DistBar label="AI Bot Attended" value={data.meeting?.ai_attended} max={data.meeting?.total_meetings} color="#a855f7" />
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-3 text-center">
                <div><p className="text-lg font-bold text-indigo-400">{data.meeting?.total_meetings}</p><p className="text-xs text-slate-400">Total Meetings</p></div>
                <div><p className="text-lg font-bold">{data.meeting?.total_duration_minutes}</p><p className="text-xs text-slate-400">Total Minutes</p></div>
                <div><p className="text-lg font-bold text-purple-400">{data.meeting?.tasks_extracted}</p><p className="text-xs text-slate-400">Tasks Extracted</p></div>
              </div>
            </div>
          </div>

          {/* AI Insights */}
          {insights && (
            <div className="glass-panel p-6 rounded-xl border border-fuchsia-500/20 shadow-[0_0_20px_rgba(217,70,239,0.07)]">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-fuchsia-300">
                <Zap className="w-5 h-5" /> AI-Powered Productivity Insights
              </h3>
              <p className="text-slate-300 mb-4">{insights.summary}</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-green-500/10 border border-green-500/20 p-4 rounded-lg">
                  <p className="text-sm font-bold text-green-400 mb-2">Positive Trends</p>
                  <ul className="space-y-1">{insights.positive_trends?.map((t: string, i: number) => <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-green-500">✓</span>{t}</li>)}</ul>
                </div>
                <div className="bg-amber-500/10 border border-amber-500/20 p-4 rounded-lg">
                  <p className="text-sm font-bold text-amber-400 mb-2">Recommendations</p>
                  <ul className="space-y-1">{insights.recommendations?.map((r: string, i: number) => <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-amber-500">→</span>{r}</li>)}</ul>
                </div>
                <div className="bg-rose-500/10 border border-rose-500/20 p-4 rounded-lg">
                  <p className="text-sm font-bold text-rose-400 mb-2">Warnings</p>
                  <ul className="space-y-1">{insights.warnings?.map((w: string, i: number) => <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-rose-500">!</span>{w}</li>)}</ul>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
