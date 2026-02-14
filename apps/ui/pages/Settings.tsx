
import React from 'react';
import { 
  Globe, 
  Database, 
  Bell, 
  Palette, 
  Link as LinkIcon,
  Save,
  RotateCcw,
  ExternalLink
} from 'lucide-react';
import { useStore } from '../store';

const Settings: React.FC = () => {
  const { theme, toggleTheme } = useStore();

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Platform Settings</h2>
          <p className="text-slate-500 text-sm">Configure global environment variables and UI preferences</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-6 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-sm font-bold hover:bg-slate-50 transition-colors">
            <RotateCcw size={18} /> Reset
          </button>
          <button className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-bold shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all">
            <Save size={18} /> Save Changes
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1">
          <nav className="space-y-1">
            {[
              { label: 'General Info', icon: <Globe size={18} />, active: true },
              { label: 'Data Endpoints', icon: <Database size={18} /> },
              { label: 'Notifications', icon: <Bell size={18} /> },
              { label: 'Branding', icon: <Palette size={18} /> },
              { label: 'Integrations', icon: <LinkIcon size={18} /> },
            ].map((item, i) => (
              <button 
                key={i}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                  item.active ? 'bg-white dark:bg-slate-800 text-blue-600 shadow-sm' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`}
              >
                {item.icon} {item.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="md:col-span-2 space-y-6">
          <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-8">
            <section className="space-y-4">
              <h3 className="font-bold text-lg">System Endpoints</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-2">Nexus API Gateway</label>
                  <input type="text" defaultValue="https://api.nexus-platform.io/v1" className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm font-mono" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-2">Superset Dashboard URL</label>
                  <input type="text" defaultValue="https://superset.nexus-platform.io" className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm font-mono" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-2">Elasticsearch Host</label>
                  <input type="text" defaultValue="https://es-internal:9200" className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm font-mono" />
                </div>
              </div>
            </section>

            <section className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-lg">Display Preferences</h3>
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-950 rounded-xl">
                 <div className="flex items-center gap-3">
                   <Palette size={20} className="text-blue-600" />
                   <div>
                     <p className="text-sm font-bold">Dark Mode</p>
                     <p className="text-xs text-slate-500">Enable high-contrast dark theme</p>
                   </div>
                 </div>
                 <button 
                  onClick={toggleTheme}
                  className={`w-12 h-6 rounded-full transition-colors relative ${theme === 'dark' ? 'bg-blue-600' : 'bg-slate-300'}`}
                 >
                   <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${theme === 'dark' ? 'left-7' : 'left-1'}`} />
                 </button>
              </div>
            </section>

            <section className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-800">
               <h3 className="font-bold text-lg">External Tools</h3>
               <div className="grid grid-cols-2 gap-4">
                 <a href="#" className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-950 rounded-xl hover:bg-slate-100 transition-colors">
                   <span className="text-sm font-bold">Grafana Admin</span>
                   <ExternalLink size={16} className="text-slate-400" />
                 </a>
                 <a href="#" className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-950 rounded-xl hover:bg-slate-100 transition-colors">
                   <span className="text-sm font-bold">Kibana Logs</span>
                   <ExternalLink size={16} className="text-slate-400" />
                 </a>
               </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
