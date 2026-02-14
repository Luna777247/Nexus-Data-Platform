import React from 'react';
import { 
  Activity, 
  Cpu, 
  MemoryStick as Memory, 
  HardDrive, 
  BarChart2,
  ExternalLink,
  ShieldAlert,
  Clock
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const chartData = [
  { time: '10:00', cpu: 25, mem: 45 },
  { time: '10:10', cpu: 30, mem: 48 },
  { time: '10:20', cpu: 85, mem: 60 },
  { time: '10:30', cpu: 45, mem: 55 },
  { time: '10:40', cpu: 40, mem: 52 },
  { time: '10:50', cpu: 35, mem: 50 },
];

const Monitoring: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { icon: <Cpu />, label: 'CPU Usage', value: '42%', color: 'text-blue-600', bg: 'bg-blue-50' },
          { icon: <Memory />, label: 'RAM Usage', value: '8.2 GB', color: 'text-purple-600', bg: 'bg-purple-50' },
          { icon: <HardDrive />, label: 'Disk IOPS', value: '1.2k', color: 'text-emerald-600', bg: 'bg-emerald-50' },
          { icon: <Activity />, label: 'Kafka Lag', value: '12 ms', color: 'text-amber-600', bg: 'bg-amber-50' },
        ].map((m, i) => (
          <div key={i} className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
             <div className="flex items-center gap-3 mb-2">
               <div className={`p-2 rounded-lg ${m.bg} ${m.color}`}>
                 {/* Fixed: Use React.ReactElement<any> to allow 'size' property in cloneElement */}
                 {React.cloneElement(m.icon as React.ReactElement<any>, { size: 18 })}
               </div>
               <span className="text-sm font-bold text-slate-500">{m.label}</span>
             </div>
             <div className="text-2xl font-bold">{m.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         <div className="lg:col-span-2 space-y-8">
            {/* Main Infrastructure Chart */}
            <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="flex items-center justify-between mb-8">
                <h3 className="text-lg font-bold">Resource Utilization (Prometheus)</h3>
                <div className="flex gap-2">
                  <span className="flex items-center gap-1.5 text-xs font-bold text-blue-600"><div className="w-2 h-2 rounded-full bg-blue-600" /> CPU</span>
                  <span className="flex items-center gap-1.5 text-xs font-bold text-purple-600"><div className="w-2 h-2 rounded-full bg-purple-600" /> Memory</span>
                </div>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{fontSize: 10}} />
                    <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10}} />
                    <Tooltip />
                    <Area type="monotone" dataKey="cpu" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} strokeWidth={2} />
                    <Area type="monotone" dataKey="mem" stroke="#a855f7" fill="#a855f7" fillOpacity={0.1} strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Grafana Integration Section */}
            <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm min-h-[400px] flex flex-col">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-lg font-bold">Integrated Grafana Dashboard</h3>
                  <p className="text-sm text-slate-500">Real-time JVM & Node Metrics</p>
                </div>
                <button className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded-xl text-sm font-bold hover:bg-slate-200 transition-colors">
                  Open Grafana <ExternalLink size={16} />
                </button>
              </div>
              <div className="flex-1 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-center">
                 <div className="text-center p-8">
                   <div className="w-16 h-16 bg-amber-500/10 text-amber-500 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-amber-500/30">
                     <BarChart2 size={32} />
                   </div>
                   <h4 className="text-slate-100 font-bold">Active Grafana Session</h4>
                   <p className="text-slate-500 text-sm mt-2">Iframe-based visualization connected to 10.0.1.42:3000</p>
                 </div>
              </div>
            </div>
         </div>

         {/* Alerts Sidebar */}
         <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold">Critical Alerts</h3>
              <span className="text-xs font-bold px-2 py-0.5 bg-red-100 text-red-600 rounded">2 Active</span>
            </div>
            <div className="space-y-4 flex-1">
               {[
                 { title: 'CPU Threshold Exceeded', server: 'spark-master-01', time: '2m ago', severity: 'critical' },
                 { title: 'Disk Usage > 90%', server: 'minio-storage-02', time: '15m ago', severity: 'warning' },
                 { title: 'Kafka Lag Peak', server: 'broker-cluster', time: '1h ago', severity: 'warning' },
               ].map((alert, i) => (
                 <div key={i} className={`p-4 rounded-xl border ${
                   alert.severity === 'critical' ? 'bg-red-50 border-red-100' : 'bg-amber-50 border-amber-100'
                 }`}>
                   <div className="flex items-center gap-2 mb-1">
                     <ShieldAlert size={16} className={alert.severity === 'critical' ? 'text-red-600' : 'text-amber-600'} />
                     <span className={`text-sm font-bold ${alert.severity === 'critical' ? 'text-red-700' : 'text-amber-700'}`}>
                       {alert.title}
                     </span>
                   </div>
                   <p className="text-xs text-slate-500 mb-2">{alert.server}</p>
                   <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 uppercase flex items-center gap-1">
                        <Clock size={10} /> {alert.time}
                      </span>
                      <button className="text-[10px] font-bold text-blue-600 hover:underline">Acknowledge</button>
                   </div>
                 </div>
               ))}
            </div>
            <button className="mt-8 w-full py-3 bg-slate-50 dark:bg-slate-800 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-100 transition-colors">
              View Alert History
            </button>
         </div>
      </div>
    </div>
  );
};

export default Monitoring;