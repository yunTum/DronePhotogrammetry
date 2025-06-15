import React from 'react';
import { useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import ModelViewer from './components/ModelViewer';
import './App.css';

const App: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="App">
      {isAuthenticated ? <ModelViewer /> : <Login />}
    </div>
  );
};

export default App; 