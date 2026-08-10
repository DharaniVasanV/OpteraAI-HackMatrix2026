import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Server, Activity, RefreshCw, Terminal } from 'lucide-react';

export default function Agents() {
  const [agents, setAgents] = useState<any[]>([]);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = () => {
    axios.get('/api/agents/status').then(res => setAgents(res.data)).catch(console.error);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">AI Agents Service Mesh</h1>
          <p className="text-slate-400">Manage and monitor all 14 autonomous microservices.</p>
        </div>
        <button onClick={fetchAgents} className="px-4 py-2 bg-slate-800 text-white rounded-lg flex items-center space-x-2 hover:bg-slate-700">
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent, i) => (
          <div key={i} className="glass-panel p-6 rounded-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${agent.status === 'Running' ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-red-500 shadow-[0_0_10px_#ef4444]'}`}></div>
                  <h3 className="text-lg font-bold text-white">{agent.name}</h3>
                </div>
                <Server className="w-5 h-5 text-slate-500" />
              </div>
              <p className="text-sm text-slate-400 mb-6">Hosted locally on Port {agent.port}. Communicating via inter-agent REST bus.</p>
            </div>
            
            <div className="flex items-center space-x-3 mt-auto pt-4 border-t border-slate-800">
              <button className="flex-1 px-3 py-2 bg-primary/10 text-primary hover:bg-primary/20 rounded-md text-sm font-medium flex items-center justify-center transition-colors">
                <Terminal className="w-4 h-4 mr-2" />
                Logs
              </button>
              <button className="flex-1 px-3 py-2 bg-slate-800 text-white hover:bg-slate-700 rounded-md text-sm font-medium flex items-center justify-center transition-colors">
                <Activity className="w-4 h-4 mr-2" />
                Metrics
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
