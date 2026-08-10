import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Briefcase, Zap, Cpu, List, Target, FileText, User, ExternalLink } from 'lucide-react';

type Tab = 'career' | 'resumes';

export default function Career() {
  const [tab, setTab] = useState<Tab>('career');
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [resumes, setResumes] = useState<any[]>([]);
  const [loadingCareer, setLoadingCareer] = useState(true);
  const [loadingResumes, setLoadingResumes] = useState(true);

  useEffect(() => { fetchAnalyses(); fetchResumes(); }, []);

  const fetchAnalyses = async () => {
    try {
      const res = await axios.get('/api/career/analyses');
      const data = Array.isArray(res.data) ? res.data : [res.data];
      const sorted = data.sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setAnalyses(sorted.slice(0, 3)); // Show latest 3
    } catch (e) { console.error(e); }
    finally { setLoadingCareer(false); }
  };

  const fetchResumes = async () => {
    try {
      const res = await axios.get('/api/resume/list');
      const data = Array.isArray(res.data) ? res.data : [res.data];
      setResumes(data.sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5));
    } catch (e) { console.error(e); }
    finally { setLoadingResumes(false); }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400 border-green-500/20 bg-green-500/10';
    if (score >= 50) return 'text-amber-400 border-amber-500/20 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/20 bg-rose-500/10';
  };

  const createLearningPlan = async (analysis: any) => {
    try {
      const sd = analysis.structured_data || {};
      const missingSkills: string[] = sd.skill_gap || sd.skills?.missing || [];
      const prompt = `Based on the career analysis, the missing skills are: ${missingSkills.join(', ') || 'general software engineering skills'}. Create a personalized 12-step learning plan.`;
      const res = await axios.post('/api/learning/create', { prompt, experience_level: 'intermediate' });
      if (res.data?.status === 'failed') {
          throw new Error(res.data.reason || 'Verification failure or rate limit.');
      }
      alert('Learning plan created! Check the Learning Mentor module.');
    } catch (err: any) { 
        console.error(err);
        alert(`Failed to create learning plan: ${err.message || 'Server error'}`); 
    }
  };

  return (
    <div className="p-8 text-white max-w-7xl mx-auto h-full overflow-y-auto">
      <div className="flex items-center gap-3 mb-6">
        <Briefcase className="w-10 h-10 text-emerald-400" />
        <div>
          <h1 className="text-4xl font-extrabold bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
            Career Intelligence
          </h1>
          <p className="text-slate-400">AI-powered ATS scoring & skill gap analysis.</p>
        </div>
      </div>

      <div className="space-y-8">
        {loadingCareer ? (
          <div className="animate-pulse space-y-4">
            <div className="h-64 bg-slate-800 rounded-xl"></div>
            <div className="h-64 bg-slate-800 rounded-xl"></div>
          </div>
        ) : analyses.length > 0 ? analyses.map((analysis, idx) => {
          const data = analysis.structured_data || {};
          const ats = data.ats || { score: analysis.ats_score || 0, breakdown: {} };
          const emp = data.employability_score || analysis.employability_score || 0;
          const { technical = [], missing = [] } = data.skills || {};
          const skillGap: string[] = missing.length > 0 ? missing : (data.skill_gap || []);

          return (
            <div key={analysis.id || idx} className="glass-panel rounded-2xl border border-slate-700/50 overflow-hidden shadow-xl">
              <div className="p-6 bg-slate-900/50 border-b border-slate-800 flex justify-between items-start flex-wrap gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <User className="w-5 h-5 text-emerald-400" />
                    <h2 className="text-2xl font-bold">{data.profile?.name || analysis.user_name || 'Candidate'}</h2>
                    <span className="text-xs font-normal px-2 py-0.5 bg-slate-800 rounded text-slate-400">
                      {new Date(analysis.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                  </div>
                  <p className="text-slate-400 max-w-2xl text-sm leading-relaxed">
                    {data.career_summary || analysis.career_summary || 'No summary available.'}
                  </p>
                </div>
                <div className="flex gap-4">
                  <div className={`p-4 rounded-xl border flex flex-col items-center min-w-[90px] ${getScoreColor(ats.score)}`}>
                    <span className="text-[10px] uppercase font-bold opacity-80 mb-1">ATS Score</span>
                    <span className="text-3xl font-black">{ats.score}%</span>
                  </div>
                  <div className={`p-4 rounded-xl border flex flex-col items-center min-w-[90px] ${getScoreColor(emp)}`}>
                    <span className="text-[10px] uppercase font-bold opacity-80 mb-1">Employability</span>
                    <span className="text-3xl font-black">{emp}%</span>
                  </div>
                </div>
              </div>

              <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Skills */}
                <div className="space-y-3">
                  <h3 className="text-base font-bold flex items-center gap-2 text-indigo-400"><Cpu className="w-4 h-4"/> Skill Matrix</h3>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-2">Technical Stack</p>
                    <div className="flex flex-wrap gap-1.5">{technical.length > 0 ? technical.slice(0, 12).map((s: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded text-xs border border-indigo-500/30">{s}</span>
                    )) : <span className="text-slate-500 text-xs">None detected</span>}
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] text-rose-400 uppercase font-bold mb-2 mt-3">Missing / Skill Gaps</p>
                    <div className="flex flex-wrap gap-1.5">{skillGap.length > 0 ? skillGap.slice(0, 10).map((s: any, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-rose-500/20 text-rose-300 rounded text-xs border border-rose-500/30">{typeof s === 'string' ? s : JSON.stringify(s)}</span>
                    )) : <span className="text-slate-500 text-xs">None identified</span>}
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="space-y-3">
                  <h3 className="text-base font-bold flex items-center gap-2 text-amber-400"><Target className="w-4 h-4"/> Recommendations</h3>
                  <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-700 max-h-52 overflow-y-auto">
                    <ul className="space-y-2">
                      {data.recommendations?.slice(0, 6).map((rec: string, i: number) => (
                        <li key={i} className="flex gap-2 text-xs text-slate-300 leading-relaxed"><span className="text-amber-500 mt-0.5 shrink-0">→</span>{rec}</li>
                      ))}
                      {(!data.recommendations || data.recommendations.length === 0) && (
                        <p className="text-slate-500 text-xs">No specific recommendations.</p>
                      )}
                    </ul>
                  </div>
                </div>

                {/* ATS + CTA */}
                <div className="flex flex-col justify-between space-y-3">
                  <div>
                    <h3 className="text-base font-bold flex items-center gap-2 text-emerald-400 mb-3"><List className="w-4 h-4"/> ATS Breakdown</h3>
                    <div className="space-y-2">
                      {Object.entries(ats.breakdown || {}).map(([key, val]: any) => (
                        <div key={key}>
                          <div className="flex justify-between text-[10px] mb-1 text-slate-400">
                            <span className="capitalize">{key.replace(/_/g, ' ')}</span><span>{val}%</span>
                          </div>
                          <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 transition-all" style={{ width: `${val}%` }}></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <button
                    onClick={() => createLearningPlan(analysis)}
                    className="w-full py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 rounded-lg font-bold shadow-lg flex items-center justify-center gap-2 transition-all text-sm mt-2"
                  >
                    <Zap className="w-4 h-4" /> Auto-Generate Learning Path
                  </button>
                </div>
              </div>
            </div>
          );
        }) : (
          <div className="glass-panel p-12 text-center text-slate-500 rounded-xl border border-dashed border-slate-700">
            <Briefcase className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="font-medium">No career analyses found.</p>
            <p className="text-sm mt-2">Go to Resume module → upload → click "Pass to Career Agent".</p>
          </div>
        )}
      </div>
    </div>
  );
}
