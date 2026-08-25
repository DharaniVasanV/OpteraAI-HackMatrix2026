import React, { useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Cpu, Upload, FileText, Loader2 } from 'lucide-react';
import Analytics from './Analytics';

export default function Settings() {
  const { user, setUser } = useAuth();
  const [formData, setFormData] = useState({
    name: user?.name || '',
    college_name: user?.college_name || '',
    department: user?.department || '',
    course: user?.course || ''
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await axios.put('/auth/me', formData);
      setUser({ ...user, ...res.data.user, email: user?.email || '' });
      alert('Profile updated successfully!');
    } catch (err) {
      console.error(err);
      alert('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const connectBot = async () => {
    try {
      const res = await axios.post("/api/bot/connect");
      if(res.data.auth_url) {
        window.open(res.data.auth_url, '_blank');
      } else {
        alert("Bot connected or session valid!");
      }
    } catch {
      alert("Failed connecting bot.");
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [parseStatus, setParseStatus] = useState<'idle' | 'parsing' | 'done' | 'error'>('idle');

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setParseStatus('parsing');
      const formData = new FormData();
      formData.append('file', e.target.files[0]);
      
      try {
        const parseRes = await axios.post('/api/parser/resume', formData, {
           headers: { 'Content-Type': 'multipart/form-data' }
        });
        await axios.post('/api/career/analyze_resume', {
          extracted_text: parseRes.data.text,
          user_id: user?.email || 'user_1'
        });
        setParseStatus('done');
      } catch (err) {
        setParseStatus('error');
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-900/50">
      <div className="p-8 text-gray-900 dark:text-gray-100 max-w-5xl mx-auto w-full">
        <h1 className="text-3xl font-bold mb-8 flex items-center justify-between">
          My Profile & Settings
        </h1>
        
        <div className="space-y-8">
        <div className="glass-card p-6 rounded-xl space-y-4">
          <h3 className="text-lg font-bold dark:text-white">Profile Settings</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 dark:text-slate-400 font-medium">Update your personal details below. This is permanently saved in the database.</p>
          <form className="space-y-4 max-w-md" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-bold text-gray-900 dark:text-gray-100 dark:text-slate-300 mb-1">Full Name</label>
              <input type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full bg-slate-50 dark:bg-slate-900 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 dark:border-white/10 rounded-lg px-4 py-2 text-sm text-gray-900 dark:text-gray-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0066FF]/30" />
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-900 dark:text-gray-100 dark:text-slate-300 mb-1">Email Address (Read Only)</label>
              <input type="email" value={user?.email || ''} disabled className="w-full bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 dark:border-white/10 rounded-lg px-4 py-2 text-sm text-gray-600 dark:text-gray-300 focus:outline-none cursor-not-allowed opacity-70" />
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-900 dark:text-gray-100 dark:text-slate-300 mb-1">College Name</label>
              <input type="text" placeholder="e.g. Sri Eshwar College of Engineering" value={formData.college_name} onChange={e => setFormData({...formData, college_name: e.target.value})} className="w-full bg-slate-50 dark:bg-slate-900 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 dark:border-white/10 rounded-lg px-4 py-2 text-sm text-gray-900 dark:text-gray-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0066FF]/30" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-gray-900 dark:text-gray-100 dark:text-slate-300 mb-1">Department</label>
                <input type="text" placeholder="e.g. CSE" value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} className="w-full bg-slate-50 dark:bg-slate-900 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 dark:border-white/10 rounded-lg px-4 py-2 text-sm text-gray-900 dark:text-gray-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0066FF]/30" />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-900 dark:text-gray-100 dark:text-slate-300 mb-1">Course / Year</label>
                <input type="text" placeholder="e.g. B.E 3rd Year" value={formData.course} onChange={e => setFormData({...formData, course: e.target.value})} className="w-full bg-slate-50 dark:bg-slate-900 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 dark:border-white/10 rounded-lg px-4 py-2 text-sm text-gray-900 dark:text-gray-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0066FF]/30" />
              </div>
            </div>
            
            <button type="submit" disabled={saving} className="px-6 py-2 bg-[#0066FF] text-white rounded-lg hover:bg-blue-600 transition font-bold text-sm disabled:opacity-50">
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </div>

        <div className="glass-card p-6 rounded-xl space-y-4">
          <h3 className="text-lg font-bold dark:text-white">Google Account Sync</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 dark:text-slate-400 font-medium">Sync OpteraAI with your calendar and email inbox.</p>
          <a href={`/gmail/oauth?user_email=${user?.email || ''}`} className="inline-block px-6 py-2 bg-slate-100 dark:bg-slate-800 text-gray-900 dark:text-gray-100 dark:text-white border border-slate-200 dark:border-slate-700 dark:border-white/10 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition font-bold text-sm">Link Google Account</a>
        </div>
        
        <div className="glass-card p-6 rounded-xl space-y-4 border-l-4 border-[#0066FF]">
          <h3 className="text-lg font-bold dark:text-white flex items-center gap-2"><Cpu className="w-5 h-5 text-[#0066FF]" /> Playwright Bot Session</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 dark:text-slate-400 font-medium">Initialize the headless browser session for automated Zoom/Teams meeting joining.</p>
          <button onClick={connectBot} className="inline-flex items-center space-x-2 px-6 py-2 bg-[#0066FF] text-white rounded-lg hover:bg-blue-600 transition font-bold text-sm shadow-md">
            <span>Connect Bot Session</span>
          </button>
        </div>

        {/* Resume Parser block */}
        <div className="glass-card p-6 rounded-xl space-y-4 border-l-4 border-violet-500">
          <h3 className="text-lg font-bold dark:text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-violet-500" /> Automated Resume Parsing
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 dark:text-slate-400 font-medium max-w-2xl">
            Drag and drop your latest resume. It will be automatically parsed via OCR and the extracted payload will securely bypass manual triggers to instantly update your Career Agent's context.
          </p>
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 dark:border-slate-600 hover:border-violet-500 dark:hover:border-violet-400 bg-slate-50 hover:bg-violet-50 dark:bg-slate-800 dark:hover:bg-violet-900/10 rounded-xl p-8 text-center cursor-pointer transition-all mt-4"
          >
            <input type="file" className="hidden" ref={fileInputRef} onChange={handleResumeUpload} accept="application/pdf,image/*" />
            {parseStatus === 'idle' && (
              <div className="flex flex-col items-center gap-3">
                <Upload className="w-8 h-8 text-slate-400" />
                <span className="font-bold text-slate-700 dark:text-slate-300">Click or drag resume here to Auto-Sync with Career Agent</span>
              </div>
            )}
            {parseStatus === 'parsing' && (
              <div className="flex flex-col items-center gap-3 text-violet-600 dark:text-violet-400">
                <Loader2 className="w-8 h-8 animate-spin" />
                <span className="font-bold">Extracting text & synchronizing with Career AI...</span>
              </div>
            )}
            {parseStatus === 'done' && (
              <div className="flex flex-col items-center gap-3 text-emerald-600 dark:text-emerald-400">
                <FileText className="w-8 h-8" />
                <span className="font-bold">Resume successfully parsed & Career Agent updated!</span>
              </div>
            )}
            {parseStatus === 'error' && (
              <div className="flex flex-col items-center gap-3 text-rose-600 dark:text-rose-400">
                <Upload className="w-8 h-8" />
                <span className="font-bold">Error parsing resume or updating Agent. Please try again.</span>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
    
    <div className="mt-8 border-t border-slate-200 dark:border-slate-800">
      <div className="pt-8">
        <h2 className="text-2xl font-bold px-8 max-w-7xl mx-auto mb-4 text-gray-900 dark:text-white">Live User Analytics</h2>
        <div className="h-full relative">
          <Analytics />
        </div>
      </div>
    </div>
  </div>
  );
}
