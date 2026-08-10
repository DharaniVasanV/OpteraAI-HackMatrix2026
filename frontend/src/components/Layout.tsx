import React from 'react';
import { Outlet, Navigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Home, Inbox, Briefcase, Calendar, Video, FileText, 
  Map, MonitorPlay, FileCheck, CopyPlus, Bell, 
  Activity, Component, Settings, LogOut
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  { name: 'Home', path: '/', icon: Home },
  { name: 'Inbox', path: '/inbox', icon: Inbox },
  { name: 'Opportunities', path: '/opportunities', icon: Briefcase },
  { name: 'Meetings', path: '/meetings', icon: Video },
  { name: 'Calendar', path: '/calendar', icon: Calendar },
  { name: 'Knowledge', path: '/knowledge', icon: FileText },
  { name: 'Career', path: '/career', icon: Map },
  { name: 'Learning', path: '/learning', icon: MonitorPlay },
  { name: 'Resume', path: '/resume', icon: FileCheck },
  { name: 'Applications', path: '/applications', icon: CopyPlus },
  { name: 'Notifications', path: '/notifications', icon: Bell },
  { name: 'Analytics', path: '/analytics', icon: Activity },
  { name: 'AI Agents', path: '/agents', icon: Component },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export default function Layout() {
  const { user, isLoading, logout } = useAuth();
  const location = useLocation();

  if (isLoading) return <div className="h-screen w-screen flex items-center justify-center">Loading...</div>;
  if (!user) return <Navigate to="/login" />;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-slate-900 flex flex-col h-full shrink-0">
        <div className="h-16 flex items-center px-6 border-b border-border">
          <Component className="w-6 h-6 mr-2 text-primary" />
          <span className="text-lg font-bold tracking-tight text-white">AgentOS</span>
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-3">
            {navItems.map((item) => {
              const active = location.pathname === item.path || 
                             (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <li key={item.name}>
                  <Link
                    to={item.path}
                    className={cn(
                      "flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                      active ? "bg-primary/20 text-primary" : "text-slate-400 hover:text-white hover:bg-slate-800"
                    )}
                  >
                    <item.icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      {/* Main content wrapper */}
      <div className="flex-1 flex flex-col h-full bg-slate-950 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 flex-shrink-0 flex items-center justify-between px-6 border-b border-border glass-panel z-10 w-full relative">
          <div className="flex items-center w-96">
             <div className="relative w-full">
               <input 
                 type="text" 
                 placeholder="Search or jump to... (Ctrl+K)" 
                 className="w-full bg-slate-800 border-none rounded-md px-4 py-1.5 text-sm focus:ring-1 focus:ring-primary text-slate-200"
               />
             </div>
          </div>
          <div className="flex items-center space-x-4">
             <button className="text-slate-400 hover:text-white relative">
               <Bell className="w-5 h-5" />
               <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
             </button>
             <div className="flex items-center space-x-2 pl-4 border-l border-border">
                <div className="text-right hidden md:block">
                   <p className="text-sm font-medium text-white">{user.name}</p>
                </div>
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                   {user.name.charAt(0)}
                </div>
                <button onClick={logout} className="ml-2 text-slate-400 hover:text-white">
                  <LogOut className="w-4 h-4" />
                </button>
             </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto p-6 scroll-smooth">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
