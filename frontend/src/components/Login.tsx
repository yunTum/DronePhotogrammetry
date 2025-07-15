import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LoginCredentials } from '../types';

interface LoginProps {
  onGlbViewerClick: () => void;
}

const Login: React.FC<LoginProps> = ({ onGlbViewerClick }) => {
  const [credentials, setCredentials] = useState<LoginCredentials>({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      await login(credentials);
    } catch (err) {
      setError('ログインに失敗しました。ユーザー名とパスワードを確認してください。');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form">
        <h2>WebODMログイン</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="form-group">
          <label htmlFor="username">ユーザー名</label>
          <input
            type="text"
            id="username"
            name="username"
            value={credentials.username}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">パスワード</label>
          <input
            type="password"
            id="password"
            name="password"
            value={credentials.password}
            onChange={handleChange}
            required
          />
        </div>

        <button type="submit" className="login-button">
          ログイン
        </button>
      </form>
      
      <div className="glb-viewer-section" style={{
        marginTop: '20px',
        textAlign: 'center',
        padding: '20px',
        borderTop: '1px solid #ddd'
      }}>
        <p style={{ marginBottom: '15px', color: '#666' }}>
          ログインせずにGLBビューアを使用する
        </p>
        <button 
          onClick={onGlbViewerClick}
          style={{
            padding: '10px 20px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          GLBビューアを開く
        </button>
      </div>
    </div>
  );
};

export default Login; 