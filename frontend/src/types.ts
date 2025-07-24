export interface ModelProps {
  url: string;
}

export interface CreateModelResponse {
  project_id: number;
  task_id: number;
}

export interface ModelResponse {
  status: number; // 数値ステータスに変更
  statusLabel?: string; // 日本語ラベル
  running_progress: number;
  model_url?: string;
  processing_time?: number;
  size?: number;
  images_count?: number;
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
  user?: {
    id: number;
    username: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    isAdmin: boolean;
  };
}

export interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  user: {
    id: number;
    username: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    isAdmin: boolean;
  } | null;
}

export interface Task {
  id: string;
  name: string;
  status: number; // 10: QUEUED, 20: RUNNING, 30: FAILED, 40: COMPLETED, 50: CANCELED
  statusLabel?: string; // 日本語ラベル
  progress: number;
  processing_time?: number;  // 処理時間（秒）
  size?: number;            // 使用容量（MB）
  created_at: string;
  options: any;
  images_count: number;
}

export interface Project {
  id: number;
  name: string;
  created_at: string;
  tasks?: Task[]; // オプショナルに変更（APIによっては含まれない場合がある）
}

// タスク作成オプションの型定義
export interface TaskOptions {
  'orthophoto-resolution'?: string;
  'pc-quality'?: string;
  'mesh-quality'?: string;
  [key: string]: string | undefined;
}

// ユーザー関連の型定義
export interface User {
  id: number;
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  isAdmin: boolean;
  webodm_user_id?: number;
  created_at: string;
  updated_at: string;
}

export interface CreateUserRequest {
  username: string;
  password: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  isAdmin?: boolean;
}

export interface SignupRequest {
  username: string;
  password: string;
  email?: string;
  first_name?: string;
  last_name?: string;
} 