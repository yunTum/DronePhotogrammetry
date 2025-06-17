import React, { useState, useEffect, Suspense } from 'react';
import { useDropzone } from 'react-dropzone';
import { Canvas } from '@react-three/fiber';
import { TrackballControls } from '@react-three/drei';
import { Project, Task } from '../types';
import { webodmApi } from '../api/webodm';
import { Model } from './Model';
import './ModelViewer.css';
interface SelectedTask {
  projectId: number;
  taskId: string;
}

const ModelViewer: React.FC = () => {
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [currentProject, setCurrentProject] = useState<{ id: number; taskId: string } | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedTask, setSelectedTask] = useState<SelectedTask | null>(null);
  const [modelLoading, setModelLoading] = useState<boolean>(false);

  // プロジェクト一覧の取得
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await webodmApi.getProjects();
        // 各プロジェクトのタスク情報を取得
        const projectsWithTasks = await Promise.all(
          response.map(async (project) => {
            const tasks = await webodmApi.getTasks(project.id);
            return {
              ...project,
              tasks: tasks
            };
          })
        );

        // 進行中のタスクを探す
        let foundRunningTask = false;
        for (const project of projectsWithTasks) {
          const runningTask = project.tasks.find(task => task.status === 20);
          if (runningTask) {
            console.log('進行中のタスクを発見:', runningTask);
            setCurrentProject({ id: project.id, taskId: runningTask.id });
            setLoading(true);
            foundRunningTask = true;
            break;
          }
        }

        if (!foundRunningTask) {
          console.log('進行中のタスクが見つかりません');
        }

        setProjects(projectsWithTasks);
      } catch (err) {
        console.error('プロジェクト一覧の取得に失敗しました:', err);
        setError('プロジェクト一覧の取得に失敗しました');
      }
    };

    fetchProjects();
  }, []);

  // 進行状況の監視
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const checkProgress = async () => {
      if (!currentProject) return;

      try {
        console.log('進捗状況を確認中...', currentProject);
        const status = await webodmApi.getTaskStatus(currentProject.id, currentProject.taskId);
        console.log('タスクステータス:', status);

        // 進捗状況を更新
        const newProgress = status.running_progress;
        console.log('新しい進捗状況:', newProgress);
        setProgress(newProgress);

        if (Number(status.status) === 40) {
          console.log('タスク完了を検出');
          clearInterval(intervalId); // 先にインターバルを停止
          const modelUrl = webodmApi.getModelUrl(currentProject.id, currentProject.taskId);
          setModelUrl(modelUrl);
          setLoading(false);
          setCurrentProject(null);
          // プロジェクト一覧を更新
          const updatedProject = await webodmApi.getProject(currentProject.id);
          setProjects(prev => {
            console.log('プロジェクト一覧を更新:', updatedProject);
            return prev.map(p => p.id === updatedProject.id ? updatedProject : p);
          });
          return; // 処理を終了
        } else if (Number(status.status) === 20) {
          console.log('タスク進行中');
          setLoading(true);
        } else if (Number(status.status) === 30) {
          console.log('タスク失敗を検出');
          clearInterval(intervalId); // 先にインターバルを停止
          setError('モデルの生成に失敗しました');
          setLoading(false);
          setCurrentProject(null);
          return; // 処理を終了
        }
      } catch (err) {
        console.error('進行状況の確認に失敗しました:', err);
        clearInterval(intervalId); // 先にインターバルを停止
        setError('進行状況の確認に失敗しました');
        setLoading(false);
        setCurrentProject(null);
        return; // 処理を終了
      }
    };

    if (loading && currentProject) {
      console.log('進捗監視を開始:', currentProject);
      // 即座に最初のチェックを実行
      checkProgress();
      // 2秒ごとに進捗を更新
      intervalId = setInterval(checkProgress, 2000);
    }

    return () => {
      if (intervalId) {
        console.log('進捗監視を停止');
        clearInterval(intervalId);
      }
    };
  }, [loading, currentProject]);

  const handleTaskSelect = async (projectId: number, taskId: string) => {
    setModelLoading(true);
    setError(null);
    setModelUrl(null); // 既存のモデルをクリア

    try {
      // タスクの状態を確認
      const taskStatus = await webodmApi.getTaskStatus(projectId, taskId);
      console.log('タスクステータス:', taskStatus); // デバッグ用

      if (!isTaskCompleted(Number(taskStatus.status))) {
        throw new Error('タスクが完了していません');
      }

      // モデルURLを取得
      const modelUrl = webodmApi.getModelUrl(projectId, taskId);
      console.log('モデルURL:', modelUrl); // デバッグ用

      // JWTトークンを取得
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('認証トークンが見つかりません');
      }

      // URLの有効性を確認
      const response = await fetch(modelUrl, {
        method: 'HEAD',
        headers: {
          'Authorization': `JWT ${token}`
        }
      });
      console.log('モデル response:', response);
      if (!response.ok) {
        throw new Error(`モデルファイルが見つかりません: ${response.status}`);
      }

      setModelUrl(modelUrl);
      setSelectedTask({ projectId, taskId });
    } catch (err) {
      console.error('モデル取得エラー:', err); // デバッグ用
      setError(err instanceof Error ? err.message : '3Dモデルの取得に失敗しました');
    } finally {
      setModelLoading(false);
    }
  };

  const onDrop = async (acceptedFiles: File[]) => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      // 既存のプロジェクトを取得
      const existingProjects = await webodmApi.getProjects();
      let project;

      if (existingProjects.length > 0) {
        // 最新のプロジェクトを使用
        project = existingProjects[0];
        console.log('既存のプロジェクトを使用:', project.name);
      } else {
        // プロジェクトが存在しない場合は新規作成
        const newProject = await webodmApi.createProject('New Project');
        // プロジェクトの詳細情報を取得
        project = await webodmApi.getProject(newProject.id);
        console.log('新規プロジェクトを作成:', project.name);
      }
      
      // タスク作成（ファイルアップロードを含む）
      const task = await webodmApi.createTask(project.id, acceptedFiles, {
        'orthophoto-resolution': 2,
        'pc-quality': 'medium',
        'mesh-quality': 'medium',
      });

      console.log('タスクを作成:', task);
      setCurrentProject({ id: project.id, taskId: task.id });
    } catch (err) {
      console.error('モデル生成エラー:', err);
      setError('モデルの生成中にエラーが発生しました');
      setLoading(false);
    }
  };

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png'],
      'video/*': ['.mp4', '.mov']
    }
  });

  const getTaskStatus = (status: number): string => {
    switch (status) {
      case 10:
        return 'QUEUED';
      case 20:
        return 'RUNNING';
      case 40:
        return 'COMPLETED';
      case 30:
        return 'FAILED';
      case 50:
        return 'CANCELED';
      default:
        return `ステータス: ${status}`;
    }
  };

  const isTaskCompleted = (status: number): boolean => {
    return status === 40;
  };

  const getTaskProgress = (progress: number): number => {
    if (typeof progress !== 'number' || isNaN(progress)) {
      return 0;
    }
    return Math.min(Math.max(Math.round(progress), 0), 100);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Photogrammetry Viewer</h1>
      </header>

      <main>
        <div className="projects-section">
          <div className="projects-list">
            <h2 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Project List</h2>
            {projects.map(project => (
              <div key={project.id} className="project-item" style={{ marginBottom: '0.5rem' }}>
                <h3 style={{ fontSize: '1rem', margin: '0.2rem 0' }}>{project.name}</h3>
                <p style={{ fontSize: '0.7rem', margin: '0.1rem 0' }}>作成日: {new Date(project.created_at).toLocaleString()}</p>
                {project.tasks?.map((task: Task) => (
                  <div key={task.id} className="task-item" style={{ margin: '0.2rem 0' }}>
                    <div className="task-info">
                      <p className="task-header" style={{ fontSize: '0.6rem', margin: '0.1rem 0' }}>タスクID {task.id}</p>
                      <div className="task-stats" style={{ fontSize: '0.8rem', margin: '0.1rem 0' }}>
                        <p style={{ margin: '0.1rem 0' }}>進捗: {getTaskProgress(task.progress)}% | {getTaskStatus(Number(task.status))}</p>
                        <p style={{ margin: '0.1rem 0' }}>処理時間: {task.processing_time ? `${Math.round(task.processing_time / (1000 * 60))}分` : '未計測'} | 画像数: {task.images_count}</p>
                        <p style={{ margin: '0.1rem 0' }}>使用容量: {task.size ? `${task.size.toFixed(2)} MB` : '未計測'}</p>
                      </div>
                      <div className="progress-bar" style={{ height: '0.5rem', margin: '0.2rem 0' }}>
                        <div 
                          className="progress-bar-fill" 
                          style={{ width: `${getTaskProgress(task.progress)}%` }}
                        />
                      </div>
                    </div>
                    {isTaskCompleted(Number(task.status)) && (
                      <button
                        onClick={() => handleTaskSelect(project.id, task.id)}
                        disabled={modelLoading}
                        style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem' }}
                      >
                        {modelLoading && selectedTask?.taskId === task.id ? '読み込み中...' : '表示'}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>

          <div {...getRootProps()} className="dropzone">
            <input {...getInputProps()} />
            <p>写真または動画をドラッグ＆ドロップ、またはクリックして選択</p>
          </div>
        </div>

        <div className="model-section">
          {loading && (
            <div className="progress-container">
              <p>モデルを生成中... {Math.round(progress * 100)}%</p>
              <div className="progress-bar">
                <div 
                  className="progress-bar-fill" 
                  style={{ width: `${progress * 100}%` }}
                />
              </div>
            </div>
          )}
          
          {modelUrl && !modelLoading && (
            <Canvas
              style={{ width: '100%', height: '100%' }}
              camera={{ 
                position: [3, 3, 3],
                fov: 45,
                near: 0.1,
                far: 1000
              }}
            >
              <Suspense fallback={null}>
                <ambientLight intensity={0.5} />
                <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} />
                <Model url={modelUrl} />
                <TrackballControls
                  enableDamping
                  dampingFactor={0.05}
                  rotateSpeed={2.5}
                  zoomSpeed={1.2}
                  panSpeed={0.8}
                  minDistance={0.1}
                  maxDistance={100}
                  dynamicDampingFactor={0.2}
                  noPan={false}
                  noZoom={false}
                  noRotate={false}
                  staticMoving={false}
                  center={[0, 0, 0]}
                  handleKeys={{
                    LEFT: 'ArrowLeft',
                    UP: 'ArrowUp',
                    RIGHT: 'ArrowRight',
                    BOTTOM: 'ArrowDown',
                    ROTATE: 'ControlLeft'
                  }}
                />
              </Suspense>
            </Canvas>
          )}

          {modelLoading && (
            <div className="loading-overlay">
              <p>3Dモデルを読み込み中...</p>
            </div>
          )}

          {error && (
            <div className="error-message">
              <p>{error}</p>
              <button onClick={() => setError(null)}>閉じる</button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ModelViewer; 