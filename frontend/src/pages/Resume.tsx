import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, Bot, ChevronRight, FileText, Briefcase } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Resume() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [careerAnalysis, setCareerAnalysis] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post('/api/resume/upload', formData);
      setResult(res.data);
    } catch(err) {
      console.error(err);
      alert("Failed to parse resume.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleCareerAnalysis = async () => {
    if (!result || !result.raw_text) return;
    setIsAnalyzing(true);
    try {
      const payload = { content: result.raw_text };
      const res = await axios.post('/api/career/analyze', payload);
      setCareerAnalysis(res.data);
    } catch(err) {
      console.error("Career Analysis Error:", err);
      alert("Career agent failed to analyze.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="p-8 text-gray-900 dark:text-gray-100 max-w-5xl mx-auto h-full overflow-y-auto">
      <div className="flex items-center gap-3 mb-2">
        <UploadCloud className="w-10 h-10 text-blue-400" />
        <h1 className="text-3xl font-bold">Resume Extractor</h1>
      </div>
      <p className="text-gray-600 dark:text-gray-300 font-medium mb-8">Upload your resume to instantly extract key metadata.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Upload Panel */}
        <div className="glass-card p-8 rounded-2xl h-fit border border-slate-200 dark:border-slate-700 shadow-xl relative overflow-hidden group hover:border-blue-500/50 transition-all">
          <div className="absolute inset-0 pointer-events-none bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity z-0"></div>
          <h2 className="relative z-10 text-xl font-bold mb-6 flex items-center gap-2"><FileText className="w-5 h-5 text-blue-400"/> Upload PDF/DOCX</h2>
          
          <div className="relative z-10 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-8 text-center hover:border-blue-400 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700/50 transition-all mb-6">
            <input 
              type="file" 
              accept=".pdf,.docx,.txt"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-50"
              onChange={(e) => setFile(e.target.files && e.target.files.length > 0 ? e.target.files[0] : null)}
            />
            <UploadCloud className="w-12 h-12 mx-auto mb-4 text-gray-600 dark:text-gray-300 font-medium group-hover:text-blue-400" />
            <p className="text-gray-900 dark:text-gray-100 font-bold font-medium">
              {file ? file.name : "Drag & drop or click to upload"}
            </p>
            {!file && <p className="text-xs text-slate-400 dark:text-slate-400 font-semibold mt-2">Supported formats: PDF, DOCX, TXT</p>}
          </div>

          <button 
            onClick={handleUpload}
            disabled={!file || isUploading}
            className="relative z-10 w-full py-3 bg-[#0066FF] hover:bg-blue-600 text-white rounded-lg font-bold disabled:opacity-50 transition-colors shadow-lg shadow-blue-900/20"
          >
            {isUploading ? 'Parsing Resume...' : 'Extract Data'}
          </button>
        </div>

        {/* Results Panel */}
        {result && (
          <div className="glass-card p-8 rounded-2xl flex flex-col justify-between h-fit animate-fade-in border border-slate-200 dark:border-slate-700 shadow-xl space-y-6">
            <div>
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-green-600">
                <Bot className="w-5 h-5" /> Extraction Successful
              </h3>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                  <p className="text-xs text-slate-400 dark:text-slate-400 font-semibold uppercase font-bold">First Name</p>
                  <p className="font-medium text-gray-900 dark:text-gray-100">{result.first_name || 'N/A'}</p>
                </div>
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                  <p className="text-xs text-slate-400 dark:text-slate-400 font-semibold uppercase font-bold">Last Name</p>
                  <p className="font-medium text-gray-900 dark:text-gray-100">{result.last_name || 'N/A'}</p>
                </div>
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-600 dark:text-gray-300 font-medium mb-2 font-semibold">🤖 AI-Formatted Resume Profile <span className="text-xs text-violet-600">(via Groq LLM)</span></p>
              <div className="bg-slate-50 dark:bg-slate-900 p-5 rounded-lg text-sm text-gray-900 dark:text-gray-100 font-mono h-64 overflow-y-auto border border-violet-500/20 whitespace-pre-wrap leading-relaxed shadow-inner">
                {result.formatted_text || result.raw_text || 'No text extracted.'}
              </div>
            </div>

            {!careerAnalysis ? (
              <button 
                onClick={handleCareerAnalysis}
                disabled={isAnalyzing}
                className="w-full mt-4 flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-[#0066FF] to-[#0052cc] hover:from-[#0052cc] hover:to-[#0040a8] text-white rounded-xl font-bold shadow-lg transition-all disabled:opacity-50"
              >
                <Bot className="w-5 h-5"/>
                {isAnalyzing ? 'Analyzing Career Matrix...' : 'Pass to Career Agent for Analysis'}
                <ChevronRight className="w-5 h-5"/>
              </button>
            ) : (
                  <div className="w-full mt-4 flex items-center justify-between p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                 <div className="flex items-center gap-3">
                   <Briefcase className="w-6 h-6 text-[#2E9A47]" />
                   <div>
                     <p className="font-bold text-[#2E9A47]">Analysis Complete!</p>
                     <p className="text-xs text-[#2E9A47]/80 font-medium">Data saved to Career Database</p>
                   </div>
                 </div>
                 <Link to="/career" className="px-5 py-2 bg-[#2E9A47] hover:bg-emerald-700 text-white font-bold rounded-lg transition-colors shadow-lg shadow-emerald-500/20">
                   View Dashboard
                 </Link>
              </div>
            )}
          </div>
        )}
      </div>

      {/* RESUME HISTORY SECTION */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <FileText className="w-6 h-6 text-blue-400" /> Resume History
        </h2>
        <ResumeHistoryList />
      </div>
    </div>
  );
}

function ResumeHistoryList() {
  const [resumes, setResumes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    fetchResumes();
  }, []);

  const fetchResumes = async () => {
    try {
      const res = await axios.get('/api/resume/list');
      const data = Array.isArray(res.data) ? res.data : [res.data];
      setResumes(data.sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-32 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
        <div className="h-32 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
      </div>
    );
  }

  if (resumes.length === 0) {
    return (
      <div className="glass-card p-12 text-center text-slate-400 dark:text-slate-400 font-semibold rounded-xl border border-dashed border-slate-200 dark:border-slate-700">
        <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p className="font-medium">No resumes found in database.</p>
        <p className="text-sm mt-2">Upload a resume above to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {resumes.map((resume, idx) => (
        <div key={resume.id || idx} className="glass-card rounded-xl border border-slate-200 dark:border-slate-700/50 p-5 flex justify-between items-start flex-wrap gap-4 hover:border-blue-500/30 transition-colors">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <FileText className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="font-bold text-lg">{[resume.first_name, resume.last_name].filter(Boolean).join(' ') || resume.filename || 'Unknown Candidate'}</h3>
              <p className="text-gray-600 dark:text-gray-300 font-medium text-sm">{resume.email || '—'} {resume.phone ? `• ${resume.phone}` : ''}</p>
              {resume.location && <p className="text-slate-400 dark:text-slate-400 font-semibold text-xs">{resume.location}</p>}
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-400 dark:text-slate-400 font-semibold mb-2">{resume.filename}</p>
            <p className="text-xs text-slate-600">{new Date(resume.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
            <div className="flex flex-wrap gap-1 mt-2 justify-end">
              {resume.skills?.slice(0, 8).map((sk: any, i: number) => (
                <span key={i} className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-gray-900 dark:text-gray-100 font-bold rounded text-[10px]">{sk.name || sk}</span>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
