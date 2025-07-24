import React, { useState, useEffect, Suspense } from 'react';
import { useDropzone } from 'react-dropzone';
import { Canvas } from '@react-three/fiber';
import { TrackballControls } from '@react-three/drei';
import { Project, Task } from '../types';
import { webodmApi } from '../api/webodm';
import { Model } from './Model';
import { useAuth } from '../contexts/AuthContext';
import './ModelViewer.css';
import { Box, Button, Input, Heading, VStack, Text, Flex } from "@chakra-ui/react";
import Header from './Header';

interface SelectedTask {
  projectId: number;
  taskId: string;
}
interface ModelViewerProps {
  onGoMypage: () => void;
}

const ModelViewer: React.FC<ModelViewerProps> = ({ onGoMypage }) => {
  const { logout } = useAuth();
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [currentProject, setCurrentProject] = useState<{ id: number; taskId: string } | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedTask, setSelectedTask] = useState<SelectedTask | null>(null);
  const [modelLoading, setModelLoading] = useState<boolean>(false);
  const [modelError, setModelError] = useState<string | null>(null);

  const handleLogout = () => {
    logout();
    // ページをリロードしてログイン画面に遷移
    window.location.reload();
  };

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
          const modelUrl = await webodmApi.getModel(currentProject.id, currentProject.taskId);
          setModelUrl(modelUrl);
          setLoading(false);
          setCurrentProject(null);
          // プロジェクト一覧を最新化
          const projectsWithTasks = await webodmApi.getProjects().then(async (response) => {
            return Promise.all(
              response.map(async (project) => {
                const tasks = await webodmApi.getTasks(project.id);
                return { ...project, tasks };
              })
            );
          });
          setProjects(projectsWithTasks);
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
      // 5秒ごとに進捗を更新
      intervalId = setInterval(checkProgress, 5000);
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
      const modelUrl = await webodmApi.getModel(projectId, taskId);
      console.log('モデルURL:', modelUrl); // デバッグ用

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
        'orthophoto-resolution': '2',
        'pc-quality': 'medium',
        'mesh-quality': 'medium',
      });

      console.log('タスクを作成:', task);
      setCurrentProject({ id: project.id, taskId: task.id });
      // プロジェクト一覧を最新化
      const projectsWithTasks = await webodmApi.getProjects().then(async (response) => {
        return Promise.all(
          response.map(async (project) => {
            const tasks = await webodmApi.getTasks(project.id);
            return { ...project, tasks };
          })
        );
      });
      setProjects(projectsWithTasks);
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
        return '待機中（QUEUED）';
      case 20:
        return '処理中（RUNNING）';
      case 40:
        return '完了（COMPLETED）';
      case 30:
        return '失敗（FAILED）';
      case 50:
        return 'キャンセル（CANCELED）';
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
    <Box className="App" minH="100vh" bg="gray.900">
      <Header
        title="Photogrammetry Viewer"
        leftButtonText="マイページ"
        onLeftButtonClick={onGoMypage}
        rightButtonText="ログアウト"
        onRightButtonClick={handleLogout}
      />

      <Flex className="main-content" width="100%" height="calc(100vh - 80px)">
        {/* 左カラム: プロジェクトリスト */}
        <Box minW="340px" maxW="400px" width="25%" p={4} bg="gray.800" borderRight="1px solid #2d3748" overflowY="auto">
          <VStack gap={4} align="stretch" width="100%">
            <Box className="projects-section">
              <Heading size="md" mb="0.5rem" bg="gray.800" color="teal.200" p={2} borderRadius="md">Project List</Heading>
              {projects.map(project => (
                <Box
                  key={project.id}
                  className="project-item"
                  p={3}
                  mb={3}
                  bg="gray.700"
                  borderRadius="lg"
                  boxShadow="md"
                  _hover={{ boxShadow: "xl", bg: "gray.600", transform: "translateY(-2px) scale(1.02)", transition: "all 0.2s" }}
                  transition="all 0.2s"
                >
                  <Heading size="sm" mb={1} color="teal.200" fontWeight="bold" letterSpacing="wide">{project.name}</Heading>
                  <Text fontSize="xs" mb={2} color="gray.300">作成日: {new Date(project.created_at).toLocaleString()}</Text>
                  <Box>
                    {project.tasks?.map((task: Task, idx) => (
                      <Box
                        key={task.id}
                        className="task-item"
                        p={3}
                        borderRadius="md"
                        bg="gray.800"
                        mb={idx !== project.tasks!.length - 1 ? 2 : 0}
                        boxShadow="sm"
                        display="flex"
                        flexDirection="column"
                        gap={2}
                        _hover={{
                          boxShadow: "md",
                          bg: "gray.700",
                          transform: "translateY(-2px) scale(1.01)",
                          transition: "all 0.2s"
                        }}
                        transition="all 0.2s"
                      >
                        <Text fontSize="sm" fontWeight="bold" color="teal.200" display="flex" alignItems="center" gap={1}>
                          <span style={{fontSize: '1.1em'}}>🗂️</span> {task.name}
                        </Text>
                        <Box className="task-stats" fontSize="sm" color="gray.100" pl={2}>
                          <Text mb={0.5} fontSize="xs">進捗: <b>{getTaskProgress(task.progress)}%</b> | {getTaskStatus(Number(task.status))}</Text>
                          <Text mb={0.5} fontSize="xs">処理時間: {task.processing_time ? `${Math.round(task.processing_time / (1000 * 60))}分` : '未計測'} | 画像数: {task.images_count}</Text>
                          <Text mb={0.5} fontSize="xs">使用容量: {task.size ? `${task.size.toFixed(2)} MB` : '未計測'}</Text>
                        </Box>
                        <Box className="progress-bar" height="0.5rem" borderRadius="full" bg="gray.600" overflow="hidden">
                          <Box
                            className="progress-bar-fill"
                            width={`${getTaskProgress(task.progress)}%`}
                            height="100%"
                            borderRadius="full"
                            bgGradient="linear(to-r, teal.300, cyan.400)"
                            transition="width 0.3s"
                          />
                        </Box>
                        {isTaskCompleted(Number(task.status)) && (
                          <Button
                            onClick={() => handleTaskSelect(project.id, task.id)}
                            disabled={modelLoading}
                            fontSize="sm"
                            colorScheme="teal"
                            variant="solid"
                            size="sm"
                            _hover={{ bg: "teal.400", color: "white" }}
                            alignSelf="flex-end"
                            mt={1}
                          >
                            {modelLoading && selectedTask?.taskId === task.id ? '読み込み中...' : '表示'}
                          </Button>
                        )}
                      </Box>
                    ))}
                  </Box>
                </Box>
              ))}
            </Box>

            <Box {...getRootProps()} className="dropzone" p="1rem" border="1px dashed" borderColor="gray.300" borderRadius="md" textAlign="center">
              <Input {...getInputProps()} type="file" multiple />
              <Text>写真または動画をドラッグ＆ドロップ、またはクリックして選択</Text>
            </Box>
          </VStack>
        </Box>

        {/* 右カラム: 3Dモデルビュー */}
        <Box flex={1} p={4} overflowY="auto" height="calc(100vh - 80px)" bg="gray.800">
          <VStack gap={4} align="stretch" width="100%" height="100%">
            <Box className="model-section" height="100%" position="relative">
              {loading && (
                <Box className="progress-container" p="0.5rem" borderRadius="md" bg="gray.700" border="1px solid" borderColor="gray.600">
                  <Text color="white">モデルを生成中... {Math.round(progress * 100)}%</Text>
                  <Box className="progress-bar" height="0.5rem" borderRadius="full" overflow="hidden" bg="gray.600">
                    <Box 
                      className="progress-bar-fill" 
                      height="100%" 
                      borderRadius="full" 
                      bgGradient="linear(to-r, teal.300, cyan.400)" 
                      width={`${Math.round(progress * 100)}%`}
                      transition="width 0.3s ease-in-out"
                    />
                  </Box>
                </Box>
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
                    <Model url={modelUrl} onError={setModelError} />
                    <TrackballControls
                      enableDamping
                      dampingFactor={0.05}
                      rotateSpeed={5.5}
                      zoomSpeed={1.2}
                      panSpeed={0.6}
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
                <Box
                  position="absolute"
                  top={0}
                  left={0}
                  width="100%"
                  height="100%"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  bg="rgba(0,0,0,0.6)"
                  zIndex={10}
                  borderRadius="md"
                >
                  <VStack gap={4}>
                    <Box as="span" className="chakra-spinner" boxSize={10} borderWidth={2} borderColor="teal.300" borderStyle="solid" borderRadius="full" borderTopColor="transparent" animation="spin 1s linear infinite" />
                    <Text color="white" fontWeight="bold" fontSize="lg">3Dモデルを読み込み中...</Text>
                  </VStack>
                </Box>
              )}
              {error && (
                <Box className="error-message" p="0.5rem 1rem" borderRadius="md" bg="red.100" border="1px solid" borderColor="red.200">
                  <Text>{error}</Text>
                  <Button onClick={() => setError(null)}>閉じる</Button>
                </Box>
              )}
              {modelError && (
                <Box className="error-message" p="0.5rem 1rem" borderRadius="md" bg="red.100" border="1px solid" borderColor="red.200">
                  <Text>モデルエラー: {modelError}</Text>
                  <Button onClick={() => setModelError(null)}>閉じる</Button>
                </Box>
              )}
            </Box>
          </VStack>
        </Box>
      </Flex>
    </Box>
  );
};

export default ModelViewer; 