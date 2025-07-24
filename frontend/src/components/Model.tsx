import React, { useEffect, useState, useRef } from 'react';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';

interface ModelProps {
  url: string;
  onError?: (error: string) => void;
}

export const Model: React.FC<ModelProps> = ({ url, onError }) => {
  const { scene } = useThree();
  const [model, setModel] = useState<THREE.Object3D | null>(null);
  const token = localStorage.getItem('token');
  const loaderRef = useRef<GLTFLoader | null>(null);

  // ジオメトリの検証と修正を行う関数
  const validateAndFixGeometry = (object: THREE.Object3D) => {
    object.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const geometry = child.geometry;
        
        // 位置属性の検証
        if (geometry.attributes.position) {
          const positions = geometry.attributes.position.array;
          let hasNaN = false;
          
          // NaNの値を0に置き換え
          for (let i = 0; i < positions.length; i++) {
            if (isNaN(positions[i])) {
              positions[i] = 0;
              hasNaN = true;
            }
          }
          
          if (hasNaN) {
            console.warn('ジオメトリのNaN値を修正しました');
            geometry.attributes.position.needsUpdate = true;
          }
        }

        // 法線の再計算
        if (geometry.attributes.normal) {
          geometry.computeVertexNormals();
        }

        // バウンディングスフィアの再計算
        geometry.computeBoundingSphere();
        geometry.computeBoundingBox();
      }
    });
  };

  useEffect(() => {
    if (!token) {
      onError?.('認証トークンが見つかりません');
      return;
    }

    let isMounted = true;

    // GLBファイルをダウンロードして読み込み
    const downloadAndLoadModel = async () => {
      try {
        console.log('モデルのダウンロードを開始:', url);

        if (!token) {
          throw new Error('認証トークンが見つかりません');
        }

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `JWT ${token}`,
            'Accept': 'application/json, model/gltf-binary, */*',
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          mode: 'cors'
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('サーバーレスポンス:', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            body: errorText
          });
          throw new Error(`モデルの取得に失敗しました: ${response.status} ${response.statusText}\n${errorText}`);
        }

        // GLBファイルの内容を取得
        const glbBuffer = await response.arrayBuffer();
        
        if (!isMounted) return;

        // GLBファイルをロード
        await loadModel(glbBuffer);

      } catch (error) {
        console.error('モデルの読み込みに失敗しました:', error);
        if (isMounted) {
          const errorMessage = error instanceof Error ? error.message : 'モデルの読み込みに失敗しました';
          onError?.(errorMessage);
        }
      }
    };

    downloadAndLoadModel();

    return () => {
      isMounted = false;
    };
  }, [url, token, onError]);

  const loadModel = async (glbBuffer: ArrayBuffer) => {
    try {
      if (!loaderRef.current) {
        loaderRef.current = new GLTFLoader();
      }

      // GLBファイルの内容からオブジェクトを作成
      const gltf = await new Promise<any>((resolve, reject) => {
        loaderRef.current!.parse(
          glbBuffer,
          '',
          (gltf) => resolve(gltf),
          (error) => reject(error)
        );
      });

      const object = gltf.scene;
      
      // ジオメトリの検証と修正
      validateAndFixGeometry(object);

      // シーンに追加
      if (model) {
        scene.remove(model);
      }
      
      scene.add(object);
      setModel(object);

      console.log('GLBモデルの読み込みが完了しました');

    } catch (error) {
      console.error('モデルの読み込みエラー:', error);
      onError?.('モデルの読み込みに失敗しました');
    }
  };

  // モデルが読み込まれている場合は表示
  return model ? <primitive object={model} /> : null;
}; 