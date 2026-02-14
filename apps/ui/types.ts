
export enum UserRole {
  ADMIN = 'ADMIN',
  DATA_ENGINEER = 'DATA_ENGINEER',
  ANALYST = 'ANALYST',
  VIEWER = 'VIEWER'
}

export interface User {
  id: string;
  username: string;
  role: UserRole;
  email: string;
}

export interface PipelineStatus {
  id: string;
  name: string;
  status: 'running' | 'failed' | 'success' | 'queued';
  lastRun: string;
  duration: string;
  throughput: number;
}

export interface DataMetric {
  name: string;
  value: number;
  change: number;
  type: 'events' | 'jobs' | 'errors' | 'alerts';
}

export interface DataRecord {
  id: string;
  timestamp: string;
  layer: 'Bronze' | 'Silver' | 'Gold';
  source: string;
  status: string;
  size: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  service: string;
  message: string;
}
