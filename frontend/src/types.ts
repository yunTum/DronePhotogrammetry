export interface ModelProps {
  url: string;
}

export interface CreateModelResponse {
  project_id: number;
  task_id: number;
}

export interface ModelResponse {
  status: string;
  running_progress: number;
  model_url?: string;
}

export interface ErrorResponse {
  error: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: {
    id: number;
    username: string;
  };
}

export interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  user: LoginResponse['user'] | null;
}

export interface Task {
  id: string;
  status: number;
  progress: number;
  processing_time?: number;  // 処理時間（秒）
  size?: number;            // 使用容量（MB）
  created_at: string;
  options: any;
}

export interface Project {
  id: number;
  name: string;
  created_at: string;
  tasks: Task[];
} 