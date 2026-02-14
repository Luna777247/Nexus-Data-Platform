
import React, { useState } from 'react';
import { 
  Play, 
  Save, 
  History, 
  BarChart, 
  ExternalLink,
  Code,
  Table as TableIcon,
  Maximize2
} from 'lucide-react';

const Analytics: React.FC = () => {
  const [query, setQuery] = useState('SELECT \n  date_trunc(\'day\', timestamp) as day,\n  count(*) as event_count\nFROM nexus_gold.tourism_events\nGROUP BY day\nORDER BY day DESC\nLIMIT 10;');

  return (
    <div className="flex flex-col h-full gap-8">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 h-full">
        {/* SQL Editor Simulation */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Code size={18} className="text-blue-600" />
              <span className="font-bold">ClickHouse SQL Editor</span>
            </div>
            <div className="flex gap-2">
              <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500">
                <History size={18} />
              </button>
              <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500">
                <Save size={18} />
              </button>
              <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-xl text-sm font-bold shadow-lg shadow-blue-200 transition-all active:scale-95">
                <Play size={16} fill="white" /> Run
              </button>
            </div>
          </div>
          <div className="flex-1 p-0">
            <textarea 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full h-full p-6 font-mono text-sm bg-slate-50 dark:bg-slate-950 border-none resize-none focus:ring-0 outline-none text-blue-900 dark:text-blue-300"
              spellCheck={false}
            />
          </div>
        </div>

        {/* Results / Visualizer */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-4">
               <button className="flex items-center gap-2 text-sm font-bold text-blue-600 border-b-2 border-blue-600 px-2 py-1">
                 <TableIcon size={16} /> Data View
               </button>
               <button className="flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-700 px-2 py-1 transition-colors">
                 <BarChart size={16} /> Chart View
               </button>
            </div>
            <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500">
               <Maximize2 size={18} />
            </button>
          </div>
          <div className="flex-1 p-6 overflow-auto">
             <table className="w-full text-left border-collapse">
               <thead>
                 <tr className="border-b border-slate-100 dark:border-slate-800">
                   <th className="py-3 px-4 text-xs font-bold text-slate-400 uppercase">Day</th>
                   <th className="py-3 px-4 text-xs font-bold text-slate-400 uppercase text-right">Event Count</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-slate-50 dark:divide-slate-800/50">
                 {[...Array(8)].map((_, i) => (
                   <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                     <td className="py-3 px-4 text-sm font-medium">2024-03-{20-i}</td>
                     <td className="py-3 px-4 text-sm font-mono text-right text-blue-600">{(Math.random() * 50000 + 10000).toFixed(0)}</td>
                   </tr>
                 ))}
               </tbody>
             </table>
          </div>
        </div>
      </div>

      {/* Embedded Superset Simulation */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col min-h-[500px]">
        <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/30">
          <div>
            <h3 className="text-lg font-bold">Integrated Superset Dashboard</h3>
            <p className="text-sm text-slate-500">Tourism Insight Dashboard • Read-only</p>
          </div>
          <button className="flex items-center gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-4 py-2 rounded-xl text-sm font-semibold hover:bg-slate-50 transition-colors">
            Open in Superset <ExternalLink size={16} />
          </button>
        </div>
        <div className="flex-1 bg-slate-100 dark:bg-slate-800 flex items-center justify-center p-8">
           <div className="text-center max-w-md">
             <div className="w-20 h-20 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
               <BarChart size={40} />
             </div>
             <h4 className="text-xl font-bold mb-2">Iframe Embedding</h4>
             <p className="text-slate-500 mb-6">This area would typically render a Superset dashboard iframe. Role-based access tokens are automatically passed via Nexus Gateway.</p>
             <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
               <div className="w-2/3 h-full bg-blue-600 rounded-full animate-pulse"></div>
             </div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
