
import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  Download, 
  Database, 
  FileJson, 
  LayoutList,
  ChevronLeft,
  ChevronRight,
  Eye,
  MoreVertical
} from 'lucide-react';

const layers = ['Bronze', 'Silver', 'Gold'] as const;

const DataExplorer: React.FC = () => {
  const [activeLayer, setActiveLayer] = useState<typeof layers[number]>('Bronze');
  const [searchQuery, setSearchQuery] = useState('');

  const mockData = Array.from({ length: 10 }).map((_, i) => ({
    id: `rec-${i + 1}`,
    name: `${activeLayer}_dataset_${i + 100}`,
    rows: (Math.random() * 1000000).toFixed(0),
    schema: 'Avro',
    updated: '2024-03-20 14:00',
    status: i % 4 === 0 ? 'Failed' : 'Healthy'
  }));

  return (
    <div className="space-y-6">
      {/* Header Tabs */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
          {layers.map((layer) => (
            <button
              key={layer}
              onClick={() => setActiveLayer(layer)}
              className={`
                px-6 py-2 rounded-lg text-sm font-semibold transition-all duration-200
                ${activeLayer === layer 
                  ? 'bg-white dark:bg-slate-700 text-blue-600 shadow-sm' 
                  : 'text-slate-500 hover:text-slate-700'
                }
              `}
            >
              {layer} Layer
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button className="flex items-center gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-4 py-2 rounded-xl text-sm font-medium hover:bg-slate-50 transition-colors">
            <Download size={18} /> Export
          </button>
          <button className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2 rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200">
            <Database size={18} /> Register Data
          </button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Search tables, schemas, or metadata..." 
            className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none transition-shadow"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <button className="flex items-center justify-center gap-2 px-6 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-sm font-medium hover:bg-slate-50 transition-colors">
          <Filter size={18} /> Advanced Filters
        </button>
      </div>

      {/* Table Content */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Dataset Name</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Record Count</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Format</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Last Sync</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {mockData.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-50 dark:bg-blue-900/20 text-blue-600 rounded-lg">
                        <FileJson size={18} />
                      </div>
                      <span className="font-semibold">{row.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{parseInt(row.rows).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-xs font-medium uppercase">{row.schema}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{row.updated}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${row.status === 'Healthy' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                      <span className={`text-xs font-medium ${row.status === 'Healthy' ? 'text-emerald-600' : 'text-red-600'}`}>{row.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-400 hover:text-blue-600 transition-colors">
                        <Eye size={18} />
                      </button>
                      <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-400 transition-colors">
                        <MoreVertical size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between">
          <p className="text-sm text-slate-500">Showing <span className="font-medium text-slate-900 dark:text-white">1</span> to <span className="font-medium text-slate-900 dark:text-white">10</span> of <span className="font-medium text-slate-900 dark:text-white">45</span> results</p>
          <div className="flex gap-2">
            <button className="p-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50">
              <ChevronLeft size={20} />
            </button>
            <button className="p-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-400 hover:text-slate-600 transition-colors">
              <ChevronRight size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataExplorer;
