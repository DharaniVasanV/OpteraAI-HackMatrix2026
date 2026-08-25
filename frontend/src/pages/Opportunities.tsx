import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { Loader2, Zap } from 'lucide-react';
import { Email, EmailCard } from '../components/EmailCard';

export default function Opportunities() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeCategory, setActiveCategory] = useState('ALL');

  const categories = ['ALL', 'Hackathon', 'Internship'];


  const fetchOpportunities = useCallback(async () => {
    try {
      const res = await axios.get('/api/inbox');
      const ops = res.data.filter((e: Email) => {
        const cat = e.category?.toLowerCase() || '';
        const title = (e.title || '').toLowerCase();
        const subject = (e.subject || '').toLowerCase();
        
        // Exact constraint: Opportunities contains ONLY hackathons and internships
        const isOpportunityCategory = cat === 'internship' || cat === 'hackathon';
        const hasKeyword = 
          title.includes('hackathon') || title.includes('internship') ||
          subject.includes('hackathon') || subject.includes('internship');
          
        return isOpportunityCategory || hasKeyword;
      });
      setEmails(ops);
    } catch {
      setError('Failed to fetch opportunities.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchOpportunities(); }, [fetchOpportunities]);

  if (loading) return (
    <div className="p-8 flex items-center space-x-3 text-gray-600 dark:text-gray-300 font-medium">
      <Loader2 className="w-5 h-5 animate-spin text-primary" />
      <span>Loading Opportunities…</span>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100 mb-1">Opportunities</h1>
          <p className="text-gray-600 dark:text-gray-300 font-medium text-sm">
            Internships, Hackathons & Jobs parsed from 1-Click Auto Apply capable Filler Agent
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="flex gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm p-2 rounded-xl overflow-x-auto custom-scrollbar border border-slate-200 dark:border-slate-700">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
              activeCategory === cat
                ? 'bg-violet-600 text-white shadow-[0_0_10px_rgba(139,92,246,0.5)]'
                : 'text-gray-600 dark:text-gray-300 font-medium hover:text-gray-900 dark:text-gray-100 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {emails
          .filter(e => activeCategory === 'ALL' || (e.category || '').toLowerCase() === activeCategory.toLowerCase())
          .map((email, i) => (
            <EmailCard key={email.id || i} email={email} />
        ))}
        {emails.filter(e => activeCategory === 'ALL' || (e.category || '').toLowerCase() === activeCategory.toLowerCase()).length === 0 && !error && (
          <div className="text-center p-12 glass-card rounded-xl text-gray-600 dark:text-gray-300 font-medium">
            <Zap className="w-10 h-10 mx-auto mb-4 opacity-40 text-yellow-400" />
            <p>No new opportunities detected in your inbox.</p>
          </div>
        )}
      </div>
    </div>
  );
}
