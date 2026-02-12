
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  PipelineStatus, ApiConnection, Schedule, ApiRun, TravelLocation,
  PipelineState, ChatMessage, DataMapping, WarehouseRecord
} from 'shared/types';
import { 
  chatWithAnalyst
} from './services/geminiService';
import { 
  getRecommendations, getTours, getRegionalStats, checkApiHealth, convertTourToTravelLocation, convertStatsToWarehouseRecord
} from './services/apiService';
import DataSourceManager from './components/DataSourceManager';
import { 
  LayoutDashboard, Plug, Calendar, PlayCircle, BarChart3, 
  Database, Map as MapIcon, Settings, Brain, Search, 
  Plus, Terminal, CheckCircle2, XCircle, AlertCircle, ChevronRight, 
  Activity, Clock, Server, FileOutput, ShieldCheck, ArrowRightLeft,
  RefreshCw, MoreVertical, Filter, Code2, Trash2, Edit3, Heart, Layers, Sparkles, Send, MapPin, Star, FileCode
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, AreaChart, Area
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('platform_dashboard');
  const [pipeline, setPipeline] = useState<PipelineState>({ status: PipelineStatus.IDLE, progress: 0, activeStep: -1, logs: [] });
  const [connections, setConnections] = useState<ApiConnection[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [recommendations, setRecommendations] = useState<TravelLocation[]>([]);
  const [warehouseData, setWarehouseData] = useState<WarehouseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);
  const [showChat, setShowChat] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatting, setIsChatting] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      setApiError(null);
      try {
        // Check API health first
        const health = await checkApiHealth();
        if (!health) {
          throw new Error('FastAPI backend is not responding');
        }

        // Fetch real data from FastAPI
        const [recResponse, toursResponse, statsResponse] = await Promise.all([
          getRecommendations(123, 15), // Real recommendations from ML model
          getTours(undefined, undefined, undefined, 15), // Real tours from database
          getRegionalStats() // Real analytics from ClickHouse
        ]);

        // Convert API data to component format
        const recommendations = recResponse.recommendations.map(rec => ({
          id: rec.id,
          name: rec.name,
          city: `${rec.region} Region`,
          category: rec.tags[0] || 'Travel',
          rating: rec.rating,
          reviewsCount: Math.floor(Math.random() * 500) + 50,
          avgPrice: rec.price,
          tags: rec.tags,
          matchScore: rec.match_score,
          recommendationType: 'Hybrid',
        } as TravelLocation));

        const warehouseData = [
          ...toursResponse.data.map((tour, idx) => ({
            id: `tour-${idx}`,
            region: tour.region,
            metricValue: tour.price,
            qualityScore: tour.rating * 20,
            category: 'Tours',
            sourceConnection: 'Platform API',
          } as WarehouseRecord)),
          ...statsResponse.data.map((stat, idx) => ({
            id: `stat-${idx}`,
            region: stat.region,
            metricValue: stat.total_revenue,
            qualityScore: stat.conversion_rate,
            category: 'Analytics',
            sourceConnection: 'Platform API',
          } as WarehouseRecord)),
        ];

        setRecommendations(recommendations);
        setWarehouseData(warehouseData);

        // Set mock connections and schedules (these are typically managed by Airflow)
        setConnections([
          { id: 'c1', name: 'Hotels Pro API', baseUrl: 'https://api.hotelspro.com/v2', authType: 'ApiKey', status: 'active', lastChecked: new Date().toISOString(), category: 'Travel' },
          { id: 'c2', name: 'Global Flights Hub', baseUrl: 'https://api.flights.global', authType: 'Bearer', status: 'active', lastChecked: new Date().toISOString(), category: 'Travel' },
          { id: 'c3', name: 'Social Feed Monitor', baseUrl: 'https://social.nexus.io/stream', authType: 'None', status: 'testing', lastChecked: new Date().toISOString(), category: 'Social' },
        ]);

        setSchedules([
          { id: 's1', connectionId: 'c1', name: 'Daily Tour Extraction', cron: '0 2 * * *', enabled: true, nextRun: '2025-05-21T02:00:00Z', lastRunStatus: 'success' },
          { id: 's2', connectionId: 'c2', name: 'Flight Price Alert Sync', cron: '*/30 * * * *', enabled: true, nextRun: '2025-05-20T21:30:00Z', lastRunStatus: 'success' },
        ]);

        setLoading(false);
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Failed to load data from FastAPI';
        console.error('❌ API Error:', errorMsg);
        setApiError(errorMsg);
        setLoading(false);

        // Fallback to mock data if API fails
        console.log('⚠️  Falling back to mock data...');
        setTimeout(() => {
          const [recData, whData] = [
            [],
            []
          ];
          setRecommendations(recData);
          setWarehouseData(whData);
          setConnections([
            { id: 'c1', name: 'Hotels Pro API', baseUrl: 'https://api.hotelspro.com/v2', authType: 'ApiKey', status: 'active', lastChecked: new Date().toISOString(), category: 'Travel' },
            { id: 'c2', name: 'Global Flights Hub', baseUrl: 'https://api.flights.global', authType: 'Bearer', status: 'active', lastChecked: new Date().toISOString(), category: 'Travel' },
            { id: 'c3', name: 'Social Feed Monitor', baseUrl: 'https://social.nexus.io/stream', authType: 'None', status: 'testing', lastChecked: new Date().toISOString(), category: 'Social' },
          ]);
          setSchedules([
            { id: 's1', connectionId: 'c1', name: 'Daily Tour Extraction', cron: '0 2 * * *', enabled: true, nextRun: '2025-05-21T02:00:00Z', lastRunStatus: 'success' },
            { id: 's2', connectionId: 'c2', name: 'Flight Price Alert Sync', cron: '*/30 * * * *', enabled: true, nextRun: '2025-05-20T21:30:00Z', lastRunStatus: 'success' },
          ]);
          setApiError(null);
        }, 500);
      }
    };
    init();
  }, []);

  const addLog = useCallback((msg: string) => { 
    setPipeline(prev => ({ ...prev, logs: [msg, ...prev.logs].slice(0, 50) })); 
  }, []);

  const runETL = async () => {
    if (pipeline.status !== PipelineStatus.IDLE && pipeline.status !== PipelineStatus.COMPLETED) return;
    
    setPipeline({ status: PipelineStatus.INGESTING, progress: 10, activeStep: 0, logs: [] });
    addLog('[INGEST] Pulling raw clusters from 3 active API nodes...');
    await new Promise(r => setTimeout(r, 1000));
    
    setPipeline(p => ({ ...p, status: PipelineStatus.STORING, progress: 30, activeStep: 1 }));
    addLog('[STORAGE] Partitioning raw buffers into Data Lake (S3 Partition dt=20250520)...');
    await new Promise(r => setTimeout(r, 1000));
    
    setPipeline(p => ({ ...p, status: PipelineStatus.PROCESSING, progress: 60, activeStep: 2 }));
    addLog('[PROCESS] Running Spark job: Applying schema mapping & Hybrid Recommendation scores...');
    await new Promise(r => setTimeout(r, 1500));
    
    setPipeline(p => ({ ...p, status: PipelineStatus.SERVING, progress: 90, activeStep: 3 }));
    addLog('[SERVING] Indexing processed results into Warehouse Gold Layer & Vector DB...');
    await new Promise(r => setTimeout(r, 1000));
    
    setPipeline(p => ({ ...p, status: PipelineStatus.COMPLETED, progress: 100, activeStep: 4 }));
    addLog('[SUCCESS] End-to-end platform cycle completed. Refreshing UI metrics.');
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatting) return;
    const userMsg: ChatMessage = { role: 'user', text: chatInput };
    setChatHistory(prev => [...prev, userMsg]);
    setChatInput('');
    setIsChatting(true);
    const response = await chatWithAnalyst([{role: 'user', parts: [{text: chatInput}]}], recommendations);
    setChatHistory(prev => [...prev, { role: 'model', text: response }]);
    setIsChatting(false);
  };

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatHistory]);

  const SidebarItem = ({ id, icon: Icon, label }: { id: string, icon: any, label: string }) => (
    <button 
      onClick={() => setActiveTab(id)} 
      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-2xl transition-all text-sm font-bold ${activeTab === id ? 'bg-blue-600 text-white shadow-xl shadow-blue-500/30' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}
    >
      <Icon size={20} />
      <span>{label}</span>
    </button>
  );

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Sidebar - Representing all 12 modules via stages */}
      <aside className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-10 flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-[18px] flex items-center justify-center shadow-xl shadow-blue-500/20">
            <Layers size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tighter">NEXUS<span className="text-blue-500">DP</span></h1>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Platform Architect</p>
          </div>
        </div>

        <nav className="flex-1 px-4 space-y-8 overflow-y-auto pb-10 scrollbar-hide">
          <div className="space-y-1.5">
            <p className="px-4 text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Core</p>
            <SidebarItem id="platform_dashboard" icon={LayoutDashboard} label="Hub Overview" />
            <SidebarItem id="smart_travel" icon={Sparkles} label="Smart Travel AI" />
          </div>

          <div className="space-y-1.5">
            <p className="px-4 text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">6-Layer Architecture</p>
            <SidebarItem id="connections" icon={Plug} label="1. Ingestion" />
            <SidebarItem id="lake" icon={Database} label="2. Storage" />
            <SidebarItem id="processing" icon={Terminal} label="3. Processing" />
            <SidebarItem id="warehouse" icon={BarChart3} label="4. Serving" />
            <SidebarItem id="consumption" icon={Sparkles} label="5. Consumption" />
            <SidebarItem id="monitoring" icon={ShieldCheck} label="6. Monitoring" />
          </div>

          <div className="space-y-1.5">
            <p className="px-4 text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Orchestration</p>
            <SidebarItem id="airflow" icon={Server} label="Airflow DAGs" />
            <SidebarItem id="schedules" icon={Calendar} label="Auto-Schedules" />
            <SidebarItem id="data_sources" icon={FileCode} label="Data Sources" />
            <SidebarItem id="explorer" icon={Search} label="Data Explorer" />
          </div>

          <div className="space-y-1.5 pt-6 border-t border-slate-800/50">
            <SidebarItem id="admin" icon={ShieldCheck} label="Admin Control" />
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-slate-950">
        <header className="h-24 bg-slate-900/50 backdrop-blur-2xl border-b border-slate-800 flex items-center justify-between px-12 sticky top-0 z-40">
          <div className="flex items-center space-x-6">
            <div className="h-10 w-1.5 bg-blue-500 rounded-full"></div>
            <div>
              <h2 className="text-xl font-black text-white uppercase tracking-tight">{activeTab.replace(/_/g, ' ')}</h2>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                <p className="text-[10px] font-mono text-slate-500">LIVE SYSTEM STATUS: OPTIMAL</p>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-6">
            <button onClick={() => setShowChat(!showChat)} className={`p-3 rounded-2xl transition-all ${showChat ? 'bg-blue-600 text-white shadow-xl shadow-blue-500/20' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
              <Brain size={24} />
            </button>
            <button 
              onClick={runETL} 
              disabled={pipeline.status !== PipelineStatus.IDLE && pipeline.status !== PipelineStatus.COMPLETED}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white px-8 py-3.5 rounded-2xl font-black text-sm shadow-2xl shadow-blue-500/20 transition-all flex items-center space-x-3 active:scale-95"
            >
              <RefreshCw size={20} className={pipeline.status !== PipelineStatus.IDLE && pipeline.status !== PipelineStatus.COMPLETED ? 'animate-spin' : ''} />
              <span>TRIGGER ETL WORKFLOW</span>
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-12 scrollbar-thin scrollbar-thumb-slate-800">
          
          {/* HUB OVERVIEW */}
          {activeTab === 'platform_dashboard' && (
            <div className="max-w-7xl mx-auto space-y-10 animate-in fade-in duration-500">
              
              {/* 6-Layer Architecture Status Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6">
                {[
                  { label: 'Ingestion', value: '45 MB/s', icon: Plug, color: 'from-blue-600 to-cyan-600', border: 'border-blue-500/30' },
                  { label: 'Storage', value: '2.4 TB', icon: Database, color: 'from-cyan-600 to-teal-600', border: 'border-cyan-500/30' },
                  { label: 'Processing', value: '128 Jobs', icon: Terminal, color: 'from-teal-600 to-emerald-600', border: 'border-teal-500/30' },
                  { label: 'Serving', value: '99.98%', icon: BarChart3, color: 'from-emerald-600 to-green-600', border: 'border-emerald-500/30' },
                  { label: 'Consumption', value: '12 Tools', icon: Sparkles, color: 'from-orange-600 to-amber-600', border: 'border-orange-500/30' },
                  { label: 'Monitoring', value: '98.3%', icon: ShieldCheck, color: 'from-red-600 to-rose-600', border: 'border-red-500/30' },
                ].map((layer, i) => (
                  <div key={i} className={`bg-gradient-to-br ${layer.color} p-6 rounded-3xl border ${layer.border} shadow-xl hover:scale-105 transition-all cursor-pointer group relative overflow-hidden`}>
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                      <layer.icon size={60} />
                    </div>
                    <div className="relative z-10">
                      <layer.icon size={20} className="mb-3 opacity-80" />
                      <p className="text-[9px] font-black uppercase tracking-widest opacity-90 mb-1">{layer.label}</p>
                      <p className="text-xl font-black text-white">{layer.value}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* System Health Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                {[
                  { label: 'Platform Uptime', value: '99.99%', icon: Clock, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
                  { label: 'Active DAGs', value: '12/12', icon: Server, color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
                  { label: 'Data Quality', value: '98.3%', icon: ShieldCheck, color: 'text-blue-500', bg: 'bg-blue-500/10' },
                  { label: 'Rec. Accuracy', value: '94.8%', icon: Heart, color: 'text-rose-500', bg: 'bg-rose-500/10' },
                ].map((stat, i) => (
                  <div key={i} className="bg-slate-900 p-8 rounded-[40px] border border-slate-800 hover:border-blue-500/40 transition-all shadow-xl group">
                    <div className="flex justify-between items-center mb-6">
                      <div className={`p-4 rounded-2xl ${stat.bg} border border-slate-800 ${stat.color}`}>
                        <stat.icon size={24} />
                      </div>
                      <div className={`w-2 h-2 rounded-full ${stat.bg.replace('/10', '')} animate-pulse`}></div>
                    </div>
                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{stat.label}</p>
                    <p className="text-3xl font-black text-white">{stat.value}</p>
                  </div>
                ))}
              </div>

              {/* End-to-End Pipeline Monitor */}
              <div className="bg-gradient-to-br from-slate-900 to-slate-950 p-12 rounded-[56px] border border-slate-800 shadow-2xl overflow-hidden relative">
                <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
                  <Database size={300} />
                </div>
                <h3 className="text-2xl font-black mb-12 flex items-center space-x-4">
                  <Activity className="text-blue-500" size={28} />
                  <span>6-Layer Data Platform Flow</span>
                  <span className="ml-auto text-xs font-mono text-slate-500 px-4 py-2 rounded-full bg-slate-950 border border-slate-800">Real-time Status</span>
                </h3>
                
                <div className="flex justify-between items-center relative gap-3">
                  {['Ingestion', 'Storage', 'Processing', 'Serving', 'Consumption', 'Monitoring'].map((stage, idx) => (
                    <div key={stage} className={`flex flex-col items-center z-10 transition-all duration-700 ${idx <= pipeline.activeStep ? 'opacity-100 scale-105' : 'opacity-30'}`}>
                      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center border-4 ${idx <= pipeline.activeStep ? 'bg-gradient-to-br from-blue-600 to-indigo-600 border-blue-400 text-white shadow-2xl shadow-blue-500/50 animate-pulse' : 'bg-slate-800 border-slate-700 text-slate-500'}`}>
                        <span className="text-2xl font-black">{idx + 1}</span>
                      </div>
                      <p className={`mt-4 text-[10px] font-black uppercase tracking-widest ${idx <= pipeline.activeStep ? 'text-blue-400' : 'text-slate-600'}`}>{stage}</p>
                    </div>
                  ))}
                  {/* Progress Connector */}
                  <div className="absolute top-8 left-0 w-full h-2 bg-slate-800 -z-10 rounded-full">
                    <div className="h-full bg-gradient-to-r from-blue-600 to-indigo-600 transition-all duration-1000 rounded-full shadow-lg shadow-blue-500/50" style={{ width: `${((pipeline.activeStep + 1) / 6) * 100}%` }}></div>
                  </div>
                </div>

                <div className="mt-16 bg-slate-950 p-8 rounded-[40px] border border-slate-800/50">
                   <div className="flex justify-between items-center mb-6">
                      <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">Execution Logs (Airflow + Spark)</h4>
                      <Terminal size={16} className="text-blue-500" />
                   </div>
                   <div className="space-y-3 font-mono text-[11px] leading-relaxed max-h-60 overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-slate-800">
                      {pipeline.logs.map((log, i) => (
                        <div key={i} className="flex space-x-6 text-slate-400 hover:text-white transition-colors">
                           <span className="text-blue-500 font-bold shrink-0">[{new Date().toLocaleTimeString()}]</span>
                           <span>{log}</span>
                        </div>
                      ))}
                      {pipeline.logs.length === 0 && <p className="text-slate-700 italic text-center py-10">Waiting for trigger event...</p>}
                   </div>
                </div>
              </div>
            </div>
          )}

          {/* SMART TRAVEL AI - HYBRID RECOM RESULTS */}
          {activeTab === 'smart_travel' && (
            <div className="max-w-7xl mx-auto space-y-12 animate-in slide-in-from-bottom-6 duration-700">
              <div className="flex items-center justify-between">
                <div>
                   <h2 className="text-4xl font-black tracking-tighter">Hybrid Recommender Output</h2>
                   <p className="text-slate-500 font-medium mt-2 italic">Combining Content-based (Tags) & Collaborative (User Ratings) filters for optimal tour matching.</p>
                </div>
                <div className="flex space-x-3">
                   <button className="bg-slate-800 px-6 py-3 rounded-2xl text-xs font-black text-slate-400 border border-slate-700 hover:text-white">Adjust Weights</button>
                   <button className="bg-blue-600 text-white px-6 py-3 rounded-2xl text-xs font-black shadow-xl shadow-blue-500/20">Refine Model</button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {recommendations.map(rec => (
                  <div key={rec.id} className="bg-slate-900 rounded-[48px] border border-slate-800 overflow-hidden hover:border-blue-500/50 transition-all shadow-2xl group cursor-pointer">
                    <div className="h-48 bg-slate-800 relative flex items-center justify-center">
                       <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent"></div>
                       <MapPin className="text-blue-500 group-hover:scale-110 transition-transform" size={48} />
                       <div className="absolute top-6 right-6">
                          <div className="bg-blue-600 text-white px-4 py-2 rounded-2xl text-[10px] font-black shadow-2xl ring-4 ring-blue-500/10">
                             {Math.round(rec.matchScore * 100)}% MATCH
                          </div>
                       </div>
                    </div>
                    <div className="p-10 space-y-6">
                       <div>
                         <h3 className="text-xl font-black mb-1 group-hover:text-blue-400 transition-colors">{rec.name}</h3>
                         <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">{rec.city} • {rec.category}</p>
                       </div>
                       <div className="flex flex-wrap gap-2">
                          {rec.tags.map(tag => (
                            <span key={tag} className="px-3 py-1 bg-slate-950 text-slate-500 rounded-xl text-[10px] font-bold border border-slate-800">#{tag}</span>
                          ))}
                       </div>
                       <div className="pt-6 border-t border-slate-800 flex justify-between items-center">
                          <p className="text-xl font-black text-emerald-500">{rec.avgPrice.toLocaleString()} <span className="text-[10px] text-slate-600">VND</span></p>
                          <div className="flex items-center space-x-1.5 text-amber-500 font-black">
                             <Star size={14} fill="currentColor" />
                             <span>{rec.rating}</span>
                          </div>
                       </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="bg-slate-900 p-12 rounded-[56px] border border-slate-800 shadow-2xl">
                 <h3 className="text-xl font-black mb-12 flex items-center space-x-4">
                    <BarChart3 className="text-blue-500" />
                    <span>Serving Layer: Recommendation Analytics</span>
                 </h3>
                 <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                    <div className="h-[400px]">
                      <ResponsiveContainer width="100%" height="100%">
                         <BarChart data={recommendations.slice(0, 10)}>
                           <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                           <XAxis dataKey="city" hide />
                           <YAxis axisLine={false} tickLine={false} tick={{fill: '#475569', fontSize: 10}} />
                           <ReTooltip contentStyle={{backgroundColor: '#0f172a', border: 'none', borderRadius: '16px'}} />
                           <Bar dataKey="reviewsCount" fill="#3b82f6" radius={[12, 12, 0, 0]} barSize={40} />
                         </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-6 flex flex-col justify-center">
                       <div className="p-8 bg-blue-600/10 rounded-[32px] border border-blue-500/20">
                          <p className="text-[10px] font-black text-blue-500 uppercase tracking-widest mb-4">Hybrid Precision Score</p>
                          <p className="text-3xl font-black">0.94 <span className="text-xs text-slate-500 font-normal">MAP@10</span></p>
                       </div>
                       <div className="p-8 bg-emerald-600/10 rounded-[32px] border border-emerald-500/20">
                          <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-4">Serving Availability</p>
                          <p className="text-3xl font-black">99.98 <span className="text-xs text-slate-500 font-normal">%</span></p>
                       </div>
                    </div>
                 </div>
              </div>
            </div>
          )}

          {/* INGESTION MODULE */}
          {activeTab === 'connections' && (
            <div className="max-w-6xl mx-auto space-y-10 animate-in slide-in-from-left duration-300">
              <div className="flex justify-between items-end">
                <div>
                   <h2 className="text-3xl font-black">Data Ingestion Hub</h2>
                   <p className="text-slate-500">Configured API clusters for real-time tourism extraction.</p>
                </div>
                <button 
                  onClick={() => setActiveTab('data_sources')}
                  className="bg-blue-600 text-white px-8 py-3.5 rounded-2xl font-black text-sm shadow-xl shadow-blue-500/20 flex items-center space-x-3 active:scale-95 transition-all hover:bg-blue-500 cursor-pointer"
                >
                  <Plus size={18} /><span>ADD NEW SOURCE</span>
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {connections.map(conn => (
                  <div key={conn.id} className="bg-slate-900 p-10 rounded-[48px] border border-slate-800 relative group overflow-hidden">
                    <div className="absolute top-0 right-0 p-8">
                       <Activity className={`${conn.status === 'active' ? 'text-emerald-500' : 'text-slate-700'}`} size={20} />
                    </div>
                    <div className={`w-16 h-16 rounded-[24px] mb-8 flex items-center justify-center ${conn.status === 'active' ? 'bg-blue-600/10 text-blue-500 border border-blue-500/20' : 'bg-slate-800 text-slate-500'}`}>
                       <Plug size={28} />
                    </div>
                    <h3 className="text-2xl font-black mb-2">{conn.name}</h3>
                    <p className="text-xs font-mono text-slate-500 mb-8 truncate">{conn.baseUrl}</p>
                    <div className="flex items-center justify-between pt-8 border-t border-slate-800">
                       <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase ${conn.status === 'active' ? 'bg-emerald-500/20 text-emerald-500' : 'bg-slate-800 text-slate-500'}`}>{conn.status}</span>
                       <button className="text-[10px] font-black text-blue-500 uppercase hover:underline">Check Health</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* DATA LAKE EXPLORER */}
          {activeTab === 'lake' && (
            <div className="max-w-7xl mx-auto space-y-10 animate-in fade-in duration-500">
               <div className="bg-slate-900 p-12 rounded-[56px] border border-slate-800 shadow-2xl relative overflow-hidden">
                 <div className="flex items-center space-x-6 mb-12">
                    <div className="w-16 h-16 bg-blue-600 rounded-3xl flex items-center justify-center text-white"><Database size={32} /></div>
                    <div>
                       <h2 className="text-3xl font-black uppercase tracking-tight">Data Lake Storage (S3-Equivalent)</h2>
                       <p className="text-slate-500 font-mono text-xs">Bucket: s3://nexus-platform-prod / Region: ap-southeast-1</p>
                    </div>
                 </div>
                 <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                   <div className="space-y-6">
                      <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">Partition Directory Browser</p>
                      {['dt=20250520', 'dt=20250519', 'dt=20250518'].map(p => (
                        <div key={p} className="flex items-center justify-between p-6 bg-slate-950 rounded-[28px] border border-slate-800 hover:border-blue-500/50 cursor-pointer transition-all">
                           <div className="flex items-center space-x-4">
                              <Layers size={18} className="text-blue-500" />
                              <span className="font-mono text-sm">{p}</span>
                           </div>
                           <span className="text-[10px] font-bold text-slate-600">142 Objects</span>
                        </div>
                      ))}
                   </div>
                   <div className="bg-slate-950 p-10 rounded-[40px] border border-slate-800">
                      <h4 className="text-xs font-black mb-8 flex items-center space-x-3"><Code2 className="text-blue-500" /> <span>Raw Parquet Schema (First 10 Rows)</span></h4>
                      <pre className="text-[10px] font-mono text-emerald-500 leading-relaxed overflow-x-auto whitespace-pre">
                        {JSON.stringify(recommendations.slice(0, 3), null, 2)}
                      </pre>
                   </div>
                 </div>
               </div>
            </div>
          )}

          {/* SERVING LAYER / WAREHOUSE */}
          {activeTab === 'warehouse' && (
            <div className="max-w-7xl mx-auto space-y-10 animate-in fade-in duration-500">
               <div className="flex justify-between items-end">
                  <div>
                    <h2 className="text-3xl font-black">Serving Layer (Snowflake Gold)</h2>
                    <p className="text-slate-500 font-medium mt-1">Aggregated dimensions for business intelligence.</p>
                  </div>
                  <div className="flex space-x-3">
                     <button className="bg-slate-800 p-3 rounded-xl"><FileOutput size={18}/></button>
                  </div>
               </div>
               <div className="bg-slate-900 rounded-[48px] border border-slate-800 overflow-hidden shadow-2xl">
                  <table className="w-full text-left text-sm">
                     <thead>
                        <tr className="bg-slate-800/50 text-slate-500 text-[10px] font-black uppercase tracking-widest border-b border-slate-800">
                           <th className="px-10 py-6">Fact ID</th>
                           <th className="px-10 py-6">Timestamp</th>
                           <th className="px-10 py-6">Cluster</th>
                           <th className="px-10 py-6 text-right">Metric (VND)</th>
                           <th className="px-10 py-6 text-right">Data Health</th>
                           <th className="px-10 py-6 text-center">Transform</th>
                        </tr>
                     </thead>
                     <tbody className="divide-y divide-slate-800/30">
                        {warehouseData.map(row => (
                          <tr key={row.id} className="hover:bg-slate-800/30 transition-colors group">
                             <td className="px-10 py-6 font-mono text-xs text-blue-500">FAC_{row.id}</td>
                             <td className="px-10 py-6 text-slate-400 text-xs">{row.timestamp}</td>
                             <td className="px-10 py-6 font-black text-white">{row.region}</td>
                             <td className="px-10 py-6 text-right font-bold text-emerald-500">{row.metricValue.toLocaleString()}</td>
                             <td className="px-10 py-6 text-right">
                                <span className={`px-3 py-1 rounded-full text-[9px] font-black ${row.qualityScore > 90 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>
                                   {row.qualityScore}% SCORE
                                </span>
                             </td>
                             <td className="px-10 py-6 text-center">
                                <button className="text-slate-500 hover:text-blue-500"><Terminal size={16} /></button>
                             </td>
                          </tr>
                        ))}
                     </tbody>
                  </table>
               </div>
            </div>
          )}

          {/* CONSUMPTION LAYER (Layer 5) */}
          {activeTab === 'consumption' && (
            <div className="max-w-7xl mx-auto space-y-10 animate-in fade-in duration-500">
              <div>
                <h2 className="text-3xl font-black mb-2">Data Consumption Layer</h2>
                <p className="text-slate-500">BI Tools, Notebooks, and End-User Applications</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Superset */}
                <div className="bg-gradient-to-br from-slate-900 to-slate-950 p-10 rounded-[48px] border border-orange-500/30 relative group overflow-hidden hover:border-orange-500/50 transition-all shadow-xl hover:shadow-orange-500/20">
                  <div className="absolute top-0 right-0 p-8 opacity-20">
                    <BarChart3 className="text-orange-500" size={80} />
                  </div>
                  <div className="w-16 h-16 rounded-[24px] mb-8 flex items-center justify-center bg-orange-600/10 text-orange-500 border border-orange-500/20">
                    <BarChart3 size={32} />
                  </div>
                  <h3 className="text-2xl font-black mb-2">Apache Superset</h3>
                  <p className="text-xs text-slate-500 mb-8">Interactive BI dashboards and visualizations</p>
                  <div className="space-y-3 mb-8">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Port</span>
                      <span className="font-mono text-orange-500">8088</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Dashboards</span>
                      <span className="font-bold text-white">12 Active</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Status</span>
                      <span className="px-2 py-1 rounded-full text-[9px] font-black bg-emerald-500/20 text-emerald-500">RUNNING</span>
                    </div>
                  </div>
                  <button className="w-full bg-orange-600 hover:bg-orange-500 text-white py-3 rounded-2xl font-black text-sm transition-all active:scale-95">Open Superset</button>
                </div>

                {/* Grafana */}
                <div className="bg-gradient-to-br from-slate-900 to-slate-950 p-10 rounded-[48px] border border-orange-500/30 relative group overflow-hidden hover:border-orange-500/50 transition-all shadow-xl hover:shadow-orange-500/20">
                  <div className="absolute top-0 right-0 p-8 opacity-20">
                    <Activity className="text-orange-500" size={80} />
                  </div>
                  <div className="w-16 h-16 rounded-[24px] mb-8 flex items-center justify-center bg-orange-600/10 text-orange-500 border border-orange-500/20">
                    <Activity size={32} />
                  </div>
                  <h3 className="text-2xl font-black mb-2">Grafana</h3>
                  <p className="text-xs text-slate-500 mb-8">Real-time monitoring and observability</p>
                  <div className="space-y-3 mb-8">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Port</span>
                      <span className="font-mono text-orange-500">3000</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Datasources</span>
                      <span className="font-bold text-white">8 Connected</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Status</span>
                      <span className="px-2 py-1 rounded-full text-[9px] font-black bg-amber-500/20 text-amber-500">PLANNED</span>
                    </div>
                  </div>
                  <button className="w-full bg-slate-700 hover:bg-slate-600 text-white py-3 rounded-2xl font-black text-sm transition-all active:scale-95">Configure</button>
                </div>

                {/* Jupyter */}
                <div className="bg-gradient-to-br from-slate-900 to-slate-950 p-10 rounded-[48px] border border-orange-500/30 relative group overflow-hidden hover:border-orange-500/50 transition-all shadow-xl hover:shadow-orange-500/20">
                  <div className="absolute top-0 right-0 p-8 opacity-20">
                    <FileCode className="text-orange-500" size={80} />
                  </div>
                  <div className="w-16 h-16 rounded-[24px] mb-8 flex items-center justify-center bg-orange-600/10 text-orange-500 border border-orange-500/20">
                    <FileCode size={32} />
                  </div>
                  <h3 className="text-2xl font-black mb-2">Jupyter Notebook</h3>
                  <p className="text-xs text-slate-500 mb-8">Interactive data science and ML workflows</p>
                  <div className="space-y-3 mb-8">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Port</span>
                      <span className="font-mono text-orange-500">8888</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Notebooks</span>
                      <span className="font-bold text-white">24 Files</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Status</span>
                      <span className="px-2 py-1 rounded-full text-[9px] font-black bg-amber-500/20 text-amber-500">PLANNED</span>
                    </div>
                  </div>
                  <button className="w-full bg-slate-700 hover:bg-slate-600 text-white py-3 rounded-2xl font-black text-sm transition-all active:scale-95">Setup Jupyter</button>
                </div>
              </div>
            </div>
          )}

          {/* MONITORING & GOVERNANCE (Layer 6) */}
          {activeTab === 'monitoring' && (
            <div className="max-w-7xl mx-auto space-y-10 animate-in fade-in duration-500">
              <div>
                <h2 className="text-3xl font-black mb-2">Monitoring & Governance</h2>
                <p className="text-slate-500">Data Quality, Lineage, Security & Observability</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Prometheus + Grafana */}
                <div className="bg-gradient-to-br from-slate-900 to-slate-950 p-10 rounded-[48px] border border-red-500/30 relative group overflow-hidden hover:border-red-500/50 transition-all shadow-xl hover:shadow-red-500/20">
                  <div className="absolute top-0 right-0 p-8 opacity-20">
                    <Activity className="text-red-500" size={80} />
                  </div>
                  <div className="w-16 h-16 rounded-[24px] mb-8 flex items-center justify-center bg-red-600/10 text-red-500 border border-red-500/20">
                    <Activity size={32} />
                  </div>
                  <h3 className="text-2xl font-black mb-2">Prometheus</h3>
                  <p className="text-xs text-slate-500 mb-8">Metrics collection and alerting system</p>
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[9px] text-slate-500 font-black uppercase mb-1">Metrics/sec</p>
                      <p className="text-xl font-black text-white">1,240</p>
                    </div>
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[9px] text-slate-500 font-black uppercase mb-1">Alerts</p>
                      <p className="text-xl font-black text-emerald-500">0</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs mb-4">
                    <span className="text-slate-500">Status</span>
                    <span className="px-2 py-1 rounded-full text-[9px] font-black bg-amber-500/20 text-amber-500">PLANNED</span>
                  </div>
                  <button className="w-full bg-red-600 hover:bg-red-500 text-white py-3 rounded-2xl font-black text-sm transition-all active:scale-95">View Metrics</button>
                </div>

                {/* DataHub */}
                <div className="bg-gradient-to-br from-slate-900 to-slate-950 p-10 rounded-[48px] border border-purple-500/30 relative group overflow-hidden hover:border-purple-500/50 transition-all shadow-xl hover:shadow-purple-500/20">
                  <div className="absolute top-0 right-0 p-8 opacity-20">
                    <Database className="text-purple-500" size={80} />
                  </div>
                  <div className="w-16 h-16 rounded-[24px] mb-8 flex items-center justify-center bg-purple-600/10 text-purple-500 border border-purple-500/20">
                    <Database size={32} />
                  </div>
                  <h3 className="text-2xl font-black mb-2">DataHub</h3>
                  <p className="text-xs text-slate-500 mb-8">Metadata catalog and data discovery</p>
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[9px] text-slate-500 font-black uppercase mb-1">Datasets</p>
                      <p className="text-xl font-black text-white">342</p>
                    </div>
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[9px] text-slate-500 font-black uppercase mb-1">Lineage</p>
                      <p className="text-xl font-black text-purple-500">128</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs mb-4">
                    <span className="text-slate-500">Status</span>
                    <span className="px-2 py-1 rounded-full text-[9px] font-black bg-amber-500/20 text-amber-500">PLANNED</span>
                  </div>
                  <button className="w-full bg-purple-600 hover:bg-purple-500 text-white py-3 rounded-2xl font-black text-sm transition-all active:scale-95">Browse Catalog</button>
                </div>

                {/* Great Expectations */}
                <div className="bg-gradient-to-br from-slate-900 to-slate-950 p-10 rounded-[48px] border border-blue-500/30 relative group overflow-hidden hover:border-blue-500/50 transition-all shadow-xl hover:shadow-blue-500/20">
                  <div className="absolute top-0 right-0 p-8 opacity-20">
                    <ShieldCheck className="text-blue-500" size={80} />
                  </div>
                  <div className="w-16 h-16 rounded-[24px] mb-8 flex items-center justify-center bg-blue-600/10 text-blue-500 border border-blue-500/20">
                    <ShieldCheck size={32} />
                  </div>
                  <h3 className="text-2xl font-black mb-2">Great Expectations</h3>
                  <p className="text-xs text-slate-500 mb-8">Data quality validation and testing</p>
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[9px] text-slate-500 font-black uppercase mb-1">Tests Run</p>
                      <p className="text-xl font-black text-white">1,248</p>
                    </div>
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[9px] text-slate-500 font-black uppercase mb-1">Pass Rate</p>
                      <p className="text-xl font-black text-emerald-500">98.3%</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs mb-4">
                    <span className="text-slate-500">Status</span>
                    <span className="px-2 py-1 rounded-full text-[9px] font-black bg-emerald-500/20 text-emerald-500">ACTIVE</span>
                  </div>
                  <button className="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-2xl font-black text-sm transition-all active:scale-95">View Reports</button>
                </div>

                {/* Apache Atlas */}
                <div className="bg-gradient-to-br from-slate-900 to-slate-950 p-10 rounded-[48px] border border-teal-500/30 relative group overflow-hidden hover:border-teal-500/50 transition-all shadow-xl hover:shadow-teal-500/20">
                  <div className="absolute top-0 right-0 p-8 opacity-20">
                    <Layers className="text-teal-500" size={80} />
                  </div>
                  <div className="w-16 h-16 rounded-[24px] mb-8 flex items-center justify-center bg-teal-600/10 text-teal-500 border border-teal-500/20">
                    <Layers size={32} />
                  </div>
                  <h3 className="text-2xl font-black mb-2">Apache Atlas</h3>
                  <p className="text-xs text-slate-500 mb-8">Data governance and compliance</p>
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[9px] text-slate-500 font-black uppercase mb-1">Entities</p>
                      <p className="text-xl font-black text-white">892</p>
                    </div>
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[9px] text-slate-500 font-black uppercase mb-1">Tags</p>
                      <p className="text-xl font-black text-teal-500">156</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs mb-4">
                    <span className="text-slate-500">Status</span>
                    <span className="px-2 py-1 rounded-full text-[9px] font-black bg-amber-500/20 text-amber-500">PLANNED</span>
                  </div>
                  <button className="w-full bg-teal-600 hover:bg-teal-500 text-white py-3 rounded-2xl font-black text-sm transition-all active:scale-95">Open Atlas</button>
                </div>
              </div>
            </div>
          )}

          {/* Data Sources Management */}
          {activeTab === 'data_sources' && (
            <div className="max-w-7xl mx-auto animate-in fade-in duration-500">
              <DataSourceManager />
            </div>
          )}

          {/* Placeholders for remaining modules */}
          {['processing', 'airflow', 'schedules', 'explorer', 'admin'].includes(activeTab) && (
            <div className="flex flex-col items-center justify-center h-full py-40 opacity-20 grayscale grayscale-100">
               <Layers size={100} className="mb-8" />
               <h2 className="text-3xl font-black uppercase tracking-[0.4em] mb-4">{activeTab} Interface</h2>
               <p className="font-bold text-sm tracking-widest uppercase">Dedicated node standby mode</p>
            </div>
          )}
          
        </div>

        {/* AI Chat Drawer */}
        {showChat && (
          <div className="absolute top-0 right-0 w-[580px] h-full bg-slate-900 border-l border-slate-800 shadow-2xl z-50 flex flex-col animate-in slide-in-from-right duration-500 ring-8 ring-blue-500/5">
             <div className="p-12 border-b border-slate-800 bg-slate-950 flex justify-between items-center">
                <div className="flex items-center space-x-6">
                   <div className="w-16 h-16 bg-blue-600 rounded-[24px] flex items-center justify-center shadow-2xl shadow-blue-500/30">
                      <Brain size={32} className="text-white" />
                   </div>
                   <div>
                      <h3 className="font-black text-2xl">Nexus Platform AI</h3>
                      <div className="flex items-center space-x-2">
                         <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                         <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Hybrid Model Context Aware</span>
                      </div>
                   </div>
                </div>
                <button onClick={() => setShowChat(false)} className="p-3 hover:bg-slate-800 rounded-full transition-all text-slate-500 hover:text-white"><XCircle size={32}/></button>
             </div>

             <div className="flex-1 overflow-y-auto p-12 space-y-10 scrollbar-hide">
                {chatHistory.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[90%] px-8 py-6 rounded-[36px] text-sm leading-relaxed shadow-2xl ${msg.role === 'user' ? 'bg-blue-600 text-white font-bold rounded-tr-none' : 'bg-slate-800 text-slate-100 rounded-tl-none border border-slate-700'}`}>
                      {msg.text}
                    </div>
                  </div>
                ))}
                {isChatting && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800 px-8 py-6 rounded-[36px] rounded-tl-none flex space-x-2 animate-pulse">
                       <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                       <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                       <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
             </div>

             <form onSubmit={handleSendMessage} className="p-12 border-t border-slate-800 bg-slate-950/50">
                <div className="relative group">
                   <input 
                    type="text" 
                    value={chatInput} 
                    onChange={(e) => setChatInput(e.target.value)} 
                    placeholder="Ask about hybrid model weights or ETL health..." 
                    className="w-full bg-slate-900 border-2 border-slate-800 rounded-[32px] pl-10 pr-20 py-7 text-sm font-bold focus:outline-none focus:border-blue-500/50 transition-all shadow-inner"
                   />
                   <button type="submit" disabled={isChatting} className="absolute right-5 top-1/2 -translate-y-1/2 w-14 h-14 bg-blue-600 rounded-3xl flex items-center justify-center text-white shadow-2xl shadow-blue-500/30 hover:scale-110 active:scale-95 transition-all">
                      <Send size={24} />
                   </button>
                </div>
             </form>
          </div>
        )}

      </main>
    </div>
  );
};

export default App;
