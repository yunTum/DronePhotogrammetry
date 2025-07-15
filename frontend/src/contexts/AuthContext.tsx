import React, { createContext, useContext, useState } from 'react';
import { LoginCredentials, LoginResponse, AuthState } from '../types';
import { webodmApi } from '../api/webodm';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>(() => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    let user = null;
    
    try {
      if (userStr) {
        user = JSON.parse(userStr);
      }
    } catch (error) {
      console.error('ユーザー情報の解析に失敗しました:', error);
      localStorage.removeItem('user');
    }

    return {
      token,
      isAuthenticated: !!token,
      user,
    };
  });

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await webodmApi.login(credentials);
      const { token } = response;

      // ローカルストレージに保存
      localStorage.setItem('token', token);

      // 状態を更新
      setAuthState({
        token,
        isAuthenticated: true,
        user: null, // WebODMはuser情報を返さないため
      });
    } catch (error) {
      console.error('ログインエラー:', error);
      throw error;
    }
  };

  const logout = () => {
    // ローカルストレージから削除
    localStorage.removeItem('token');
    localStorage.removeItem('user');

    // 状態を更新
    setAuthState({
      token: null,
      isAuthenticated: false,
      user: null,
    });
  };

  return (
    <AuthContext.Provider value={{ ...authState, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 