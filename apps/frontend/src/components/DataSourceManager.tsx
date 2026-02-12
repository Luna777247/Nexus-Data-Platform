import React, { useState, useEffect } from 'react';
import {
  Database, Plus, Edit3, Trash2, CheckCircle2, XCircle,
  AlertCircle, RefreshCw, FileCode, Settings, Zap, Cloud, Activity, Globe, Layers, Sparkles
} from 'lucide-react';
import {
  getDataSources,
  createDataSource,
  updateDataSource,
  deleteDataSource
} from '../services/apiService';
import { generateDataSourceConfig } from '../services/geminiService';

// Extended Data Source Types
type DataSourceType = 
  // 1. Application Data
  | 'application_api'      // App → API → Kafka
  | 'application_kafka'    // Direct Kafka stream from app
  // 2. Database/OLTP
  | 'jdbc_batch'          // Batch jobs (Airflow)
  | 'jdbc_cdc'            // Change Data Capture
  | 'postgresql'          // PostgreSQL specific
  | 'mysql'               // MySQL specific
  | 'mongodb'             // MongoDB specific
  // 3. Streaming Data
  | 'clickstream'         // User clickstream
  | 'logs'                // Application logs
  | 'event_stream'        // Real-time events
  // 4. External Data
  | 'external_api'        // Third-party APIs (weather, maps, etc)
  | 'open_dataset'        // Public datasets
  | 'social_media'        // Social media APIs
  // Legacy
  | 's3' | 'file';

// Data Source Interface
interface DataSource {
  source_id: string;
  source_name: string;
  source_type: DataSourceType;
  category: 'application' | 'database' | 'streaming' | 'external';
  enabled: boolean;
  location: string;
  kafka_topic: string;
  target_table: string;
  schedule_interval: string;
  format?: string;
  method?: string;
  auth_type?: string;
  cdc_enabled?: boolean;
  required_fields?: string[];
  description?: string;
}

