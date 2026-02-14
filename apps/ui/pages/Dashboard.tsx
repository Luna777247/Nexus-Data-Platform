
import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend, Cell
} from 'recharts';
import { 
  ArrowUpRight, 
  ArrowDownRight, 
  Activity, 
  Database, 
  AlertTriangle, 
  CheckCircle2,
  Clock,
  Zap
} from 'lucide-react';

const stats = [
  { label: 'Total Events', value: '1.2M', change: '+12.5%', isPositive: true, icon: <Zap size={24} className="text-blue-600" /> },
  { label: 'Active Pipelines', value: '42', change: 'Stable', isPositive: true, icon: <Activity size={24} className="text-emerald-600" /> },
  { label: 'Processing Errors', value: '12', change: '-5.2%', isPositive: true, icon: <AlertTriangle size={24} className="text-amber-600" /> },
  { label: 'System Health', value: '99.9%', change: '+0.1%', isPositive: true, icon: <CheckCircle2 size={24} className="text-indigo-600" /> },
];

const chartData = [
  { name: '00:00', events: 4000, errors: 240 },
  { name: '04:00', events: 3000, errors: 198 },
  { name: '08:00', events: 2000, errors: 980 },
  { name: '12:00', events: 2780, errors: 390 },
  { name: '16:00', events: 1890, errors: 480 },
  { name: '20:00', events: 2390, errors: 380 },
  { name: '23:59', events: 3490, errors: 430 },
];

const pipelineData = [
  { id: 'p-1', name: 'Raw Ingestion', status: 'Running', health: 98, lastRun: '2 mins ago' },
  { id: 'p-2', name: 'Cleaning Task', status: 'Idle', health: 100, lastRun: '1 hour ago' },
  { id: 'p-3', name: 'Gold Aggregation', status: 'Error', health: 45, lastRun: '15 mins ago' },
  { id: 'p-4', name: 'ML Features', status: 'Running', health: 92, lastRun: 'Just now' },
];

const Dashboard: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm transition-transform hover:scale-[1.02]">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">{stat.icon}</div>
              <div className={`flex items-center text-xs font-medium px-2 py-1 rounded-full ${
                stat.isPositive ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
              }`}>
                {stat.isPositive ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowDownRight size={14} className="mr-1" />}
                {stat.change}
              </div>
            </div>
            <p className="text-slate-500 text-sm font-medium">{stat.label}</p>
            <h3 className="text-2xl font-bold mt-1">{stat.value}</h3>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-lg font-bold">Event Throughput</h3>
            <select className="bg-slate-50 border-none rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500">
              <option>Last 24 Hours</option>
              <option>Last 7 Days</option>
            </select>
          </div>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fontSize: 12}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fontSize: 12}} />
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                />
                <Area type="monotone" dataKey="events" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorEvents)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col">
          <h3 className="text-lg font-bold mb-6">Pipeline Health</h3>
          <div className="space-y-6 flex-1">
            {pipelineData.map(p => (
              <div key={p.id} className="flex items-center gap-4">
                <div className={`w-3 h-3 rounded-full ${
                  p.status === 'Running' ? 'bg-blue-500 animate-pulse' : 
                  p.status === 'Error' ? 'bg-red-500' : 'bg-slate-300'
                }`} />
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-sm">{p.name}</span>
                    <span className="text-xs text-slate-500">{p.health}%</span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${p.health > 80 ? 'bg-emerald-500' : p.health > 50 ? 'bg-amber-500' : 'bg-red-500'}`} 
                      style={{ width: `${p.health}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
          <button className="mt-8 text-blue-600 text-sm font-semibold hover:underline flex items-center justify-center gap-2">
            View All Pipelines <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-8 py-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <h3 className="text-lg font-bold">Service Status</h3>
          <button className="text-sm bg-blue-50 text-blue-600 px-4 py-1.5 rounded-lg font-medium hover:bg-blue-100 transition-colors">
            Refresh Status
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 divide-x divide-y md:divide-y-0 border-slate-100 dark:border-slate-800">
           {['Kafka Cluster', 'Spark Master', 'MinIO Storage', 'Superset API'].map((service, i) => (
             <div key={i} className="p-8 flex items-center gap-4">
                <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center">
                  <CheckCircle2 size={24} />
                </div>
                <div>
                  <p className="font-bold">{service}</p>
                  <p className="text-xs text-slate-500">Operational • 100% Uptime</p>
                </div>
             </div>
           ))}
        </div>
      </div>
    </div>
  );
};

const ChevronRight = ({ size }: { size: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m9 18 6-6-6-6"/>
  </svg>
);

export default Dashboard;
