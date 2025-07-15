import React, { useState, useEffect } from 'react';
import { useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import ModelViewer from './components/ModelViewer';
import GlbViewer from './components/GlbViewer';
import './App.css';

const App: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();
  const [currentPage, setCurrentPage] = useState<'login' | 'model' | 'glb'>('login');

  // ログイン済みの場合はModel Viewerを表示
  useEffect(() => {
    if (isAuthenticated && currentPage === 'login') {
      setCurrentPage('model');
    }
  }, [isAuthenticated, currentPage]);

  // JWTの有効性を定期的にチェック
  useEffect(() => {
    if (!isAuthenticated) return;

    const checkTokenValidity = async () => {
      try {
        // 簡単なAPI呼び出しでJWTの有効性をチェック
        const response = await fetch('/api/projects/', {
          headers: {
            'Authorization': `JWT ${localStorage.getItem('token')}`
          }
        });

        if (response.status === 401 || response.status === 403) {
          console.log('JWTが無効です。ログアウトします。');
          logout();
          setCurrentPage('login');
        }
      } catch (error) {
        console.error('JWT有効性チェックエラー:', error);
        // エラーの場合はログアウト
        logout();
        setCurrentPage('login');
      }
    };

    // 5分ごとにJWTの有効性をチェック
    const interval = setInterval(checkTokenValidity, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [isAuthenticated, logout]);

  const renderPage = () => {
    switch (currentPage) {
      case 'login':
        return <Login onGlbViewerClick={() => setCurrentPage('glb')} />;
      case 'model':
        return <ModelViewer />;
      case 'glb':
        return <GlbViewer />;
      default:
        return <Login onGlbViewerClick={() => setCurrentPage('glb')} />;
    }
  };

  return (
    <div className="App">
      {renderPage()}
    </div>
  );
};

export default App; 