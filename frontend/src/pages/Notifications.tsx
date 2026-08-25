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

  const getPriorityColor = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'warning': return 'border-rose-500 bg-rose-50 dark:bg-rose-900/20 text-rose-600';
      case 'info': return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600';
      case 'success': return 'border-emerald-500 bg-emerald-50 text-emerald-600';
      default: return 'border-slate-500 bg-slate-50 dark:bg-slate-900 text-gray-600 dark:text-gray-300 font-medium';
    }
  };

  const getPriorityIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'warning': return <AlertTriangle className="w-6 h-6 text-rose-600" />;
      case 'info': return <Info className="w-6 h-6 text-blue-600" />;
      case 'success': return <CheckCircle className="w-6 h-6 text-emerald-600" />;
      default: return <Bell className="w-6 h-6 text-gray-600 dark:text-gray-300 font-medium" />;
    }
  };

  return (
    <div className="p-8 text-gray-900 dark:text-gray-100 max-w-5xl mx-auto h-full overflow-y-auto">
      <div className="flex items-center gap-3 mb-2">
        <Bell className="w-10 h-10 text-amber-400" />
        <h1 className="text-4xl font-extrabold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
          Notification Center
        </h1>
      </div>
      <p className="text-gray-600 dark:text-gray-300 font-medium mb-8">System alerts and history managed by Notification Agent.</p>
      
      <div className="space-y-4">
        {loading ? (
          <div className="animate-pulse space-y-4">
             <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
             <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
             <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
          </div>
        ) : notifications.length > 0 ? (
          notifications.map((notif: any, i: number) => (
            <div key={notif.id || i} className={`glass-card p-5 rounded-xl border-l-4 flex gap-4 ${getPriorityColor(notif.type)} transition-all hover:bg-opacity-80 shadow-sm`}>
               <div className="mt-1 bg-white dark:bg-slate-800 p-2 rounded-full shadow-sm">
                 {getPriorityIcon(notif.type)}
               </div>
               <div className="flex-1">
                 <div className="flex justify-between items-start mb-1">
                   <h4 className="font-extrabold text-lg text-gray-900 dark:text-gray-100 tracking-wide">{notif.title || 'System Alert'}</h4>
                   <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-300 font-bold">
                     <Clock className="w-3 h-3" />
                     {notif.time || new Date().toLocaleTimeString()}
                   </div>
                 </div>
                 <p className="text-gray-900 dark:text-gray-100 font-bold text-sm leading-relaxed">{notif.message}</p>
                 
                 <div className="mt-3 flex items-center justify-between border-t border-black/5 pt-3">
                   <span className="text-[10px] uppercase font-extrabold tracking-wider bg-black/5 px-3 py-1 rounded-full">
                     {notif.type || 'NORMAL'} ALERT
                   </span>
                   <span className="text-xs text-gray-600 dark:text-gray-300 font-bold">
                     Source: Watcher Agent
                   </span>
                 </div>
               </div>
            </div>
          ))
        ) : (
          <div className="glass-card p-12 text-center text-slate-400 dark:text-slate-400 font-semibold rounded-xl border border-dashed border-slate-200 dark:border-slate-700">
            <Bell className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No notifications found in history.</p>
          </div>
        )}
      </div>
    </div>
  );
}
