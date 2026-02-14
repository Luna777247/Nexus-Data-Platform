
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useStore } from '../store';
import { UserRole } from '../types';
import { Lock, Mail, Github, Loader2, Sparkles } from 'lucide-react';

const Login: React.FC = () => {
  const [username, setUsername] = useState('admin_nexus');
  const [password, setPassword] = useState('password');
  const [loading, setLoading] = useState(false);
  const { setAuthenticated } = useStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
      setAuthenticated({
        id: '1',
        username: 'Admin User',
        email: 'admin@nexus.io',
        role: UserRole.ADMIN
      });
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-[2.5rem] shadow-2xl shadow-slate-200 dark:shadow-none border border-slate-100 dark:border-slate-800 overflow-hidden">
        <div className="p-10">
          <div className="flex flex-col items-center text-center mb-10">
            <div className="w-16 h-16 bg-blue-600 rounded-3xl flex items-center justify-center text-white text-3xl font-black shadow-xl shadow-blue-200 mb-6 animate-bounce-slow">
              N
            </div>
            <h1 className="text-3xl font-black tracking-tight mb-2">Nexus Data Platform</h1>
            <p className="text-slate-500 font-medium">Enterprise Data Fabric Orchestrator</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-4">
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors" size={20} />
                <input 
                  type="text" 
                  placeholder="Username or Email" 
                  className="w-full pl-12 pr-4 py-4 bg-slate-50 dark:bg-slate-950 border-none rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none transition-all font-medium"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors" size={20} />
                <input 
                  type="password" 
                  placeholder="Password" 
                  className="w-full pl-12 pr-4 py-4 bg-slate-50 dark:bg-slate-950 border-none rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none transition-all font-medium"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-sm font-bold">
              <label className="flex items-center gap-2 cursor-pointer text-slate-500">
                <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                Remember me
              </label>
              <a href="#" className="text-blue-600 hover:underline">Forgot password?</a>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-2xl font-bold shadow-xl shadow-blue-200 dark:shadow-none transition-all flex items-center justify-center gap-2 disabled:opacity-70 active:scale-95"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={20} /> Authenticating...
                </>
              ) : (
                'Sign In to Platform'
              )}
            </button>
          </form>

          <div className="relative my-10">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-100 dark:border-slate-800"></div></div>
            <div className="relative flex justify-center text-xs font-bold uppercase"><span className="bg-white dark:bg-slate-900 px-4 text-slate-400">Or continue with SSO</span></div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <button className="flex items-center justify-center gap-2 py-3 px-4 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors font-bold text-sm">
              <Github size={18} /> GitHub
            </button>
            <button className="flex items-center justify-center gap-2 py-3 px-4 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors font-bold text-sm">
              <Sparkles size={18} className="text-amber-500" /> Google
            </button>
          </div>
        </div>
        
        <div className="bg-slate-50 dark:bg-slate-800/30 p-6 text-center border-t border-slate-100 dark:border-slate-800">
          <p className="text-sm text-slate-500 font-medium">New to Nexus? <a href="#" className="text-blue-600 font-bold hover:underline">Contact Administrator</a></p>
        </div>
      </div>
      
      <p className="mt-8 text-slate-400 text-xs font-bold uppercase tracking-widest">
        &copy; 2024 Nexus Data Systems. Version 4.2.0-stable
      </p>
    </div>
  );
};

export default Login;
