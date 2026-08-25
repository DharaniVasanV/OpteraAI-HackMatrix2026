import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FormInput, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

export default function Applications() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await axios.get('/api/filler/history');
      setHistory(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 text-gray-900 dark:text-gray-100 max-w-7xl mx-auto space-y-8 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-extrabold mb-2 bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent flex items-center gap-3">
            <FormInput className="w-10 h-10 text-emerald-400" />
            Auto-Applications
          </h1>
          <p className="text-gray-600 dark:text-gray-300 font-medium">View and track automated form submissions by the Filler Agent.</p>
        </div>
      </div>

      <div className="glass-card rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-600 dark:text-gray-300 font-medium">Loading applications...</div>
        ) : history.length === 0 ? (
          <div className="p-8 text-center text-gray-600 dark:text-gray-300 font-medium">No applications submitted yet.</div>
        ) : (
          <div className="divide-y divide-slate-800">
            {history.map((app: any) => (
              <div key={app.id} className="p-6 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700/30 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 break-words">
                      {app.title || "Untitled Application Form"}
                    </h3>
                    <a 
                      href={app.form_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-blue-400 hover:underline mt-1 block truncate max-w-xl"
                    >
                      {app.form_url}
                    </a>
                    
                    {app.summary_json && (
                      <div className="mt-4 grid grid-cols-2 gap-4 text-sm max-w-3xl">
                        {Object.entries(app.summary_json).map(([key, val]) => (
                          <div key={key} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm/50 p-2 rounded border border-slate-200 dark:border-slate-700/50">
                            <div className="text-xs text-slate-400 dark:text-slate-400 font-semibold truncate">{key}</div>
                            <div className="text-gray-900 dark:text-gray-100 font-bold truncate" title={String(val)}>{String(val)}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="ml-6 flex flex-col items-end flex-shrink-0 space-y-2">
                    <span className={`px-3 py-1 text-xs font-medium rounded-full flex items-center gap-1.5 border
                      ${app.status === 'completed' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 
                        app.status === 'error' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                        'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'}`}
                    >
                      {app.status === 'completed' ? <CheckCircle2 className="w-3.5 h-3.5" /> : 
                       app.status === 'error' ? <AlertCircle className="w-3.5 h-3.5" /> :
                       <Clock className="w-3.5 h-3.5" />}
                      {app.status.toUpperCase()}
                    </span>
                    <span className="text-xs text-slate-400 dark:text-slate-400 font-semibold">
                      {app.submitted_at ? new Date(app.submitted_at).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
