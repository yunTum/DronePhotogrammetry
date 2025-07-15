import { Injectable } from '@nestjs/common';

interface LoginResponse {
  token: string;
}

@Injectable()
export class AuthService {
  private webodmUrl: string;
  private apiToken: string;

  constructor() {
    this.webodmUrl = process.env.WEBODM_URL || 'http://localhost:8000';
    this.apiToken = process.env.WEBODM_API_TOKEN || '';
  }

  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      console.log('WebODMログイン開始:', username);
      console.log('WebODM URL:', this.webodmUrl);
      console.log('API Token:', this.apiToken ? '設定済み' : '未設定');

      const response = await fetch(`${this.webodmUrl}/api/token-auth/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiToken && { 'Token': this.apiToken })
        },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('WebODMログイン失敗:', response.status, errorText);
        throw new Error(`ログインに失敗しました: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('WebODMレスポンス:', data);

      if (!data.token) {
        throw new Error('WebODMのレスポンスにtokenが含まれていません: ' + JSON.stringify(data));
      }

      return {
        token: data.token
      };
    } catch (error) {
      console.error('WebODMログインエラー:', error);
      throw error;
    }
  }

  async logout(token: string): Promise<void> {
    try {
      console.log('WebODMログアウト開始');

      const response = await fetch(`${this.webodmUrl}/api/token-auth/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `JWT ${token}`,
          ...(this.apiToken && { 'Token': this.apiToken })
        }
      });

      if (!response.ok) {
        console.warn('WebODMログアウト警告:', response.status, response.statusText);
      } else {
        console.log('WebODMログアウト成功');
      }
    } catch (error) {
      console.error('WebODMログアウトエラー:', error);
      // ログアウトエラーは致命的ではないので、エラーを投げない
    }
  }

  // WebODM APIリクエスト用のヘッダーを取得
  getAuthHeaders(token?: string): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };

    if (token) {
      headers['Authorization'] = `JWT ${token}`;
    }

    if (this.apiToken) {
      headers['Token'] = this.apiToken;
    }

    return headers;
  }
} 