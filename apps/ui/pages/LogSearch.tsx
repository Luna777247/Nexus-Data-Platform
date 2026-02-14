
import React, { useState } from 'react';
import { 
  Search, 
  Terminal, 
  Clock, 
  AlertCircle, 
  Info, 
  Download,
  Calendar,
  Filter
} from 'lucide-react';

const LogSearch: React.FC = () => {
  const [levelFilter, setLevelFilter] = useState('ALL');

  const logs = [
    { id: 1, ts: '2024-03-20 14:05:22', level: 'ERROR', service: 'spark-executor-1', msg: 'OutOfMemoryError: Java heap space' },
    { id: 2, ts: '2024-03-20 14:05:15', level: 'INFO', service: 'api-gateway', msg: 'User login success: admin_nexus' },
    { id: 3, ts: '2024-03-20 14:04:58', level: 'WARN', service: 'kafka-broker-2', msg: 'Leader balance in progress' },
    { id: 4, ts: '2024-03-20 14:04:30', level: 'DEBUG', service: 'ingestion-worker', msg: 'Heartbeat received' },
    { id: 5, ts: '2024-03-20 14:03:10', level: 'INFO', service: 'clickhouse-node', msg: 'Partition rotation completed' },
  ].filter(l => levelFilter === 'ALL' || l.level === levelFilter);

  const getLevelStyles = (level: string) => {
    switch(level) {
      case 'ERROR': return 'bg-red-50 text-red-700 border-red-100';
      case 'WARN': return 'bg-amber-50 text-amber-700 border-amber-100';
      case 'DEBUG': return 'bg-slate-50 text-slate-700 border-slate-100';
      default: return 'bg-blue-50 text-blue-700 border-blue-100';
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input 
              type="text" 
              placeholder="Query logs (KQL: message:'error' AND service:'spark*')..." 
              className="w-full pl-12 pr-4 py-3.5 bg-slate-50 dark:bg-slate-950 border-none rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
            />
          </div>
          <button className="bg-blue-600 text-white px-8 py-3.5 rounded-2xl font-bold shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all">
            Search Elasticsearch
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
             {['ALL', 'ERROR', 'WARN', 'INFO', 'DEBUG'].map(lvl => (
               <button 
                 key={lvl}
                 onClick={() => setLevelFilter(lvl)}
                 className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${levelFilter === lvl ? 'bg-white dark:bg-slate-700 text-blue-600 shadow-sm' : 'text-slate-500'}`}
               >
                 {lvl}
               </button>
             ))}
          </div>
          <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 mx-2"></div>
          <button className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 px-3 py-1.5 rounded-lg transition-colors">
            <Calendar size={16} /> Last 15 minutes
          </button>
          <button className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 px-3 py-1.5 rounded-lg transition-colors">
            <Filter size={16} /> Filter by Service
          </button>
          <button className="ml-auto flex items-center gap-2 text-sm font-bold text-blue-600 hover:underline">
            <Download size={16} /> Download CSV
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
            <Terminal size={18} />
            <span className="text-sm font-bold">Log Stream</span>
          </div>
          <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold animate-pulse">Live</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-[13px]">
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {logs.map(log => (
                <tr key={log.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                  <td className="px-6 py-3 whitespace-nowrap text-slate-400 flex items-center gap-2">
                    <Clock size={14} /> {log.ts}
                  </td>
                  <td className="px-6 py-3">
                    <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getLevelStyles(log.level)}`}>
                      {log.level}
                    </span>
                  </td>
                  <td className="px-6 py-3 font-bold text-blue-600 dark:text-blue-400 whitespace-nowrap">
                    {log.service}
                  </td>
                  <td className="px-6 py-3 text-slate-700 dark:text-slate-300 w-full">
                    {log.msg}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LogSearch;
