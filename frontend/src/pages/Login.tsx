import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { LogIn } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const errParam = params.get('error');
    const detailParam = params.get('detail');
    if (errParam) {
      setError(`Google OAuth Error: ${detailParam || errParam}`);
      return;
    }

    if (params.get('google_login') === 'true') {
      const emailParam = params.get('email') || '';
      const nameParam = params.get('name') || '';
      
      if (emailParam) {
        axios.post('/auth/google', {
          email: emailParam,
          name: nameParam,
          google_id: emailParam, 
          picture: ''
        }).then(res => {
          login(res.data.access_token, res.data.user);
        }).catch(err => {
          setError('Google auto-login failed: ' + (err.response?.data?.detail || err.message));
        });
      }
    }
  }, [login]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      const res = await axios.post('/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      login(res.data.access_token, res.data.user);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <>
      <div className="text-center">
        <h2 className="text-3xl font-extrabold text-gray-900 dark:text-gray-100 mb-2 tracking-tight">Welcome Back</h2>
        <p className="text-gray-600 dark:text-gray-300 text-sm font-medium">Sign in to access your OpteraAI dashboard</p>
      </div>

      {error && <div className="bg-[#C5192D]/10 border border-[#C5192D]/20 text-[#C5192D] text-sm font-semibold p-4 rounded-xl shadow-sm">{error}</div>}

      <a 
        href="http://localhost:9000/gmail/oauth"
        className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm text-gray-900 dark:text-gray-100 hover:bg-slate-50 dark:bg-slate-900 hover:shadow-md font-bold py-3 px-4 rounded-xl flex justify-center items-center transition-all mb-8 mt-4"
      >
        <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
        </svg>
        Continue with Google
      </a>

      <div className="relative mb-8">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-200 dark:border-slate-700"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-white dark:bg-slate-800 text-slate-400 dark:text-slate-400 font-bold">Or continue with email</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-bold text-gray-600 dark:text-gray-300 mb-1.5 ml-1">Email</label>
          <input 
            type="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-[#0066FF]/20 focus:border-[#0066FF]/50 focus:bg-white dark:bg-slate-800 outline-none transition-all shadow-inner font-medium text-base"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-bold text-gray-600 dark:text-gray-300 mb-1.5 ml-1">Password</label>
          <input 
            type="password" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-[#0066FF]/20 focus:border-[#0066FF]/50 focus:bg-white dark:bg-slate-800 outline-none transition-all shadow-inner font-medium text-base"
            required
          />
        </div>
        
        <button 
          type="submit"
          className="w-full btn-primary-custom py-3.5 px-4 rounded-xl flex justify-center items-center transition-all mt-2 text-base font-extrabold shadow-lg"
        >
          <LogIn className="w-5 h-5 mr-3" />
          Sign In
        </button>
      </form>

      <div className="text-center mt-8">
        <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
          Don't have an account? <Link to="/signup" className="text-[#0066FF] font-bold hover:underline">Create one</Link>
        </p>
      </div>
    </>
  );
}
