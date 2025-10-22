export interface User {
  id: string;
  email: string;
  username: string;
  createdAt: string;
}

export interface Model {
  id: string;
  name: string;
  type: 'sdk' | 'api' | 'container';
  status: 'created' | 'running' | 'stopped' | 'error';
  createdAt: string;
  userId: string;
}

export interface TestRun {
  id: string;
  name: string;
  modelId: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  results: TestResults;
  createdAt: string;
}

export interface TestResults {
  latency: number;
  throughput: number;
  accuracy: number;
  errorRate: number;
  customMetrics: Record<string, number>;
}

export interface CollaborationSession {
  id: string;
  name: string;
  createdBy: string;
  participants: string[];
  isActive: boolean;
}

export interface CodeExecutionResult {
  success: boolean;
  output: string | null;
  error: string | null;
  executionTime: number;
}