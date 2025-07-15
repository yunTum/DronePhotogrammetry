import React, { useEffect, useState, useRef } from 'react';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';

interface GlbModelProps {
  url: string;
}

export const GlbModel: React.FC<GlbModelProps> = ({ url }) => {
  const { scene } = useThree();
  const [error, setError] = useState<string | null>(null);
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
    let isMounted = true;

    const loadGlbModel = async () => {
      try {
        console.log('GLBモデルの読み込みを開始:', url);

        let response: Response;
        
        // URLがBlobURLの場合は直接使用
        if (url.startsWith('blob:')) {
          response = await fetch(url);
        } else {
          // 外部URLの場合は認証トークンを使用
          if (!token) {
            setError('認証トークンが見つかりません');
            return;
          }

          response = await fetch(url, {
            method: 'GET',
            headers: {
              'Authorization': `JWT ${token}`,
              'Accept': 'application/json, application/octet-stream, */*',
              'Content-Type': 'application/json'
            },
            credentials: 'include',
            mode: 'cors'
          });
        }

        if (!response.ok) {
          const errorText = await response.text();
          console.error('サーバーレスポンス:', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            body: errorText
          });
          throw new Error(`GLBモデルの取得に失敗しました: ${response.status} ${response.statusText}\n${errorText}`);
        }

        // レスポンスをArrayBufferとして取得
        const arrayBuffer = await response.arrayBuffer();
        console.log('GLBファイルのダウンロードが完了:', arrayBuffer.byteLength, 'bytes');

        if (arrayBuffer.byteLength === 0) {
          throw new Error('ダウンロードされたGLBファイルが空です');
        }

        // GLTFLoaderの初期化
        if (!loaderRef.current) {
          loaderRef.current = new GLTFLoader();
        }

        // GLBファイルを読み込む
        const gltf = await new Promise<any>((resolve, reject) => {
          loaderRef.current?.parse(
            arrayBuffer,
            '',
            (gltf) => {
              console.log('GLBファイルの解析が完了');
              console.log('シーン数:', gltf.scenes?.length || 0);
              console.log('アニメーション数:', gltf.animations?.length || 0);
              console.log('アセット:', gltf.asset);
              resolve(gltf);
            },
            (error) => {
              console.error('GLBファイルの解析に失敗:', error);
              reject(error);
            }
          );
        });

        if (!isMounted) return;

        const object = gltf.scene;
        
        // ジオメトリの検証と修正
        validateAndFixGeometry(object);

        // モデルのスケールを調整
        const box = new THREE.Box3().setFromObject(object);
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 2 / maxDim;
        object.scale.set(scale, scale, scale);

        // モデルを中央に配置
        const center = box.getCenter(new THREE.Vector3());
        object.position.sub(center.multiplyScalar(scale));

        // モデルの向きを調整
        const quaternion = new THREE.Quaternion();
        quaternion.setFromEuler(new THREE.Euler(0, 0, 0));
        object.quaternion.copy(quaternion);

        setModel(object);
        scene.add(object);
        console.log('GLBモデルの設定が完了');

        // アニメーションがある場合は再生
        if (gltf.animations && gltf.animations.length > 0) {
          console.log('アニメーションを再生:', gltf.animations.length, '個');
          // アニメーションの再生処理をここに追加
        }

      } catch (err) {
        if (isMounted) {
          console.error('GLBモデルの読み込みに失敗しました:', err);
          setError(err instanceof Error ? err.message : 'GLBモデルの読み込みに失敗しました');
        }
      }
    };

    loadGlbModel();

    return () => {
      isMounted = false;
    };
  }, [url, token, scene]);

  useEffect(() => {
    return () => {
      if (model) {
        scene.remove(model);
      }
    };
  }, [model, scene]);

  if (error) {
    return (
      <mesh>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color="red" />
      </mesh>
    );
  }

  return model ? <primitive object={model} /> : null;
}; 