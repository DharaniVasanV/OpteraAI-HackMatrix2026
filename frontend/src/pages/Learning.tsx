import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BookOpen, Zap, Target, Loader2, Play, CheckCircle } from 'lucide-react';

export default function Learning() {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [manualInput, setManualInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const res = await axios.get('/api/learning/plans');
      if (Array.isArray(res.data)) {
        setPlans(res.data);
      } else {
        setPlans([]); // Default if object
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleManualGenerate = async () => {
    if (!manualInput.trim()) return;
    setIsGenerating(true);
    try {
      const resp = await axios.post('/api/learning/create', { prompt: manualInput.trim(), experience_level: 'beginner' });
      if (resp.data?.status === 'failed') {
          throw new Error(resp.data.reason || "Failed by Learning Agent validation or rate-limit");
      }
      setManualInput('');
      fetchPlans();
    } catch (err: any) {
      console.error("Failed to generate plan:", err);
      alert(`Failed to generate plan: ${err.message || 'Server Error'}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const getDifficultyColor = (diff: string) => {
    switch (diff?.toLowerCase()) {
       case 'beginner': return 'text-green-400 bg-green-500/10 border-green-500/20';
       case 'advanced': return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
       default: return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    }
  };

  return (
    <div className="p-8 text-white max-w-7xl mx-auto h-full overflow-y-auto space-y-8">
      <div className="flex items-center gap-3">
        <BookOpen className="w-10 h-10 text-pink-400" />
        <div>
           <h1 className="text-4xl font-extrabold bg-gradient-to-r from-pink-400 to-rose-500 bg-clip-text text-transparent">
             Learning Mentor
           </h1>
           <p className="text-slate-400">Personalized 12-step AI curriculums to close skill gaps.</p>
        </div>
      </div>

      <div className="glass-panel p-6 rounded-xl border border-slate-700 shadow-xl flex items-end gap-4">
         <div className="flex-1">
            <label className="block text-sm font-bold text-slate-300 mb-2">Manual Generate Learning Path 💡</label>
            <input 
              type="text"
              value={manualInput}
              onChange={(e) => setManualInput(e.target.value)}
              placeholder="e.g. Master Rust for Web3 backend development..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-pink-500 transition-colors"
              disabled={isGenerating}
            />
         </div>
         <button 
           onClick={handleManualGenerate}
           disabled={isGenerating || !manualInput.trim()}
           className="px-6 py-3 bg-pink-600 hover:bg-pink-500 text-white font-bold rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
         >
           {isGenerating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
           Generate
         </button>
      </div>

      <div className="space-y-6">
         {loading ? (
           <div className="animate-pulse space-y-4">
              <div className="h-64 bg-slate-800 rounded-xl"></div>
           </div>
         ) : plans.length > 0 ? (
           plans.map((plan, i) => {
              const data = plan || {};
              // Convert the flat daily_plan strings into structured curriculum steps
              const dailyPlan = data.daily_plan || [];
              const curriculum = dailyPlan.length > 0 ? dailyPlan.map((d: string, idx: number) => {
                  const parts = d.split(':');
                  return {
                      topic: parts.length > 1 ? parts[1].trim() : d,
                      description: parts.length > 1 ? parts.join(':') : 'Daily learning goal.',
                      duration_hours: 2,
                      step_number: idx + 1
                  }
              }) : (data.recommended_topics || []).map((t: string, idx: number) => ({
                  topic: t,
                  description: 'Core topic to master.',
                  duration_hours: 4,
                  step_number: idx + 1
              }));

              const progress = data.progress?.percentage || 0;
              const difficulty = data.current_level || 'Intermediate';

              return (
                <div key={plan.plan_id || i} className="glass-panel rounded-xl overflow-hidden border border-slate-700/50">
                  <div className="bg-slate-900/50 p-6 border-b border-slate-800 flex justify-between items-start flex-wrap gap-4">
                     <div>
                       <h2 className="text-2xl font-bold mb-2 capitalize">{data.career_goal || 'Custom Learning Path'}</h2>
                       <p className="text-slate-400 max-w-2xl text-sm leading-relaxed">{data.motivation || 'Focus on your daily tasks to achieve your learning goal.'}</p>
                     </div>
                     <div className="flex gap-3">
                       <span className={`px-3 py-1 rounded text-xs uppercase font-bold border ${getDifficultyColor(difficulty)}`}>
                          {difficulty}
                       </span>
                       <span className="px-3 py-1 bg-slate-800 text-slate-300 rounded text-xs uppercase font-bold border border-slate-700">
                          {curriculum.length} STEPS
                       </span>
                     </div>
                  </div>
                  
                  <div className="p-6">
                     <div className="mb-4">
                        <div className="flex justify-between text-sm mb-1 font-bold">
                           <span className="text-slate-400">Mastery Progress</span>
                           <span className="text-pink-400">{progress}%</span>
                        </div>
                        <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                           <div className="h-full bg-gradient-to-r from-pink-500 to-rose-500 transition-all duration-1000" style={{ width: `${progress}%`}}></div>
                        </div>
                     </div>

                     <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
                        {curriculum.map((mod: any, idx: number) => (
                           <div key={idx} className="bg-slate-900 border border-slate-800 p-4 rounded-lg hover:border-pink-500/30 transition-colors relative group">
                              <span className="absolute -top-3 -left-3 w-8 h-8 bg-slate-800 text-slate-400 group-hover:bg-pink-600 group-hover:text-white rounded-full flex items-center justify-center font-bold text-sm transition-colors border border-slate-700">
                                {mod.step_number || idx + 1}
                              </span>
                              <div className="ml-3">
                                 <h4 className="font-bold text-slate-200 mb-1 leading-tight">{mod.topic}</h4>
                                 <p className="text-xs text-slate-500 line-clamp-2">{mod.description}</p>
                                 <div className="mt-3 flex justify-between items-center">
                                    <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wider">
                                       {mod.duration_hours} HRS
                                    </span>
                                    <button className="text-pink-400 hover:text-pink-300 transition-colors p-1 group/btn">
                                       <CheckCircle className="w-4 h-4 fill-current group-hover/btn:scale-110 transition-transform" />
                                    </button>
                                 </div>
                              </div>
                           </div>
                        ))}
                     </div>
                  </div>
                </div>
              )
           })
         ) : (
           <div className="glass-panel p-12 text-center text-slate-500 rounded-xl border border-dashed border-slate-700">
             <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
             <p>No learning curriculums found.</p>
             <p className="text-sm mt-2">Generate one above or analyze your career profile.</p>
           </div>
         )}
      </div>
    </div>
  );
}
