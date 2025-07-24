import { Injectable } from '@nestjs/common';

interface Project {
  id: number;
  tasks: number[];
  created_at: string;
  name: string;
  description: string;
  permissions?: string[];
}

interface Task {
  id: string;
  status: number; // 10: QUEUED, 20: RUNNING, 30: FAILED, 40: COMPLETED, 50: CANCELED
  progress: number;
  processing_time?: number;
  images_count?: number;
  size?: number;
  statusLabel?: string; // 日本語ラベル
}

function getTaskStatusLabel(status: number): string {
  switch (status) {
    case 10: return '待機中（QUEUED）';
    case 20: return '処理中（RUNNING）';
    case 30: return '失敗（FAILED）';
    case 40: return '完了（COMPLETED）';
    case 50: return 'キャンセル（CANCELED）';
    default: return '不明';
  }
}

@Injectable()
export class WebodmService {
  private webodmUrl: string;
  private apiToken: string;

  constructor() {
    this.webodmUrl = process.env.WEBODM_URL || 'http://localhost:8000';
    this.apiToken = process.env.WEBODM_API_TOKEN || '';
  }

  // プロジェクト一覧の取得
  async getProjects(token: string | null): Promise<Project[]> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/projects/`, { headers });
    
    if (!response.ok) {
      const error = new Error(`プロジェクト一覧の取得に失敗: ${response.status} ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }
    
    return response.json();
  }

  // プロジェクト作成
  async createProject(name: string, token: string | null): Promise<{ id: number }> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/projects/`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ name })
    });
    
    if (!response.ok) {
      const error = new Error(`プロジェクト作成に失敗: ${response.status} ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }
    
    return response.json();
  }

  // プロジェクト詳細の取得
  async getProject(id: number, token: string | null): Promise<Project> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/projects/${id}/`, { headers });
    
    if (!response.ok) {
      const error = new Error(`プロジェクト詳細の取得に失敗: ${response.status} ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }
    
    return response.json();
  }

  // タスク一覧の取得
  async getTasks(projectId: number, token: string | null): Promise<Task[]> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/projects/${projectId}/tasks/`, { headers });
    
    if (!response.ok) {
      const error = new Error(`タスク一覧の取得に失敗: ${response.status} ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }
    
    const tasks: Task[] = await response.json();
    return tasks.map(task => ({ ...task, statusLabel: getTaskStatusLabel(task.status) }));
  }

  // タスク作成
  async createTask(projectId: number, files: Express.Multer.File[], options: string[], token: string | null): Promise<{ id: string }> {
    const formData = new FormData();
    
    // ファイルの追加
    files.forEach(file => {
      formData.append('images', new Blob([file.buffer]), file.originalname);
    });

    // オプションの追加（各オプションを個別に追加）
    options.forEach(option => {
      formData.append('options', option);
    });

    const headers = this.getHeaders(token, false); // multipart/form-dataのためContent-Typeを設定しない
    const response = await fetch(`${this.webodmUrl}/api/projects/${projectId}/tasks/`, {
      method: 'POST',
      headers,
      body: formData
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      const error = new Error(`タスク作成に失敗: ${response.status} ${response.statusText}\n${errorText}`);
      (error as any).status = response.status;
      throw error;
    }
    
    return response.json();
  }

  // タスク詳細の取得
  async getTask(projectId: number, taskId: string, token: string | null): Promise<Task> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/projects/${projectId}/tasks/${taskId}/`, { headers });
    
    if (!response.ok) {
      const error = new Error(`タスク詳細の取得に失敗: ${response.status} ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }
    
    const task: Task = await response.json();
    return { ...task, statusLabel: getTaskStatusLabel(task.status) };
  }

  // タスク削除
  async deleteTask(projectId: number, taskId: string, token: string | null): Promise<void> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/projects/${projectId}/tasks/${taskId}/`, {
      method: 'DELETE',
      headers
    });
    
    if (!response.ok) {
      const error = new Error(`タスク削除に失敗: ${response.status} ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }
  }

  // タスクの再実行
  async restartTask(projectId: number, taskId: string, token: string | null): Promise<any> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/projects/${projectId}/tasks/${taskId}/restart/`, {
      method: 'POST',
      headers
    });
    
    if (!response.ok) {
      const error = new Error(`タスク再実行に失敗: ${response.status} ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }
    
    return response.json();
  }

  // ファイルダウンロード
  async downloadFile(projectId: number, taskId: string, filename: string, token: string | null): Promise<Buffer> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/projects/${projectId}/tasks/${taskId}/download/${filename}`, { headers });
    
    if (!response.ok) {
      const error = new Error(`ファイルダウンロードに失敗: ${response.status} ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }
    
    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer);
  }

  // 管理者: ユーザー一覧取得
  async getAdminUsers(token: string): Promise<any> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/admin/users/`, { headers });
    if (!response.ok) {
      throw new Error(`管理者ユーザー一覧取得に失敗: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  // 管理者: ユーザー新規作成
  async createAdminUser(data: any, token: string): Promise<any> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/admin/users/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      throw new Error(`管理者ユーザー作成に失敗: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  // 管理者: ユーザー詳細取得
  async getAdminUser(id: number, token: string): Promise<any> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/admin/users/${id}/`, { headers });
    if (!response.ok) {
      throw new Error(`管理者ユーザー詳細取得に失敗: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  // 管理者: ユーザー更新
  async updateAdminUser(id: number, data: any, token: string): Promise<any> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/admin/users/${id}/`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      throw new Error(`管理者ユーザー更新に失敗: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  // 管理者: ユーザー削除
  async deleteAdminUser(id: number, token: string): Promise<void> {
    const headers = this.getHeaders(token);
    const response = await fetch(`${this.webodmUrl}/api/admin/users/${id}/`, {
      method: 'DELETE',
      headers
    });
    if (!response.ok) {
      throw new Error(`管理者ユーザー削除に失敗: ${response.status} ${response.statusText}`);
    }
  }

  // サインアップ用ユーザー作成（管理者権限でWebODMにユーザー作成）
  async signupUser(userData: {
    username: string;
    password: string;
    email?: string;
    first_name?: string;
    last_name?: string;
  }, adminToken: string): Promise<any> {
    const headers = this.getHeaders(adminToken);
    
    // WebODM管理者APIでユーザー作成
    const webodmUserData = {
      username: userData.username,
      password: userData.password,
      email: userData.email || '',
      first_name: userData.first_name || '',
      last_name: userData.last_name || '',
      is_superuser: false,
      is_staff: false,
      is_active: true,
      groups: [],
      user_permissions: []
    };

    const response = await fetch(`${this.webodmUrl}/api/admin/users/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(webodmUserData)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`WebODMユーザー作成に失敗: ${response.status} ${response.statusText}\n${errorText}`);
    }

    return response.json();
  }

  // ヘッダーを取得
  private getHeaders(token: string | null, includeContentType: boolean = true): Record<string, string> {
    const headers: Record<string, string> = {};
    
    if (includeContentType) {
      headers['Content-Type'] = 'application/json';
    }
    
    if (token) {
      headers['Authorization'] = `JWT ${token}`;
    }
    
    if (this.apiToken) {
      headers['Token'] = this.apiToken;
    }
    
    return headers;
  }
} 