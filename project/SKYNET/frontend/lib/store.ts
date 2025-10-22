import { create } from 'zustand'

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

interface AppState {
  user: User | null
  models: Model[]
  testRuns: TestRun[]
  activeTab: string
  collaborationSession: CollaborationSession | null
  setUser: (user: User | null) => void
  setModels: (models: Model[]) => void
  setActiveTab: (tab: string) => void
  addModel: (model: Model) => void
  updateModel: (id: string, updates: Partial<Model>) => void
}

export const useStore = create<AppState>((set, get) => ({
  user: null,
  models: [],
  testRuns: [],
  activeTab: 'code',
  collaborationSession: null,
  
  setUser: (user) => set({ user }),
  setModels: (models) => set({ models }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  
  addModel: (model) => 
    set((state) => ({ models: [...state.models, model] })),
    
  updateModel: (id, updates) =>
    set((state) => ({
      models: state.models.map(model =>
        model.id === id ? { ...model, ...updates } : model
      )
    }))
}))