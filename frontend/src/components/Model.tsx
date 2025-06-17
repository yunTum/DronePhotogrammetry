import React, { useEffect, useState, useRef } from 'react';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader';
import { MTLLoader } from 'three/examples/jsm/loaders/MTLLoader';
import * as THREE from 'three';
import JSZip from 'jszip';
import { useThree } from '@react-three/fiber';

interface ModelProps {
  url: string;
}

interface ZipFile {
  name: string;
  async: (type: string) => Promise<Blob>;
}

export const Model: React.FC<ModelProps> = ({ url }) => {
  const { scene } = useThree();
  const [error, setError] = useState<string | null>(null);
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [mtlUrl, setMtlUrl] = useState<string | null>(null);
  const [textureUrls, setTextureUrls] = useState<{ [key: string]: string }>({});
  const [model, setModel] = useState<THREE.Object3D | null>(null);
  const token = localStorage.getItem('token');
  const loaderRef = useRef<OBJLoader | null>(null);
  const mtlLoaderRef = useRef<MTLLoader | null>(null);

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
      setError('認証トークンが見つかりません');
      return;
    }

    let isMounted = true;

    // ZIPファイルをダウンロードして解凍
    const downloadAndExtract = async () => {
      try {
        console.log('モデルのダウンロードを開始:', url);

        if (!token) {
          throw new Error('認証トークンが見つかりません');
        }

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `JWT ${token}`,
            'Accept': 'application/json, application/zip, */*',
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

        // レスポンスをArrayBufferとして取得
        const arrayBuffer = await response.arrayBuffer();
        console.log('ZIPファイルのダウンロードが完了');
        const zipBlob = new Blob([arrayBuffer], { type: 'application/zip' });
        console.log('ZIPファイルのサイズ:', zipBlob.size);

        if (zipBlob.size === 0) {
          throw new Error('ダウンロードされたZIPファイルが空です');
        }

        const zip = new JSZip();
        console.log('ZIPファイルの解凍を開始');
        const zipContent = await zip.loadAsync(zipBlob);
        console.log('ZIPファイルの解凍が完了');

        // OBJファイルとMTLファイルを探す
        const objFile = Object.values(zipContent.files).find(file => 
          (file as ZipFile).name.endsWith('.obj')
        ) as ZipFile | undefined;
        const mtlFile = Object.values(zipContent.files).find(file => 
          (file as ZipFile).name.endsWith('.mtl')
        ) as ZipFile | undefined;

        if (!objFile || !mtlFile) {
          throw new Error('OBJファイルまたはMTLファイルが見つかりません');
        }

        console.log('OBJファイル:', objFile.name);
        console.log('MTLファイル:', mtlFile.name);

        // テクスチャファイルを探す
        const textureFiles = Object.values(zipContent.files).filter(file => {
          const fileName = (file as ZipFile).name;
          return fileName.endsWith('.png') || fileName.endsWith('.jpg');
        }) as ZipFile[];

        console.log('テクスチャファイル数:', textureFiles.length);
        console.log('テクスチャファイル一覧:', textureFiles.map(f => f.name));

        // ファイルを解凍してBlobURLを作成
        console.log('ファイルの解凍を開始');
        const objBlob = await objFile.async('blob');
        const mtlBlob = await mtlFile.async('blob');
        const textureBlobs = await Promise.all(
          textureFiles.map(file => file.async('blob'))
        );
        console.log('ファイルの解凍が完了');

        const objUrl = URL.createObjectURL(objBlob);
        const mtlUrl = URL.createObjectURL(mtlBlob);
        
        // テクスチャURLのマッピングを作成
        const textureUrlMap: { [key: string]: string } = {};
        textureFiles.forEach((file, index) => {
          const fileName = file.name;
          textureUrlMap[fileName] = URL.createObjectURL(textureBlobs[index]);
        });

        if (isMounted) {
          setModelUrl(objUrl);
          setMtlUrl(mtlUrl);
          setTextureUrls(textureUrlMap);
          console.log('モデルURLを設定:', objUrl);
          console.log('マテリアルURLを設定:', mtlUrl);
          console.log('テクスチャURLを設定:', textureUrlMap);
        }

        return () => {
          URL.revokeObjectURL(objUrl);
          URL.revokeObjectURL(mtlUrl);
          Object.values(textureUrlMap).forEach(url => URL.revokeObjectURL(url));
        };
      } catch (err) {
        if (isMounted) {
          console.error('モデルの読み込みに失敗しました:', err);
          setError(err instanceof Error ? err.message : 'モデルの読み込みに失敗しました');
        }
      }
    };

    downloadAndExtract();

    return () => {
      isMounted = false;
      if (modelUrl) {
        URL.revokeObjectURL(modelUrl);
      }
      if (mtlUrl) {
        URL.revokeObjectURL(mtlUrl);
      }
      Object.values(textureUrls).forEach(url => URL.revokeObjectURL(url));
    };
  }, [url, token]);

  useEffect(() => {
    if (!modelUrl || !mtlUrl) return;

    if (!loaderRef.current) {
      loaderRef.current = new OBJLoader();
    }

    const loadModel = async () => {
      try {
        console.log('マテリアルの読み込みを開始:', mtlUrl);
        // MTLファイルの内容を取得
        const mtlResponse = await fetch(mtlUrl);
        const mtlContent = await mtlResponse.text();
        console.log('MTLファイルの内容:', mtlContent);

        // マテリアルを作成
        const materialMap: { [key: string]: THREE.Material } = {};

        // MTLファイルの内容を解析
        const lines = mtlContent.split('\n');
        let currentMaterial: string | null = null;
        const texturePromises: Promise<void>[] = [];

        for (const line of lines) {
          const parts = line.trim().split(/\s+/);
          console.log('MTL行:', line, '| currentMaterial:', currentMaterial);
          if (parts[0] === 'newmtl') {
            currentMaterial = parts[1];
            console.log('newmtl検出:', currentMaterial);
            materialMap[currentMaterial] = new THREE.MeshPhongMaterial({
              color: 0xffffff,
              side: THREE.DoubleSide
            });
          } else if (currentMaterial && parts[0] === 'map_Kd') {
            const textureFileName = parts[1];
            console.log('map_Kd検出:', textureFileName, '| currentMaterial:', currentMaterial);
            console.log('利用可能なテクスチャ:', Object.keys(textureUrls));

            // テクスチャファイル名を正規化
            const normalizedFileName = textureFileName.toLowerCase();
            const availableTexture = Object.keys(textureUrls).find(
              key => key.toLowerCase() === normalizedFileName
            );

            if (availableTexture) {
              console.log('テクスチャを読み込み:', availableTexture);
              const textureLoader = new THREE.TextureLoader();
              textureLoader.crossOrigin = 'anonymous';
              // currentMaterialをクロージャで固定
              const materialNameForClosure = currentMaterial;
              // テクスチャの読み込みをPromiseでラップ
              const texturePromise = new Promise<void>((resolve, reject) => {
                textureLoader.load(
                  textureUrls[availableTexture],
                  (texture) => {
                    const material = materialMap[materialNameForClosure] as THREE.MeshPhongMaterial;
                    material.map = texture;
                    material.needsUpdate = true;
                    console.log('テクスチャを適用:', materialNameForClosure);
                    resolve();
                  },
                  undefined,
                  (error) => {
                    console.error('テクスチャの読み込みに失敗:', error);
                    reject(error);
                  }
                );
              });
              texturePromises.push(texturePromise);
            } else {
              console.warn('テクスチャが見つかりません:', textureFileName);
            }
          }
        }

        // すべてのテクスチャの読み込みが完了するまで待機
        await Promise.all(texturePromises);
        console.log('マテリアルの読み込みが完了');

        console.log('OBJファイルの読み込みを開始:', modelUrl);
        // OBJファイルを読み込む
        const object = await new Promise<THREE.Object3D>((resolve, reject) => {
          loaderRef.current?.load(
            modelUrl,
            (object) => {
              // マテリアルを適用
              object.traverse((child) => {
                if (child instanceof THREE.Mesh) {
                  if (Array.isArray(child.material)) {
                    child.material.forEach((mat, idx) => {
                      const matName = mat.name;
                      if (materialMap[matName]) {
                        child.material[idx] = materialMap[matName];
                      }
                    });
                  } else {
                    const matName = child.material.name;
                    if (materialMap[matName]) {
                      child.material = materialMap[matName];
                    }
                  }
                }
              });

              // ジオメトリの検証と修正
              validateAndFixGeometry(object);
              resolve(object);
            },
            undefined,
            (error) => reject(error)
          );
        });
        console.log('OBJファイルの読み込みが完了');

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
        console.log('モデルの設定が完了');
      } catch (err) {
        console.error('モデルの読み込みに失敗しました:', err);
        setError('モデルの読み込みに失敗しました');
      }
    };

    loadModel();

    return () => {
      if (model) {
        scene.remove(model);
      }
    };
  }, [modelUrl, mtlUrl, textureUrls, scene]);

  if (error) {
    return <mesh><boxGeometry args={[1, 1, 1]} /><meshStandardMaterial color="red" /></mesh>;
  }

  return model ? <primitive object={model} /> : null;
}; 