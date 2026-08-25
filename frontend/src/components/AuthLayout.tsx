import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AuthLayout() {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div className="h-screen w-screen flex items-center justify-center">Loading...</div>;
  if (user) return <Navigate to="/" />;

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-slate-50 dark:bg-slate-900 font-sans">
      <div className="hidden lg:flex flex-col justify-between p-12 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">
        {/* Soft abstract shapes in background */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#0066FF] rounded-full blur-[100px] opacity-10 -mr-20 -mt-20"></div>
        <div className="absolute bottom-10 left-10 w-64 h-64 bg-[#2E9A47] rounded-full blur-[100px] opacity-[0.08]"></div>

        <div className="relative z-10">
          <div className="flex items-center space-x-3 mb-8">
            <img src="/logo.png" alt="OpteraAI Logo" className="w-11 h-11 object-contain" />
            <span className="text-2xl font-extrabold tracking-tight text-gray-900 dark:text-gray-100">Optera<span className="text-[#0066FF]">AI</span></span>
          </div>
          <h2 className="text-5xl font-extrabold text-gray-900 dark:text-gray-100 leading-tight mt-16 tracking-tight">
            The World's First <br /> <span className="text-[#0066FF]">Autonomous AI</span> <br /> Productivity System
          </h2>
          <p className="mt-6 text-xl text-gray-600 dark:text-gray-300 max-w-md font-medium leading-relaxed">
            Unify all 15 of your AI agents into a single, cohesive command center. Stop jumping between tabs and start automating your life.
          </p>
        </div>
        <div className="text-sm font-semibold text-slate-400 dark:text-slate-400 relative z-10">
          Built securely with FastAPI & React.
        </div>
      </div>
      <div className="flex items-center justify-center p-8 bg-slate-50 dark:bg-slate-900">
        <div className="w-full max-w-md space-y-8 glass-card p-10 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
