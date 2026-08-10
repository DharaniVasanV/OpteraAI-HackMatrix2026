import React from 'react';

export default function Settings() {
  return (
    <div className="p-8 text-white max-w-3xl">
      <h1 className="text-3xl font-bold mb-6">Settings</h1>
      
      <div className="space-y-8">
        <div className="glass-panel p-6 rounded-xl space-y-4">
          <h3 className="text-lg font-bold">Google Account Sync</h3>
          <p className="text-sm text-slate-400">Sync AgentOS with your calendar and email inbox.</p>
          <a href="/gmail/oauth" className="inline-block px-6 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition font-medium">Link Google Account</a>
        </div>
        
        <div className="glass-panel p-6 rounded-xl space-y-4">
          <h3 className="text-lg font-bold">Agent Ports & Webhooks</h3>
          <p className="text-sm text-slate-400">View configuration for the 14 internal microservices.</p>
          <div className="bg-slate-900 p-4 rounded-lg font-mono text-xs text-primary">
            WATCHER_PORT=8001<br/>
            CAREER_PORT=8008<br/>
            KNOWLEDGE_PORT=8005<br/>
            ...
          </div>
        </div>
      </div>
    </div>
  );
}
