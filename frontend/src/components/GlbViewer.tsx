import React, { useState, useRef, Suspense } from 'react';
import { useDropzone } from 'react-dropzone';
import { Canvas } from '@react-three/fiber';
import { TrackballControls } from '@react-three/drei';
import { GlbModel } from './GlbModel';
import './ModelViewer.css';
import { Box, Button, Heading, Text } from "@chakra-ui/react";

const GlbViewer: React.FC = () => {
  const [glbUrl, setGlbUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    if (!file.name.toLowerCase().endsWith('.glb')) {
      setError('GLBファイルを選択してください');
      return;
    }

    setError(null);
    
    // GLBファイルをBlobURLとして設定
    const glbObjectUrl = URL.createObjectURL(file);
    setGlbUrl(glbObjectUrl);
    console.log('GLBファイルを読み込みました:', file.name);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'model/gltf-binary': ['.glb']
    },
    multiple: false
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      onDrop(Array.from(files));
    }
  };

  return (
    <Box className="App">
      <Box className="App-header" style={{ padding: '10px 20px' }}>
        <Heading style={{ margin: '0 0 5px 0', fontSize: '1.5rem' }}>GLB Viewer</Heading>
        <Text style={{ margin: 0, fontSize: '0.9rem', color: '#b0b0b0' }}>GLBファイルをドラッグ＆ドロップして表示</Text>
      </Box>

      <Box className="model-section" style={{ 
          flex: 1, 
          minHeight: 0,
          backgroundColor: '#1a1d24',
          borderRadius: '8px',
          border: '1px solid #2c303a',
          overflow: 'hidden'
        }}>
          {glbUrl && (
            <Canvas
              style={{ 
                width: '100%', 
                height: '100%',
                background: 'linear-gradient(135deg, #1a1d24 0%, #2c303a 100%)'
              }}
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
                <GlbModel url={glbUrl} />
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

          {error && (
            <Box className="error-message">
              <Text>{error}</Text>
              <Button onClick={() => setError(null)}>閉じる</Button>
            </Box>
          )}
        </Box>

      <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </Box>
  );
};

export default GlbViewer; 