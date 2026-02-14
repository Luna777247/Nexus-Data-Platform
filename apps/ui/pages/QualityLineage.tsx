
import React from 'react';
import { 
  ShieldCheck, 
  GitBranch, 
  CheckCircle, 
  AlertCircle, 
  ArrowRight,
  Database,
  Search,
  Maximize2
} from 'lucide-react';

const QualityLineage: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Quality Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex justify-between items-center mb-4">
             <h4 className="text-sm font-bold text-slate-500">Quality Pass Rate</h4>
             <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center">
               <ShieldCheck size={20} />
             </div>
          </div>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold">98.2%</span>
            <span className="text-emerald-600 text-sm font-bold mb-1">+0.5%</span>
          </div>
          <div className="mt-4 h-1.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
             <div className="h-full bg-emerald-500 w-[98.2%]"></div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex justify-between items-center mb-4">
             <h4 className="text-sm font-bold text-slate-500">Failed Checks</h4>
             <div className="w-10 h-10 bg-red-50 text-red-600 rounded-full flex items-center justify-center">
               <AlertCircle size={20} />
             </div>
          </div>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold">4</span>
            <span className="text-red-600 text-sm font-bold mb-1">-2</span>
          </div>
          <p className="mt-2 text-xs text-slate-500">Active incidents in Gold layer</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex justify-between items-center mb-4">
             <h4 className="text-sm font-bold text-slate-500">Total Validated Rows</h4>
             <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center">
               <CheckCircle size={20} />
             </div>
          </div>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold">2.5M</span>
            <span className="text-blue-600 text-sm font-bold mb-1">Today</span>
          </div>
          <p className="mt-2 text-xs text-slate-500">Completeness check 100%</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Quality Checks Table */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
             <h3 className="text-lg font-bold">Recent Quality Checks</h3>
             <button className="text-blue-600 text-sm font-bold hover:underline">View All</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/50">
                  <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Dataset</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Metric</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 dark:divide-slate-800">
                 {[
                   { name: 'gold.tourism_stats', metric: 'Completeness', status: 'Passed' },
                   { name: 'silver.user_activity', metric: 'Uniqueness', status: 'Passed' },
                   { name: 'bronze.raw_iot', metric: 'Schema Drift', status: 'Failed' },
                   { name: 'gold.daily_reports', metric: 'Freshness', status: 'Passed' },
                 ].map((check, i) => (
                   <tr key={i}>
                     <td className="px-6 py-4 font-bold text-sm">{check.name}</td>
                     <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{check.metric}</td>
                     <td className="px-6 py-4">
                       <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase ${
                         check.status === 'Passed' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                       }`}>
                         {check.status}
                       </span>
                     </td>
                   </tr>
                 ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Data Lineage Visualization Simulation */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col">
          <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
             <div className="flex items-center gap-2">
               <GitBranch size={20} className="text-blue-600" />
               <h3 className="text-lg font-bold">Data Lineage</h3>
             </div>
             <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400">
                <Maximize2 size={18} />
             </button>
          </div>
          <div className="flex-1 bg-slate-50 dark:bg-slate-950 p-8 flex items-center justify-center relative min-h-[400px]">
             {/* Schematic Lineage Map */}
             <div className="flex items-center gap-12">
                <LineageNode icon={<Database />} label="Kafka Source" type="source" />
                <ArrowRight className="text-slate-300" />
                <LineageNode icon={<ShieldCheck />} label="Bronze Layer" type="processing" />
                <ArrowRight className="text-slate-300" />
                <div className="flex flex-col gap-8">
                   <LineageNode icon={<CheckCircle />} label="Silver Clean" type="processing" />
                   <LineageNode icon={<AlertCircle />} label="Gold Aggs" type="sink" isWarning />
                </div>
             </div>
             <div className="absolute bottom-4 left-6 text-[10px] text-slate-400 uppercase font-bold tracking-widest">
               powered by OpenMetadata
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const LineageNode = ({ icon, label, type, isWarning }: { icon: any, label: string, type: string, isWarning?: boolean }) => (
  <div className={`p-4 rounded-xl border-2 flex flex-col items-center gap-2 w-32 shadow-sm bg-white dark:bg-slate-900 transition-all hover:scale-105 ${
    isWarning ? 'border-amber-400 ring-4 ring-amber-400/20' : 'border-blue-100 dark:border-slate-800'
  }`}>
    <div className={`p-2 rounded-lg ${isWarning ? 'bg-amber-100 text-amber-600' : 'bg-blue-50 dark:bg-blue-900/30 text-blue-600'}`}>
      {React.cloneElement(icon, { size: 20 })}
    </div>
    <span className="text-xs font-bold text-center leading-tight">{label}</span>
  </div>
);

export default QualityLineage;
