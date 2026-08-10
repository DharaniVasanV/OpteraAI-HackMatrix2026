import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Component } from 'lucide-react';

export default function AuthLayout() {
  const { user, isLoading } = useAuth();
  
  if (isLoading) return <div className="h-screen w-screen flex items-center justify-center">Loading...</div>;
  if (user) return <Navigate to="/" />;

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-slate-950">
      <div className="hidden lg:flex flex-col justify-between p-12 bg-slate-900 border-r border-border">
        <div>
          <div className="flex items-center space-x-3 mb-8">
            <Component className="w-8 h-8 text-primary" />
            <h1 className="text-2xl font-bold text-white">AgentOS</h1>
          </div>
          <h2 className="text-4xl font-bold text-white leading-tight mt-12">
            The World's First <br/> Autonomous AI <br/> Productivity System
          </h2>
          <p className="mt-6 text-lg text-slate-400 max-w-md">
            Unify all 14 of your AI agents into a single, cohesive command center. Stop jumping between tabs and start automating your life.
          </p>
        </div>
        <div className="text-sm text-slate-500">
          Built securely with FastAPI & React.
        </div>
      </div>
      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-8 glass-panel p-8 rounded-xl">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
