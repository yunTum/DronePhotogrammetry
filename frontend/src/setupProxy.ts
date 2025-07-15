import { createProxyMiddleware } from 'http-proxy-middleware';
import { Express } from 'express';

// プロキシ設定
const setupProxy = (app: Express) => {
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:3000';
  
  console.log('プロキシ設定 - バックエンドURL:', backendUrl);
  
  // WebODM API用のプロキシ（バックエンド経由）
  app.use(
    '/api',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
      secure: false,
    })
  );

  // 認証API用のプロキシ（バックエンド経由）
  app.use(
    '/auth',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
      secure: false,
    })
  );
};

export default setupProxy; 