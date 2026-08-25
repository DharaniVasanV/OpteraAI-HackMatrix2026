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
  const [editMode, setEditMode] = useState<'idle'|'options'|'add'|'delete'>('idle');

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
        setEditMode('idle');
        setNewCatName('');
        setActiveCategory(res.data.name);
      }
    } catch (e) {
      console.error(e);
      alert('Failed to add custom category');
    }
  };

  const handleDeleteCategory = async (catName: string) => {
    try {
      await axios.delete(`/api/categories/${catName}`);
      setCategories(prev => prev.filter(c => c !== catName));
      if (activeCategory === catName) setActiveCategory('ALL');
    } catch (e) {
      // Fallback local UI delete if backend route is unavailable
      setCategories(prev => prev.filter(c => c !== catName));
      if (activeCategory === catName) setActiveCategory('ALL');
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
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 dark:text-gray-100 mb-2">Smart Inbox</h1>
          <p className="text-gray-600 dark:text-gray-300 text-sm font-medium">
            Processed by Watcher → Classification → Priority → Research Agents
          </p>
        </div>
        <button
          onClick={triggerSync}
          disabled={syncing}
          className="flex items-center space-x-2 px-5 py-2.5 btn-primary-custom rounded-xl text-sm font-bold transition-transform shadow-lg"
        >
          {syncing ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCw className="w-5 h-5" />}
          <span>{syncing ? 'Syncing…' : 'Sync Gmail'}</span>
        </button>
      </div>

      {error && (
        <div className="bg-[#C5192D]/10 border border-[#C5192D]/20 text-[#C5192D] p-5 rounded-xl text-sm font-semibold shadow-sm">
          {error}
        </div>
      )}

      <div className="flex gap-2 glass-panel p-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm items-center">
        <div className="flex gap-2 overflow-x-auto custom-scrollbar flex-1 pb-1 sm:pb-0 pt-2 px-1">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => {
                if (editMode === 'delete' && cat !== 'ALL') handleDeleteCategory(cat);
                else setActiveCategory(cat);
              }}
              className={`relative px-4 py-2 rounded-xl text-sm font-bold transition-all whitespace-nowrap group ${
                activeCategory === cat
                  ? 'bg-[#0066FF] text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:text-gray-100 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700'
              } ${editMode === 'delete' && cat !== 'ALL' ? 'hover:bg-rose-100 dark:hover:bg-rose-900/40 !text-rose-600 dark:!text-rose-400' : ''}`}
            >
              {cat}
              {editMode === 'delete' && cat !== 'ALL' && (
                 <span className="absolute -top-1 -right-1 bg-rose-500 text-white w-4 h-4 rounded-full text-[10px] flex items-center justify-center shadow-sm">x</span>
              )}
            </button>
          ))}
        </div>
        
        <div className="pl-3 border-l border-slate-200 dark:border-slate-700 flex items-center">
          {editMode === 'idle' && (
            <button
              onClick={() => setEditMode('options')}
              className="px-4 py-2 rounded-xl text-sm font-bold text-gray-900 dark:text-gray-100 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-900 shadow-sm transition-all whitespace-nowrap flex-shrink-0"
            >
              Edit
            </button>
          )}
          {editMode === 'options' && (
            <div className="flex items-center space-x-2">
              <button onClick={() => setEditMode('add')} className="px-4 py-2 bg-[#0066FF] hover:bg-blue-600 text-white text-sm rounded-xl transition-colors font-bold shadow-sm">Add</button>
              <button onClick={() => setEditMode('delete')} className="px-4 py-2 bg-rose-500 hover:bg-rose-600 text-white text-sm rounded-xl transition-colors font-bold shadow-sm">Delete</button>
              <button onClick={() => setEditMode('idle')} className="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 text-sm rounded-xl font-bold transition-colors">Cancel</button>
            </div>
          )}
          {editMode === 'add' && (
            <div className="flex items-center space-x-2">
              <input 
                type="text" 
                value={newCatName} 
                onChange={e => setNewCatName(e.target.value)} 
                placeholder="Ex: Travel" 
                className="px-4 py-2 text-sm bg-slate-50 dark:bg-slate-900 text-gray-900 dark:text-gray-100 rounded-xl border border-slate-200 dark:border-slate-700 shadow-inner outline-none w-32 focus:border-[#0066FF]/50" 
                onKeyDown={e => e.key === 'Enter' && handleAddCategory()}
                autoFocus
              />
              <button onClick={handleAddCategory} className="px-4 py-2 bg-[#2E9A47] hover:bg-green-700 text-white text-sm rounded-xl transition-colors font-bold shadow-sm">Save</button>
              <button onClick={() => setEditMode('idle')} className="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 text-sm rounded-xl font-bold transition-colors">Cancel</button>
            </div>
          )}
          {editMode === 'delete' && (
            <div className="flex items-center space-x-2">
               <span className="text-sm text-rose-500 font-bold px-2 whitespace-nowrap">Select to delete</span>
               <button onClick={() => setEditMode('idle')} className="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 text-sm rounded-xl font-bold transition-colors">Done</button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
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
