import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { Mail, Loader2, RefreshCw } from 'lucide-react';
import { Email, EmailCard } from '../components/EmailCard';

export default function Inbox() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');
  const [activeCategory, setActiveCategory] = useState('ALL');

  const [categories, setCategories] = useState<string[]>(['ALL', 'Meeting', 'Form', 'Scholarship', 'Internship', 'Placement', 'Contest', 'Leetcode', 'CFI']);
  const [newCatName, setNewCatName] = useState('');
  const [showCatInput, setShowCatInput] = useState(false);

  useEffect(() => {
    axios.get('/api/categories').then(res => {
      if (res.data && Array.isArray(res.data)) {
        // Exclude Hackathon from Inbox tabs
        const filteredData = res.data.filter((c: string) => c.toLowerCase() !== 'hackathon');
        const cats = new Set(['ALL', ...filteredData]);
        setCategories(Array.from(cats));
      }
    }).catch(console.error);
  }, []);

  const handleAddCategory = async () => {
    if (!newCatName.trim()) return;
    try {
      const res = await axios.post('/api/categories', { name: newCatName.trim() });
      if (res.data?.name) {
        setCategories(prev => Array.from(new Set([...prev, res.data.name])));
        setShowCatInput(false);
        setNewCatName('');
        setActiveCategory(res.data.name);
      }
    } catch (e) {
      console.error(e);
      alert('Failed to add custom category');
    }
  };

  const fetchInbox = useCallback(async () => {
    try {
      const res = await axios.get('/api/inbox');
      setEmails(res.data);
    } catch {
      setError('Failed to fetch inbox from Watcher Agent.');
    } finally {
      setLoading(false);
    }
  }, []);

  const triggerSync = async () => {
    setSyncing(true);
    try {
      await axios.post('/api/sync', {});
      await fetchInbox();
    } catch {
      setError('Sync failed — check Watcher Agent (port 8001).');
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => { fetchInbox(); }, [fetchInbox]);

  if (loading) return (
    <div className="p-8 flex items-center space-x-3 text-slate-400">
      <Loader2 className="w-5 h-5 animate-spin text-primary" />
      <span>Loading Smart Inbox…</span>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Smart Inbox</h1>
          <p className="text-slate-400 text-sm">
            Processed by Watcher → Classification → Priority → Research Agents
          </p>
        </div>
        <button
          onClick={triggerSync}
          disabled={syncing}
          className="flex items-center space-x-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg text-sm font-semibold transition-colors"
        >
          {syncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          <span>{syncing ? 'Syncing…' : 'Sync Gmail'}</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="flex gap-2 bg-slate-900 p-2 rounded-xl border border-slate-800 items-center">
        <div className="flex gap-2 overflow-x-auto custom-scrollbar flex-1">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
                activeCategory === cat
                  ? 'bg-violet-600 text-white shadow-[0_0_10px_rgba(139,92,246,0.5)]'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        
        <div className="pl-2 border-l border-slate-700">
          {showCatInput ? (
            <div className="flex items-center space-x-2">
              <input 
                type="text" 
                value={newCatName} 
                onChange={e => setNewCatName(e.target.value)} 
                placeholder="Ex: Travel" 
                className="px-3 py-1 text-sm bg-slate-800 text-white rounded border border-slate-700 outline-none w-28" 
                onKeyDown={e => e.key === 'Enter' && handleAddCategory()}
                autoFocus
              />
              <button onClick={handleAddCategory} className="px-3 py-1 bg-green-500 hover:bg-green-600 text-white text-sm rounded transition-colors font-medium">Add</button>
              <button onClick={() => setShowCatInput(false)} className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded transition-colors font-medium">Cancel</button>
            </div>
          ) : (
            <button
              onClick={() => setShowCatInput(true)}
              className="px-4 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-700 hover:bg-slate-600 shadow-[0_0_10px_rgba(255,255,255,0.1)] transition-all whitespace-nowrap flex-shrink-0"
            >
              + Add Category
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {emails
          .filter(e => {
            const catLower = (e.category || '').toLowerCase();
            if (catLower === 'hackathon') return false; // Hide Hackathons from Inbox
            return activeCategory === 'ALL' || catLower === activeCategory.toLowerCase();
          })
          .map((email, i) => (
            <EmailCard key={email.id || i} email={email} />
        ))}
        {emails.filter(e => {
            const catLower = (e.category || '').toLowerCase();
            if (catLower === 'hackathon') return false;
            return activeCategory === 'ALL' || catLower === activeCategory.toLowerCase();
        }).length === 0 && !error && (
          <div className="text-center p-12 glass-panel rounded-xl text-slate-400">
            <Mail className="w-10 h-10 mx-auto mb-4 opacity-40" />
            <p>No emails found in this category.</p>
          </div>
        )}
      </div>
    </div>
  );
}
