
export enum PipelineStatus {
  IDLE = 'IDLE',
  INGESTING = 'INGESTING',
  STORING = 'STORING',
  PROCESSING = 'PROCESSING',
  SERVING = 'SERVING',
  COMPLETED = 'COMPLETED',
  ERROR = 'ERROR'
}

export interface ApiConnection {
  id: string;
  name: string;
  baseUrl: string;
  authType: 'Bearer' | 'Basic' | 'ApiKey' | 'None';
  status: 'active' | 'inactive' | 'testing';
  lastChecked: string;
  category: 'News' | 'Financial' | 'Travel' | 'Social';
}

export interface Schedule {
  id: string;
  connectionId: string;
  name: string;
  cron: string;
  enabled: boolean;
  nextRun: string;
  lastRunStatus: 'success' | 'failure' | 'none';
  airflowDagId?: string;
}

export interface ApiRun {
  id: string;
  timestamp: string;
  status: 'success' | 'failure' | 'pending';
  duration: number;
  type: 'manual' | 'scheduled';
  logs: string[];
}

export interface WarehouseRecord {
  id: number;
  timestamp: string;
  region: string;
  category: string;
  metricValue: number;
  qualityScore: number;
  transformationLog: string;
}

export interface TravelLocation {
  id: string;
  name: string;
  city: string;
  category: string;
  rating: number;
  reviewsCount: number;
  avgPrice: number;
  tags: string[];
  matchScore: number;
  recommendationType: 'Content-Based' | 'Collaborative' | 'Hybrid';
}

export interface DataMapping {
  id: string;
  sourceField: string;
  targetField: string;
  transformation: string;
}

export interface PipelineState {
  status: PipelineStatus;
  progress: number;
  activeStep: number;
  logs: string[];
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
}
