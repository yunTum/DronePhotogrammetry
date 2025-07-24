import axios from 'axios';
import { LoginCredentials, LoginResponse, CreateModelResponse, ModelResponse, Project, Task } from '../types';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:3000';
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// リクエストインターセプター
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `JWT ${token}`;
    }
    
    // CSRFトークンを取得して設定
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// CSRFトークンを取得する関数
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
  return null;
}

// レスポンスインターセプター
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.log('JWTが無効です。ログイン画面にリダイレクトします。');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // 現在のページがログイン画面でない場合のみリダイレクト
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

export const webodmApi = {
  // 認証
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    try {
      const response = await api.post<LoginResponse>('/auth/login', credentials);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 401) {
          throw new Error('ユーザー名またはパスワードが正しくありません。');
        }
        throw new Error('ログインに失敗しました。サーバーに接続できません。');
      }
      throw error;
    }
  },

  // プロジェクト一覧の取得
  getProjects: async (): Promise<Project[]> => {
    try {
      const response = await api.get<Project[]>('/api/projects/');
      return response.data;
    } catch (error) {
      console.error('プロジェクト一覧の取得に失敗しました:', error);
      
      // 認証エラーの場合はログイン画面に遷移
      if (axios.isAxiosError(error) && (error.response?.status === 401 || error.response?.status === 403)) {
        console.log('認証エラーのためログイン画面に遷移します');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // 現在のページがログイン画面でない場合のみリダイレクト
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/';
        }
      }
      
      throw error;
    }
  },

  // プロジェクト作成
  createProject: async (name: string): Promise<{ id: number }> => {
    try {
      const response = await api.post<{ id: number }>('/api/projects/', { name });
      return response.data;
    } catch (error) {
      console.error('プロジェクト作成に失敗しました:', error);
      
      // 認証エラーの場合はログイン画面に遷移
      if (axios.isAxiosError(error) && (error.response?.status === 401 || error.response?.status === 403)) {
        console.log('認証エラーのためログイン画面に遷移します');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/';
        }
      }
      
      throw error;
    }
  },

  // タスク作成（ファイルアップロードを含む）
  createTask: async (projectId: number, files: File[], options: any): Promise<{ id: string }> => {
    try {
      // 最低2枚の画像が必要
      if (files.length < 2) {
        throw new Error('最低2枚の画像が必要です。');
      }

      const formData = new FormData();
      
      // ファイルの追加
      files.forEach(file => {
        formData.append('images', file);
      });

      // オプションの追加（WebODMの基本オプション）
      formData.append('options', 'fast-orthophoto');
      formData.append('options', 'dtm');

      const response = await api.post<{ id: string }>(`/api/projects/${projectId}/tasks/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('タスク作成に失敗しました:', error);
      
      // エラーメッセージの改善
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 400) {
          const errorMessage = error.response.data?.error || 'タスク作成に失敗しました。';
          throw new Error(errorMessage);
        }
        
        // 認証エラーの場合はログイン画面に遷移
        if (error.response?.status === 401 || error.response?.status === 403) {
          console.log('認証エラーのためログイン画面に遷移します');
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/';
          }
        }
      }
      
      throw error;
    }
  },

  // タスク状態の取得
  getTaskStatus: async (projectId: number, taskId: string): Promise<ModelResponse> => {
    try {
      const response = await api.get<ModelResponse>(`/api/projects/${projectId}/tasks/${taskId}/`);
      // 進捗状況を0-100の範囲に正規化
      const progress = response.data.running_progress !== undefined ? 
        Math.min(Math.max(Math.round(response.data.running_progress), 0), 100) : 0;
      return {
        ...response.data,
        running_progress: progress
      };
    } catch (error) {
      console.error('タスク状態の取得に失敗しました:', error);
      
      // 認証エラーの場合はログイン画面に遷移
      if (axios.isAxiosError(error) && (error.response?.status === 401 || error.response?.status === 403)) {
        console.log('認証エラーのためログイン画面に遷移します');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/';
        }
      }
      
      throw error;
    }
  },

  // プロジェクト詳細の取得
  getProject: async (projectId: number): Promise<Project> => {
    try {
      const response = await api.get<Project>(`/api/projects/${projectId}/`);
      return response.data;
    } catch (error) {
      console.error('プロジェクト詳細の取得に失敗しました:', error);
      
      // 認証エラーの場合はログイン画面に遷移
      if (axios.isAxiosError(error) && (error.response?.status === 401 || error.response?.status === 403)) {
        console.log('認証エラーのためログイン画面に遷移します');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/';
        }
      }
      
      throw error;
    }
  },

  // タスク一覧の取得
  getTasks: async (projectId: number): Promise<Task[]> => {
    try {
      const response = await api.get<Task[]>(`/api/projects/${projectId}/tasks/`);
      return response.data;
    } catch (error) {
      console.error('タスク一覧の取得に失敗しました:', error);
      
      // 認証エラーの場合はログイン画面に遷移
      if (axios.isAxiosError(error) && (error.response?.status === 401 || error.response?.status === 403)) {
        console.log('認証エラーのためログイン画面に遷移します');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/';
        }
      }
      
      throw error;
    }
  },

  // 3Dモデルの取得
  getModel: async (projectId: number, taskId: string): Promise<string> => {
    try {
      // タスクの状態を確認
      const taskStatus = await webodmApi.getTaskStatus(projectId, taskId);
      console.log('タスクステータス:', taskStatus); // デバッグ用

      // バックエンドのモデル取得APIを使用
      const response = await api.get(`/api/projects/${projectId}/tasks/${taskId}/model`, {
        responseType: 'arraybuffer'
      });
      
      // ArrayBufferをBlobに変換してURLを作成
      const blob = new Blob([response.data], { type: 'model/gltf-binary' });
      const modelUrl = URL.createObjectURL(blob);
      console.log('モデルURL:', modelUrl); // デバッグ用
      return modelUrl;
    } catch (error) {
      console.error('3Dモデルの取得に失敗しました:', error);
      
      // 認証エラーの場合はログイン画面に遷移
      if (axios.isAxiosError(error) && (error.response?.status === 401 || error.response?.status === 403)) {
        console.log('認証エラーのためログイン画面に遷移します');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/';
        }
      }
      
      throw error;
    }
  },

  // モデルURLの取得（非推奨 - getModelを使用してください）
  getModelUrl: (projectId: number, taskId: string): string => {
    console.warn('getModelUrlは非推奨です。getModelを使用してください。');
    return `${API_URL}/api/projects/${projectId}/tasks/${taskId}/model`;
  }
}; 