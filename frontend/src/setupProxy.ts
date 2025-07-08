import { createProxyMiddleware } from 'http-proxy-middleware';
import { Express } from 'express';

// プロキシ設定
const setupProxy = (app: Express) => {
  const proxyUrl = process.env.REACT_APP_PROXY_URL || 'http://localhost:8000';
  
  app.use(
    '/api',
    createProxyMiddleware({
      target: proxyUrl,
      changeOrigin: true,
      secure: true,
    })
  );
};

export default setupProxy; 