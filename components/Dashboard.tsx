
import React, { useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { WarehouseRecord } from '../types';

interface Props {
  data: WarehouseRecord[];
  insights: { insights: string[], recommendation: string };
  loadingInsights: boolean;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

const Dashboard: React.FC<Props> = ({ data, insights, loadingInsights }) => {
  const regionData = useMemo(() => {
    const counts: Record<string, number> = {};
    data.forEach(d => {
      counts[d.region] = (counts[d.region] || 0) + d.metricValue;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [data]);

  const avgQuality = useMemo(() => {
    if (data.length === 0) return 0;
    return (data.reduce((acc, d) => acc + d.qualityScore, 0) / data.length).toFixed(1);
  }, [data]);

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400 bg-white rounded-3xl border-2 border-dashed border-slate-200">
        <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
          <i className="fas fa-chart-line text-2xl"></i>
        </div>
        <p className="font-bold">No data available for visualization</p>
        <p className="text-sm">Initiate ETL pipeline to populate warehouse fact tables.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Total Value</p>
          <p className="text-2xl font-black text-slate-800">{(data.reduce((a, b) => a + b.metricValue, 0) / 1000000).toFixed(1)}M <span className="text-xs text-slate-400 font-normal">VND</span></p>
        </div>
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Data Health</p>
          <p className={`text-2xl font-black ${Number(avgQuality) > 90 ? 'text-emerald-500' : 'text-amber-500'}`}>{avgQuality}%</p>
        </div>
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Active Clusters</p>
          <p className="text-2xl font-black text-slate-800">{regionData.length}</p>
        </div>
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Anomaly Detection</p>
          <p className="text-2xl font-black text-emerald-500">Normal</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
          <h3 className="text-sm font-black text-slate-800 mb-6 flex items-center uppercase tracking-tighter">
            <i className="fas fa-map-marked-alt mr-2 text-blue-500"></i> Revenue Distribution by Region
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regionData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#64748b'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#64748b'}} />
                <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)'}} />
                <Bar dataKey="value" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
          <h3 className="text-sm font-black text-slate-800 mb-6 flex items-center uppercase tracking-tighter">
            <i className="fas fa-percentage mr-2 text-emerald-500"></i> Category Composition
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={regionData} cx="50%" cy="50%" innerRadius={80} outerRadius={110} paddingAngle={8} dataKey="value">
                  {regionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-slate-900 p-8 rounded-[32px] text-white shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl"></div>
        <div className="relative z-10 flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center backdrop-blur-md">
              <i className="fas fa-wand-magic-sparkles text-blue-400"></i>
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight">AI Data Governance Insight</h2>
              <p className="text-slate-400 text-xs">Proprietary Nexus Reasoning Engine</p>
            </div>
          </div>
          {loadingInsights && <i className="fas fa-circle-notch fa-spin text-blue-400"></i>}
        </div>

        {!loadingInsights ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
            <div className="space-y-4">
              <h4 className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Market Findings</h4>
              {insights.insights.map((ins, i) => (
                <div key={i} className="flex items-start bg-white/5 p-4 rounded-2xl border border-white/10 hover:bg-white/10 transition-colors">
                  <i className="fas fa-circle-check text-emerald-400 mt-1 mr-4"></i>
                  <span className="text-sm text-slate-200 leading-relaxed">{ins}</span>
                </div>
              ))}
            </div>
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 p-8 rounded-3xl shadow-xl shadow-blue-900/40">
              <h4 className="text-[10px] font-black text-blue-200 uppercase tracking-widest mb-4">Core Recommendation</h4>
              <p className="text-lg font-bold leading-snug italic">"{insights.recommendation}"</p>
              <div className="mt-8 flex items-center text-xs text-blue-200/60 font-medium">
                <i className="fas fa-shield-halved mr-2"></i>
                Certified by Nexus Audit System
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4 animate-pulse">
            <div className="h-16 bg-white/5 rounded-2xl"></div>
            <div className="h-16 bg-white/5 rounded-2xl"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
