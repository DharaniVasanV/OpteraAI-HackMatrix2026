import React, { useState } from 'react';
import axios from 'axios';
import { Bot, Send, BrainCircuit, FileSearch, Sparkles } from 'lucide-react';
import { cn } from '../lib/utils';

export default function Knowledge() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setLoading(true);
    try {
      const res = await axios.get(`/api/knowledge/ask?query=${encodeURIComponent(query)}`);
      setAnswer(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleSync = async () => {
    setLoading(true);
    try {
      await axios.post('/api/knowledge/sync');
      alert("Vector Data Synchronization complete!");
    } catch (err) {
      console.error(err);
      alert("Synchronization failed.");
    }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col pt-4 relative">
      <div className="absolute top-4 right-4 flex space-x-3">
         <button onClick={handleSync} disabled={loading} className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-gray-900 dark:text-gray-100 rounded-lg flex items-center gap-2 text-sm">
            <Sparkles className="w-4 h-4"/> Sync Data
         </button>
      </div>
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full mt-6">
        <div className="text-center mb-8">
          <BrainCircuit className="w-12 h-12 text-primary mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">OpteraAI Knowledge Base</h1>
          <p className="text-gray-600 dark:text-gray-300 font-medium">Powered by Llama-3 and ChromaDB Vector RAG</p>
        </div>

        <div className="flex-1 overflow-y-auto w-full mb-6 relative">
           {!answer && !loading && (
              <div className="h-full flex flex-col items-center justify-center space-y-4 opacity-50">
                <Bot className="w-20 h-20 text-slate-600" />
                <p className="text-slate-400 dark:text-slate-400 font-semibold">Ask any question regarding your meetings, emails, or personal data.</p>
              </div>
           )}
           {loading && (
             <div className="flex justify-center my-8">
               <div className="animate-pulse flex items-center space-x-2 text-primary">
                 <Sparkles className="w-5 h-5 animate-spin" />
                 <span>Scanning vector database...</span>
               </div>
             </div>
           )}
           {answer && !loading && (
             <div className="glass-card p-8 rounded-xl space-y-6 animate-in slide-in-from-bottom-4 border border-slate-200 dark:border-slate-700 shadow-xl">
               <div>
                 <h4 className="text-sm font-bold text-gray-600 dark:text-gray-300 uppercase tracking-wider mb-3">AI Synthesis</h4>
                 <p className="text-lg text-gray-900 dark:text-gray-100 font-medium leading-relaxed">{answer.answer}</p>
               </div>
               
               <div className="grid grid-cols-2 gap-4">
                 <div className="p-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm rounded-lg">
                   <h5 className="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2 flex items-center"><FileSearch className="w-4 h-4 mr-2" /> Top Sources</h5>
                   <ul className="space-y-2">
                     {answer.sources?.map((s: any, i: number) => (
                       <li key={i} className="text-sm text-gray-900 dark:text-gray-100 font-bold flex justify-between">
                         <span className="truncate pr-4">{s.title}</span>
                         <span className="text-[#0066FF]">{s.relevance}</span>
                       </li>
                     ))}
                   </ul>
                 </div>
                 <div className="p-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm rounded-lg flex flex-col justify-center items-center">
                   <div className="text-4xl font-bold text-[#0066FF] mb-1">
                     {(answer.similarity_score * 100).toFixed(0)}%
                   </div>
                   <div className="text-sm text-gray-600 dark:text-gray-300 font-medium">Vector Confidence Score</div>
                 </div>
               </div>
             </div>
           )}
        </div>

        <form onSubmit={handleAsk} className="relative mt-auto">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask your second brain..." 
            className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm rounded-xl pl-6 pr-14 py-4 text-gray-900 dark:text-gray-100 font-medium placeholder-[#A0AEC0] focus:ring-2 focus:ring-[#0066FF]/50 shadow-xl outline-none transition-all"
          />
          <button 
            type="submit" 
            disabled={loading}
            className="absolute right-2 top-2 p-2 rounded-lg btn-primary-custom disabled:opacity-50 transition-colors shadow-none"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