const DataSourceManager: React.FC = () => {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingSource, setEditingSource] = useState<DataSource | null>(null);
  const [aiGenerating, setAiGenerating] = useState(false);

  // Form state
  const [formData, setFormData] = useState<Partial<DataSource>>({
    source_type: 'application_api',
    category: 'application',
    enabled: true,
    format: 'json',
    method: 'GET',
    schedule_interval: '@hourly',
    auth_type: 'bearer'
  });

  useEffect(() => {
    loadDataSources();
  }, []);

  const loadDataSources = async () => {
    setLoading(true);
    try {
      const data = await getDataSources();
      setSources(data);
    } catch (error) {
      console.error('Failed to load data sources:', error);
      alert('❌ Failed to load data sources from API');
      setSources([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAIAutofill = async () => {
    // Validate required fields
    if (!formData.source_id || !formData.source_name || !formData.location || !formData.category) {
      alert('⚠️ Please fill in required fields first:\n- Source ID\n- Source Name\n- Location (URL)\n- Category');
      return;
    }

    setAiGenerating(true);
    try {
      const aiConfig = await generateDataSourceConfig({
        source_id: formData.source_id,
        source_name: formData.source_name,
        location: formData.location,
        category: formData.category,
        source_type: formData.source_type
      });

      // Merge AI suggestions with existing form data
      setFormData(prev => ({
        ...prev,
        kafka_topic: aiConfig.kafka_topic || prev.kafka_topic,
        target_table: aiConfig.target_table || prev.target_table,
        schedule_interval: aiConfig.schedule_interval || prev.schedule_interval,
        method: aiConfig.method || prev.method,
        auth_type: aiConfig.auth_type || prev.auth_type,
        format: aiConfig.format || prev.format,
        required_fields: aiConfig.required_fields || prev.required_fields,
        description: aiConfig.description || prev.description,
        batch_size: aiConfig.batch_size,
        retention_days: aiConfig.retention_days
      }));

      alert('✨ AI configuration generated successfully!\n\nReview the suggested values and adjust as needed.');
    } catch (error) {
      console.error('AI generation failed:', error);
      alert('❌ Failed to generate AI configuration. Please fill manually.');
    } finally {
      setAiGenerating(false);
    }
  };

  const handleAddSource = async () => {
    if (!formData.source_id || !formData.source_name || !formData.location || !formData.category) {
      alert('Please fill in all required fields (ID, Name, Category, Location)');
      return;
    }

    const newSource: DataSource = {
      source_id: formData.source_id!,
      source_name: formData.source_name!,
      source_type: formData.source_type || 'application_api',
      category: formData.category!,
      enabled: formData.enabled ?? true,
      location: formData.location!,
      kafka_topic: formData.kafka_topic || `topic_${formData.source_id}`,
      target_table: formData.target_table || `bronze_${formData.source_id}`,
      schedule_interval: formData.schedule_interval || '@hourly',
      format: formData.format,
      method: formData.method,
      auth_type: formData.auth_type,
      cdc_enabled: formData.cdc_enabled,
      description: formData.description
    };

    try {
      if (editingSource) {
        await updateDataSource(editingSource.source_id, newSource);
        alert('✅ Data source updated');
      } else {
        await createDataSource(newSource);
        alert('✅ Data source added');
      }
      setShowAddForm(false);
      resetForm();
      await loadDataSources();
    } catch (error) {
      console.error('Failed to save data source:', error);
      alert('❌ Failed to save data source');
    }
  };

  const handleDeleteSource = async (sourceId: string) => {
    if (!confirm(`Delete data source "${sourceId}"?`)) {
      return;
    }

    try {
      await deleteDataSource(sourceId);
      alert('🗑️ Data source deleted');
      await loadDataSources();
    } catch (error) {
      console.error('Failed to delete data source:', error);
      alert('❌ Failed to delete data source');
    }
  };

  const handleToggleEnabled = async (sourceId: string) => {
    const target = sources.find((source) => source.source_id === sourceId);
    if (!target) {
      return;
    }
    try {
      await updateDataSource(sourceId, { enabled: !target.enabled });
      await loadDataSources();
    } catch (error) {
      console.error('Failed to toggle source:', error);
      alert('❌ Failed to update source status');
    }
  };

  const resetForm = () => {
    setFormData({
      source_type: 'application_api',
      category: 'application',
      enabled: true,
      format: 'json',
      method: 'GET',
      schedule_interval: '@hourly',
      auth_type: 'bearer'
    });
    setEditingSource(null);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'application': return <Zap className="w-4 h-4" />;
      case 'database': return <Database className="w-4 h-4" />;
      case 'streaming': return <Activity className="w-4 h-4" />;
      case 'external': return <Globe className="w-4 h-4" />;
      default: return <Settings className="w-4 h-4" />;
    }
  };

  const getSourceTypeIcon = (type: DataSourceType) => {
    // Application Data
    if (type.includes('application')) return <Zap className="w-4 h-4" />;
    // Database/OLTP
    if (type.includes('jdbc') || type.includes('sql') || type.includes('mongo')) return <Database className="w-4 h-4" />;
    // Streaming
    if (type === 'clickstream' || type === 'logs' || type === 'event_stream') return <Activity className="w-4 h-4" />;
    // External
    if (type === 'external_api' || type === 'social_media' || type === 'open_dataset') return <Globe className="w-4 h-4" />;
    // Legacy
    if (type === 's3') return <FileCode className="w-4 h-4" />;
    return <Settings className="w-4 h-4" />;
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'application': return 'bg-blue-100 text-blue-700';
      case 'database': return 'bg-purple-100 text-purple-700';
      case 'streaming': return 'bg-green-100 text-green-700';
      case 'external': return 'bg-orange-100 text-orange-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getScheduleColor = (schedule: string) => {
    if (schedule.includes('@continuous')) return 'text-green-600 bg-green-100';
    if (schedule.includes('@hourly')) return 'text-blue-600 bg-blue-100';
    return 'text-gray-600 bg-gray-100';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Database className="w-8 h-8 text-blue-600" />
            Data Source Management
          </h2>
          <p className="text-gray-600 mt-1">
            Manage extensible data ingestion sources • Config-driven pipeline
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadDataSources}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center gap-2 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Data Source
          </button>
        </div>
      </div>

      {/* Add/Edit Form */}
      {showAddForm && (
        <div className="bg-white border-2 border-blue-200 rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
            <Plus className="w-5 h-5 text-blue-600" />
            {editingSource ? 'Edit Data Source' : 'Add New Data Source'}
          </h3>
          
          {/* AI Auto-fill Instructions */}
          <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-purple-900 mb-1">
                  ✨ AI-Powered Configuration
                </p>
                <p className="text-xs text-purple-700">
                  Fill in the <strong>4 required fields</strong> (ID, Name, Location, Category), 
                  then click <strong>"AI Auto-fill"</strong> to automatically generate optimal settings for:
                  Kafka topic, target table, schedule, authentication, format, and more.
                </p>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source ID* <span className="text-gray-500 text-xs">(unique identifier)</span>
              </label>
              <input
                type="text"
                placeholder="e.g., my_new_source"
                value={formData.source_id || ''}
                onChange={(e) => setFormData({ ...formData, source_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source Name*
              </label>
              <input
                type="text"
                placeholder="e.g., My API Data Source"
                value={formData.source_name || ''}
                onChange={(e) => setFormData({ ...formData, source_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Category* <span className="text-gray-500 text-xs">(what type of data?)</span>
              </label>
              <select
                value={formData.category || 'application'}
                onChange={(e) => {
                  const category = e.target.value as DataSource['category'];
                  // Auto-select default source_type for category
                  let defaultType: DataSourceType = 'application_api';
                  if (category === 'database') defaultType = 'postgresql';
                  if (category === 'streaming') defaultType = 'clickstream';
                  if (category === 'external') defaultType = 'external_api';
                  setFormData({ ...formData, category, source_type: defaultType });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="application">📱 Application Data (App → API → Kafka)</option>
                <option value="database">💾 Database/OLTP (PostgreSQL, MySQL...)</option>
                <option value="streaming">⚡ Streaming Data (Clickstream, Logs...)</option>
                <option value="external">🌍 External Data (Weather, Maps, Social...)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source Type*
              </label>
              <select
                value={formData.source_type}
                onChange={(e) => setFormData({ ...formData, source_type: e.target.value as DataSourceType })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {/* Application Data */}
                {formData.category === 'application' && (
                  <>
                    <option value="application_api">App API (REST/GraphQL)</option>
                    <option value="application_kafka">App Kafka Stream</option>
                  </>
                )}
                
                {/* Database/OLTP */}
                {formData.category === 'database' && (
                  <>
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                    <option value="mongodb">MongoDB</option>
                    <option value="jdbc_batch">JDBC Batch Job</option>
                    <option value="jdbc_cdc">JDBC CDC (Real-time)</option>
                  </>
                )}
                
                {/* Streaming Data */}
                {formData.category === 'streaming' && (
                  <>
                    <option value="clickstream">Clickstream</option>
                    <option value="logs">Application Logs</option>
                    <option value="event_stream">Event Stream</option>
                  </>
                )}
                
                {/* External Data */}
                {formData.category === 'external' && (
                  <>
                    <option value="external_api">External API</option>
                    <option value="social_media">Social Media</option>
                    <option value="open_dataset">Open Dataset</option>
                  </>
                )}
              </select>
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description <span className="text-gray-500 text-xs">(what data does this source provide?)</span>
              </label>
              <textarea
                placeholder="e.g., User ratings and reviews from mobile app"
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={2}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location (URL/Connection String)*
              </label>
              <input
                type="text"
                placeholder="e.g., https://api.example.com/data or postgresql://host:port/db"
                value={formData.location || ''}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Authentication Type
              </label>
              <select
                value={formData.auth_type || 'bearer'}
                onChange={(e) => setFormData({ ...formData, auth_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="none">None</option>
                <option value="bearer">Bearer Token</option>
                <option value="api_key">API Key</option>
                <option value="basic">Basic Auth</option>
                <option value="oauth2">OAuth 2.0</option>
              </select>
            </div>

            {/* Show CDC option for database sources */}
            {formData.category === 'database' && (
              <div className="col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.cdc_enabled || false}
                    onChange={(e) => setFormData({ ...formData, cdc_enabled: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Enable CDC (Change Data Capture) for real-time updates
                  </span>
                </label>
                <p className="text-xs text-gray-500 ml-6 mt-1">
                  Uses Debezium to capture database changes in real-time
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Kafka Topic
              </label>
              <input
                type="text"
                placeholder="e.g., topic_my_source"
                value={formData.kafka_topic || ''}
                onChange={(e) => setFormData({ ...formData, kafka_topic: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Table
              </label>
              <input
                type="text"
                placeholder="e.g., bronze_my_source"
                value={formData.target_table || ''}
                onChange={(e) => setFormData({ ...formData, target_table: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Schedule Interval
              </label>
              <select
                value={formData.schedule_interval || '@daily'}
                onChange={(e) => setFormData({ ...formData, schedule_interval: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="@continuous">@continuous (Real-time)</option>
                <option value="@hourly">@hourly</option>
                <option value="@daily">@daily</option>
                <option value="@weekly">@weekly</option>
                <option value="@monthly">@monthly</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Format
              </label>
              <select
                value={formData.format || 'json'}
                onChange={(e) => setFormData({ ...formData, format: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="parquet">Parquet</option>
                <option value="avro">Avro</option>
              </select>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-2">
            <input
              type="checkbox"
              id="enabled"
              checked={formData.enabled ?? true}
              onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
            <label htmlFor="enabled" className="text-sm font-medium text-gray-700">
              Enable this data source
            </label>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={handleAIAutofill}
              disabled={aiGenerating || !formData.source_id || !formData.source_name || !formData.location || !formData.category}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-400 text-white rounded-lg flex items-center gap-2 transition-all shadow-lg disabled:shadow-none"
              title="AI will auto-fill remaining fields based on your input"
            >
              {aiGenerating ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              {aiGenerating ? 'Generating...' : 'AI Auto-fill'}
            </button>
            <button
              onClick={handleAddSource}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              {editingSource ? 'Update Source' : 'Add Source'}
            </button>
            <button
              onClick={() => {
                setShowAddForm(false);
                resetForm();
              }}
              className="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Data Sources List */}
      <div className="grid gap-4">
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-600" />
            <p className="text-gray-600 mt-2">Loading data sources...</p>
          </div>
        ) : sources.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-300">
            <Database className="w-16 h-16 mx-auto text-gray-400" />
            <p className="text-gray-600 mt-4 text-lg">No data sources configured</p>
            <p className="text-gray-500 text-sm mt-1">Click "Add Data Source" to get started</p>
          </div>
        ) : (
          sources.map((source) => (
            <div
              key={source.source_id}
              className={`bg-white rounded-xl border-2 p-5 transition-all hover:shadow-lg ${
                source.enabled ? 'border-green-200' : 'border-gray-200 opacity-60'
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`p-2 rounded-lg ${source.enabled ? getCategoryColor(source.category) : 'bg-gray-100 text-gray-400'}`}>
                      {getCategoryIcon(source.category)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold text-gray-800">{source.source_name}</h3>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getCategoryColor(source.category)}`}>
                          {source.category.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 font-mono">ID: {source.source_id}</p>
                      {source.description && (
                        <p className="text-sm text-gray-600 mt-1">{source.description}</p>
                      )}
                    </div>
                    {source.enabled ? (
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Enabled
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full flex items-center gap-1">
                        <XCircle className="w-3 h-3" />
                        Disabled
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-4 gap-4 mt-4 text-sm border-t border-gray-100 pt-4">
                    <div>
                      <p className="text-gray-500 mb-1 text-xs uppercase">Category</p>
                      <p className="font-medium text-gray-800">{source.category}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 mb-1 text-xs uppercase">Source Type</p>
                      <p className="font-medium text-gray-800 text-xs">{source.source_type.replace(/_/g, ' ')}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 mb-1 text-xs uppercase">Kafka Topic</p>
                      <p className="font-mono text-gray-800 text-xs truncate">{source.kafka_topic}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 mb-1 text-xs uppercase">Target Table</p>
                      <p className="font-mono text-gray-800 text-xs truncate">{source.target_table}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                    <div>
                      <p className="text-gray-500 mb-1 text-xs uppercase">Location</p>
                      <p className="font-mono text-gray-800 text-xs truncate" title={source.location}>{source.location}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 mb-1 text-xs uppercase">Schedule</p>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getScheduleColor(source.schedule_interval)}`}>
                        {source.schedule_interval}
                      </span>
                    </div>
                    <div>
                      <p className="text-gray-500 mb-1 text-xs uppercase">Auth</p>
                      <p className="font-medium text-gray-800 text-xs uppercase">{source.auth_type || 'N/A'}</p>
                    </div>
                  </div>

                  {source.cdc_enabled && (
                    <div className="mt-3">
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
                        ⚡ CDC Enabled (Real-time)
                      </span>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handleToggleEnabled(source.source_id)}
                    className={`p-2 rounded-lg transition-colors ${
                      source.enabled
                        ? 'bg-yellow-100 hover:bg-yellow-200 text-yellow-700'
                        : 'bg-green-100 hover:bg-green-200 text-green-700'
                    }`}
                    title={source.enabled ? 'Disable' : 'Enable'}
                  >
                    {source.enabled ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={() => {
                      setFormData(source);
                      setEditingSource(source);
                      setShowAddForm(true);
                    }}
                    className="p-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors"
                    title="Edit"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteSource(source.source_id)}
                    className="p-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-semibold text-blue-900">Config-Driven Pipeline</h4>
            <p className="text-sm text-blue-800 mt-1">
              Data sources are stored in Postgres and synced to <code className="bg-blue-100 px-1 rounded font-mono">conf/sources.yaml</code>.
              The generic pipeline reads from the database and ingests all enabled sources.
              <strong> No code changes needed!</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataSourceManager;
