import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Bell, AlertTriangle, Info, CheckCircle, Clock } from 'lucide-react';

export default function Notifications() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const res = await axios.get('/api/notifications');
      setNotifications(res.data);
    } catch (err) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority?.toUpperCase()) {
      case 'HIGH': return 'border-rose-500 bg-rose-500/10 text-rose-400';
      case 'MEDIUM': return 'border-amber-500 bg-amber-500/10 text-amber-400';
      case 'LOW': return 'border-green-500 bg-green-500/10 text-green-400';
      default: return 'border-slate-500 bg-slate-500/10 text-slate-400';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority?.toUpperCase()) {
      case 'HIGH': return <AlertTriangle className="w-5 h-5 text-rose-400" />;
      case 'MEDIUM': return <Info className="w-5 h-5 text-amber-400" />;
      case 'LOW': return <CheckCircle className="w-5 h-5 text-green-400" />;
      default: return <Bell className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="p-8 text-white max-w-5xl mx-auto h-full overflow-y-auto">
      <div className="flex items-center gap-3 mb-2">
        <Bell className="w-10 h-10 text-amber-400" />
        <h1 className="text-4xl font-extrabold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
          Notification Center
        </h1>
      </div>
      <p className="text-slate-400 mb-8">System alerts and history managed by Notification Agent.</p>
      
      <div className="space-y-4">
        {loading ? (
          <div className="animate-pulse space-y-4">
             <div className="h-20 bg-slate-800 rounded-xl"></div>
             <div className="h-20 bg-slate-800 rounded-xl"></div>
             <div className="h-20 bg-slate-800 rounded-xl"></div>
          </div>
        ) : notifications.length > 0 ? (
          notifications.map((notif: any, i: number) => (
            <div key={notif.notification_id || i} className={`glass-panel p-5 rounded-xl border-l-4 flex gap-4 ${getPriorityColor(notif.priority)} transition-all hover:bg-opacity-20`}>
               <div className="mt-1">
                 {getPriorityIcon(notif.priority)}
               </div>
               <div className="flex-1">
                 <div className="flex justify-between items-start mb-1">
                   <h4 className="font-bold text-lg text-white">{notif.title || 'System Alert'}</h4>
                   <div className="flex items-center gap-1 text-xs text-slate-400">
                     <Clock className="w-3 h-3" />
                     {new Date(notif.created_at).toLocaleString()}
                   </div>
                 </div>
                 <p className="text-slate-300 text-sm">{notif.description}</p>
                 
                 <div className="mt-3 flex items-center justify-between">
                   <span className="text-xs uppercase font-bold tracking-wider opacity-80 bg-black/20 px-2 py-1 rounded">
                     {notif.priority || 'NORMAL'} PRIORITY
                   </span>
                   <span className="text-xs text-slate-400">
                     Source: {notif.source_agent || 'System'}
                   </span>
                 </div>
               </div>
            </div>
          ))
        ) : (
          <div className="glass-panel p-12 text-center text-slate-500 rounded-xl border border-dashed border-slate-700">
            <Bell className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No notifications found in history.</p>
          </div>
        )}
      </div>
    </div>
  );
}
