import React, { useEffect, useState } from 'react';
import { Box, Text, TableRoot, TableHeader, TableBody, TableRow, TableColumnHeader, TableCell, Badge, Button, Input, VStack, Image, Heading } from '@chakra-ui/react';
import { webodmApi } from '../api/webodm';
import { Project, Task } from '../types';
import Header from './Header';

interface ProjectTablePageProps {
  onGoModel: () => void;
}

const statusColor = (status: number) => {
  switch (status) {
    case 10: return 'gray'; // QUEUED
    case 20: return 'blue'; // RUNNING
    case 40: return 'green'; // COMPLETED
    case 30: return 'red'; // FAILED
    case 50: return 'orange'; // CANCELED
    default: return 'gray';
  }
};

const statusLabel = (status: number) => {
  switch (status) {
    case 10: return '待機中';
    case 20: return '処理中';
    case 40: return '完了';
    case 30: return '失敗';
    case 50: return 'キャンセル';
    default: return `ステータス: ${status}`;
  }
};

const ProjectTablePage: React.FC<ProjectTablePageProps> = ({ onGoModel }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectImages, setNewProjectImages] = useState<File[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoading(true);
        const response = await webodmApi.getProjects();
        const projectsWithTasks = await Promise.all(
          response.map(async (project) => {
            const tasks = await webodmApi.getTasks(project.id);
            return { ...project, tasks };
          })
        );
        setProjects(projectsWithTasks);
      } catch (err) {
        setError('プロジェクト一覧の取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  return (
    <Box className="App" minH="100vh" bg="gray.900">
      <Header
        title="マイページ"
        leftButtonText="モデルビューア"
        onLeftButtonClick={onGoModel}
        rightButtonText="ログアウト"
        onRightButtonClick={() => { localStorage.removeItem('token'); window.location.reload(); }}
      />
      <Box maxW="1500px" mx="auto" mt={0} p={4} bg="gray.800" borderRadius="xl" boxShadow="2xl">
        <Box display="flex" justifyContent="flex-end" alignItems="center" mb={2}>
          <Button colorScheme="teal" onClick={() => setDialogOpen(true)} width="300px">
            新規作成
          </Button>
        </Box>
        {dialogOpen && (
          <Box position="fixed" top={0} left={0} w="100vw" h="100vh" bg="rgba(0,0,0,0.7)" zIndex={1000} display="flex" alignItems="center" justifyContent="center">
            <Box bg="gray.900" color="white" p={8} borderRadius="lg" boxShadow="2xl" minW="350px" maxW="90vw" position="relative">
              <Button position="absolute" top={2} right={2} variant="ghost" color="white" onClick={() => setDialogOpen(false)}>×</Button>
              <Heading size="md" mb={4}>新規モデル作成</Heading>
              <VStack gap={4} align="stretch">
                <Box>
                  <Text mb={1}>タスク名</Text>
                  <Input
                    placeholder="タスク名を入力"
                    value={newProjectName}
                    onChange={e => setNewProjectName(e.target.value)}
                    bg="gray.700"
                    color="white"
                  />
                </Box>
                <Box textAlign="center">
                  <Text mb={1}>画像</Text>
                  <Box
                    display="flex"
                    flexDirection="column"
                    alignItems="center"
                    justifyContent="center"
                    border="2px dashed #319795"
                    borderRadius="md"
                    bg="gray.700"
                    p={4}
                    mb={2}
                  >
                    <Button
                      as="label"
                      colorScheme="teal"
                      variant="outline"
                      cursor="pointer"
                      mb={2}
                    >
                      ファイルを選択
                      <Input
                        type="file"
                        accept="image/*"
                        multiple
                        display="none"
                        onChange={e => {
                          if (e.target.files && e.target.files.length > 0) {
                            const files = Array.from(e.target.files);
                            setNewProjectImages(files);
                            setPreviewUrl(URL.createObjectURL(files[0]));
                          } else {
                            setNewProjectImages([]);
                            setPreviewUrl(null);
                          }
                        }}
                      />
                    </Button>
                    <Text fontSize="sm" color="gray.300">
                      {newProjectImages.length > 0
                        ? `${newProjectImages.length} ファイル選択済み`
                        : '画像ファイルを選択してください（複数可）'}
                    </Text>
                    {previewUrl && (
                      <Image src={previewUrl} alt="preview" maxH="120px" mt={3} borderRadius="md" boxShadow="md" />
                    )}
                  </Box>
                </Box>
              </VStack>
              <Box display="flex" justifyContent="flex-end" gap={2} mt={6}>
                <Button variant="ghost" onClick={() => setDialogOpen(false)}>キャンセル</Button>
                <Button
                  colorScheme="teal"
                  loading={uploading}
                  onClick={async () => {
                    if (!newProjectName || newProjectImages.length === 0) return;
                    setUploading(true);
                    try {
                      // プロジェクト作成API呼び出し例
                      // const newProject = await webodmApi.createProject(newProjectName);
                      // await webodmApi.uploadProjectImages(newProject.id, newProjectImages);
                      // プロジェクト一覧を再取得
                      // const response = await webodmApi.getProjects();
                      // setProjects(response);
                      // 仮実装: 成功したら閉じる
                      setDialogOpen(false);
                      setNewProjectName('');
                      setNewProjectImages([]);
                      setPreviewUrl(null);
                    } finally {
                      setUploading(false);
                    }
                  }}
                  disabled={!newProjectName || newProjectImages.length === 0}
                >
                  作成
                </Button>
              </Box>
            </Box>
          </Box>
        )}
        <TableRoot>
          <TableHeader>
            <TableRow bg="teal.700">
              <TableColumnHeader color="white" fontWeight="bold">プロジェクト名</TableColumnHeader>
              <TableColumnHeader color="white" fontWeight="bold">作成日</TableColumnHeader>
              <TableColumnHeader color="white" fontWeight="bold">モデル名</TableColumnHeader>
              <TableColumnHeader color="white" fontWeight="bold">進捗</TableColumnHeader>
              <TableColumnHeader color="white" fontWeight="bold">ステータス</TableColumnHeader>
              <TableColumnHeader color="white" fontWeight="bold">画像数</TableColumnHeader>
              <TableColumnHeader color="white" fontWeight="bold">容量</TableColumnHeader>
            </TableRow>
          </TableHeader>
          <TableBody>
            {projects.map((project) => (
              Array.isArray(project.tasks) && project.tasks.length > 0 ? (
                project.tasks.map((task: Task, idx: number) => (
                  <TableRow
                    key={`${project.id}-${task.id}`}
                    _hover={{ bg: 'teal.900', color: 'white', transition: 'all 0.2s' }}
                    bg={idx % 2 === 0 ? 'gray.700' : 'gray.800'}
                  >
                    {idx === 0 && (
                      <TableCell rowSpan={Array.isArray(project.tasks) ? project.tasks.length : 1} fontWeight="bold" fontSize="md" color="teal.200" bg="gray.900" borderLeft="4px solid #319795">
                        {project.name}
                      </TableCell>
                    )}
                    {idx === 0 && (
                      <TableCell rowSpan={Array.isArray(project.tasks) ? project.tasks.length : 1} fontSize="sm" color="gray.200" bg="gray.900">
                        {new Date(project.created_at).toLocaleString()}
                      </TableCell>
                    )}
                    <TableCell fontWeight="bold" color="cyan.200">{task.name}</TableCell>
                    <TableCell minW={120}>
                      <Box bg="gray.600" borderRadius="md" w="100%" h="8px" position="relative">
                        <Box bgGradient="linear(to-r, teal.300, cyan.400)" borderRadius="md" h="8px" w={`${typeof task.progress === 'number' ? task.progress : 0}%`} transition="width 0.3s" />
                      </Box>
                      <Text fontSize="xs" color="gray.100" mt={1}>{typeof task.progress === 'number' ? `${Math.round(task.progress)}%` : '-'}</Text>
                    </TableCell>
                    <TableCell>
                      <Badge colorScheme={statusColor(Number(task.status))} fontSize="0.9em" px={2} py={1} borderRadius="md" bg={statusColor(Number(task.status)) === 'green' ? 'green.500' : statusColor(Number(task.status)) === 'blue' ? 'blue.500' : statusColor(Number(task.status)) === 'red' ? 'red.500' : statusColor(Number(task.status)) === 'orange' ? 'orange.500' : 'gray.600'} color="white">
                        {statusLabel(Number(task.status))}
                      </Badge>
                    </TableCell>
                    <TableCell color="white">{task.images_count}</TableCell>
                    <TableCell color="white">{task.size ? `${task.size.toFixed(2)} MB` : '-'}</TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow key={project.id} bg="gray.700">
                  <TableCell fontWeight="bold" fontSize="md" color="teal.200" bg="gray.900" borderLeft="4px solid #319795">
                    {project.name}
                  </TableCell>
                  <TableCell fontSize="sm" color="gray.200" bg="gray.900">
                    {new Date(project.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell colSpan={5} textAlign="center" color="gray.400" bg="gray.700">タスクなし</TableCell>
                </TableRow>
              )
            ))}
          </TableBody>
        </TableRoot>
      </Box>
    </Box>
  );
};

export default ProjectTablePage; 