#!/usr/bin/env python3
"""
特徴点抽出モジュール
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import os


class FeatureExtractor:
    """特徴点抽出クラス"""
    
    def __init__(self, detector_type: str = 'SIFT', max_features: int = 3000):
        """初期化
        
        Args:
            detector_type: 特徴点検出器の種類 ('SIFT', 'SURF', 'ORB', 'AKAZE')
            max_features: 最大特徴点数
        """
        self.detector_type = detector_type.upper()
        self.max_features = max_features
        self.detector = self._create_detector()
        self.preprocess = False
        self.sharpen = False
        self.enhance_contrast = False
        self.gray = False
        print(f"特徴点検出器を初期化: {self.detector_type} (最大{max_features}点)")
    
    def _create_detector(self):
        """特徴点検出器を作成"""
        if self.detector_type == 'SIFT':
            return cv2.SIFT_create(
                nfeatures=self.max_features,
                nOctaveLayers=10,        # 3から5に増加（より多くのオクターブ層）
                contrastThreshold=0.02, # 0.04から0.02に減少（より低いコントラストでも検出）
                edgeThreshold=20,       # 10から15に増加（エッジの閾値を緩和）
                sigma=1.6
            )
        elif self.detector_type == 'SURF':
            # SURFは特許の問題で利用できない場合がある
            try:
                return cv2.xfeatures2d.SURF_create(hessianThreshold=400)
            except:
                print("SURFが利用できません。SIFTに切り替えます。")
                return cv2.SIFT_create(nfeatures=self.max_features)
        elif self.detector_type == 'ORB':
            return cv2.ORB_create(nfeatures=self.max_features)
        elif self.detector_type == 'AKAZE':
            return cv2.AKAZE_create()
        else:
            print(f"未知の検出器タイプ: {self.detector_type}。SIFTを使用します。")
            return cv2.SIFT_create(nfeatures=self.max_features)
    
    def extract_features(self, image: np.ndarray) -> Tuple[List[cv2.KeyPoint], np.ndarray]:
        """単一画像から特徴点を抽出
        
        Args:
            image: 入力画像
            
        Returns:
            (特徴点リスト, ディスクリプタ配列)
        """
        if image is None:
            return [], np.array([])
        
        # 前処理を実行
        processed_image = self.preprocess_image(image)
        
        # 特徴点とディスクリプタを抽出
        keypoints, descriptors = self.detector.detectAndCompute(processed_image, None)
        
        if keypoints is None:
            keypoints = []
        if descriptors is None:
            descriptors = np.array([])
        
        print(f"特徴点抽出: {len(keypoints)} 点, ディスクリプタ: {descriptors.shape if len(descriptors) > 0 else 'なし'}")
        
        return keypoints, descriptors
    
    def extract_features_batch(self, images: List[np.ndarray] | Dict[int, np.ndarray], 
                             output_dir: Optional[str] = None) -> Tuple[Dict[int, List[cv2.KeyPoint]], Dict[int, np.ndarray]]:
        """複数画像から特徴点を一括抽出
        
        Args:
            images: 画像リストまたは画像辞書
            output_dir: 出力ディレクトリ（指定時は特徴点可視化を保存）
            
        Returns:
            (特徴点辞書, ディスクリプタ辞書)
        """
        keypoints_dict = {}
        descriptors_dict = {}
        
        # 画像辞書の場合はそのまま使用、リストの場合は辞書に変換
        if isinstance(images, dict):
            images_dict = images
            print(f"バッチ特徴点抽出を開始: {len(images_dict)} 画像")
        else:
            images_dict = {i: img for i, img in enumerate(images)}
            print(f"バッチ特徴点抽出を開始: {len(images_dict)} 画像")
        
        # 出力ディレクトリの設定
        keypoints_dir = None
        if output_dir:
            keypoints_dir = Path(output_dir) / "keypoints"
            keypoints_dir.mkdir(parents=True, exist_ok=True)
            print(f"特徴点可視化を保存: {keypoints_dir}")
        
        for image_idx, image in images_dict.items():
            try:
                keypoints, descriptors = self.extract_features(image)
                keypoints_dict[image_idx] = keypoints
                descriptors_dict[image_idx] = descriptors
                print(f"画像 {image_idx}: {len(keypoints)} 特徴点抽出完了")
                
                # 特徴点可視化を保存
                if keypoints_dir and image is not None:
                    vis_filename = f"keypoints_image_{image_idx:03d}.jpg"
                    vis_path = keypoints_dir / vis_filename
                    self.visualize_keypoints(image, keypoints, str(vis_path))
                
            except Exception as e:
                print(f"画像 {image_idx} の特徴点抽出に失敗: {e}")
                keypoints_dict[image_idx] = []
                descriptors_dict[image_idx] = np.array([])
        
        print(f"バッチ特徴点抽出完了: {len(keypoints_dict)} 画像")
        return keypoints_dict, descriptors_dict
    
    def extract_features_from_paths(self, image_paths: List[str], 
                                  output_dir: Optional[str] = None) -> Tuple[Dict[int, List[cv2.KeyPoint]], Dict[int, np.ndarray]]:
        """画像パスリストから特徴点を抽出
        
        Args:
            image_paths: 画像ファイルパスのリスト
            output_dir: 出力ディレクトリ（指定時は特徴点可視化を保存）
            
        Returns:
            (特徴点辞書, ディスクリプタ辞書)
        """
        keypoints_dict = {}
        descriptors_dict = {}
        
        print(f"パスからの特徴点抽出を開始: {len(image_paths)} 画像")
        
        # 出力ディレクトリの設定
        keypoints_dir = None
        if output_dir:
            keypoints_dir = Path(output_dir) / "keypoints"
            keypoints_dir.mkdir(parents=True, exist_ok=True)
            print(f"特徴点可視化を保存: {keypoints_dir}")
        
        for i, image_path in enumerate(image_paths):
            try:
                # 画像を読み込み
                image = cv2.imread(image_path)
                if image is None:
                    print(f"画像を読み込めません: {image_path}")
                    keypoints_dict[i] = []
                    descriptors_dict[i] = np.array([])
                    continue
                
                # 特徴点を抽出
                keypoints, descriptors = self.extract_features(image)
                keypoints_dict[i] = keypoints
                descriptors_dict[i] = descriptors
                print(f"画像 {Path(image_path).name}: {len(keypoints)} 特徴点抽出完了")
                
                # 特徴点可視化を保存
                if keypoints_dir and image is not None:
                    # 元のファイル名をベースにしたファイル名を作成
                    original_name = Path(image_path).stem
                    vis_filename = f"keypoints_{original_name}.jpg"
                    vis_path = keypoints_dir / vis_filename
                    self.visualize_keypoints(image, keypoints, str(vis_path))
                
            except Exception as e:
                print(f"画像 {image_path} の特徴点抽出に失敗: {e}")
                keypoints_dict[i] = []
                descriptors_dict[i] = np.array([])
        
        print(f"パスからの特徴点抽出完了: {len(keypoints_dict)} 画像")
        return keypoints_dict, descriptors_dict
    
    def filter_keypoints_by_quality(self, keypoints: List[cv2.KeyPoint], 
                                  descriptors: np.ndarray, 
                                  min_quality: float = 0.01) -> Tuple[List[cv2.KeyPoint], np.ndarray]:
        """品質に基づいて特徴点をフィルタリング
        
        Args:
            keypoints: 特徴点リスト
            descriptors: ディスクリプタ配列
            min_quality: 最小品質閾値
            
        Returns:
            (フィルタリングされた特徴点, フィルタリングされたディスクリプタ)
        """
        if not keypoints or len(descriptors) == 0:
            return [], np.array([])
        
        # 品質スコアでフィルタリング
        filtered_keypoints = []
        filtered_descriptors = []
        
        for i, kp in enumerate(keypoints):
            if hasattr(kp, 'response') and kp.response >= min_quality:
                filtered_keypoints.append(kp)
                filtered_descriptors.append(descriptors[i])
        
        filtered_descriptors = np.array(filtered_descriptors)
        
        print(f"品質フィルタリング: {len(keypoints)} → {len(filtered_keypoints)} 点")
        
        return filtered_keypoints, filtered_descriptors
    
    def filter_keypoints_by_distance(self, keypoints: List[cv2.KeyPoint], 
                                   descriptors: np.ndarray, 
                                   min_distance: float = 10.0) -> Tuple[List[cv2.KeyPoint], np.ndarray]:
        """距離に基づいて特徴点をフィルタリング（近接点を除去）
        
        Args:
            keypoints: 特徴点リスト
            descriptors: ディスクリプタ配列
            min_distance: 最小距離閾値
            
        Returns:
            (フィルタリングされた特徴点, フィルタリングされたディスクリプタ)
        """
        if not keypoints or len(descriptors) == 0:
            return [], np.array([])
        
        # 特徴点の座標を取得
        points = np.array([kp.pt for kp in keypoints])
        
        # 距離行列を計算
        distances = np.zeros((len(points), len(points)))
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dist = np.linalg.norm(points[i] - points[j])
                distances[i, j] = dist
                distances[j, i] = dist
        
        # 近接点を除去
        keep_indices = []
        for i in range(len(points)):
            # より良い品質の点を優先
            if i == 0 or all(distances[i, j] >= min_distance for j in keep_indices):
                keep_indices.append(i)
        
        filtered_keypoints = [keypoints[i] for i in keep_indices]
        filtered_descriptors = descriptors[keep_indices]
        
        print(f"距離フィルタリング: {len(keypoints)} → {len(filtered_keypoints)} 点")
        
        return filtered_keypoints, filtered_descriptors
    
    def visualize_keypoints(self, image: np.ndarray, keypoints: List[cv2.KeyPoint], 
                          output_path: Optional[str] = None) -> np.ndarray:
        """特徴点を可視化
        
        Args:
            image: 元画像
            keypoints: 特徴点リスト
            output_path: 出力ファイルパス（指定時は保存）
            
        Returns:
            可視化された画像
        """
        if image is None:
            return None
        
        # 特徴点を描画
        vis_image = cv2.drawKeypoints(image, keypoints, None, 
                                    flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        
        # 特徴点数の情報を追加
        text = f"Keypoints: {len(keypoints)}"
        cv2.putText(vis_image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 保存
        if output_path:
            cv2.imwrite(output_path, vis_image)
            print(f"特徴点可視化を保存: {output_path}")
        
        return vis_image
    
    def get_keypoint_statistics(self, keypoints: List[cv2.KeyPoint]) -> Dict:
        """特徴点の統計情報を取得
        
        Args:
            keypoints: 特徴点リスト
            
        Returns:
            統計情報辞書
        """
        if not keypoints:
            return {
                'count': 0,
                'avg_response': 0.0,
                'avg_size': 0.0,
                'avg_angle': 0.0,
                'response_range': (0.0, 0.0),
                'size_range': (0.0, 0.0),
                'angle_range': (0.0, 0.0)
            }
        
        responses = [kp.response for kp in keypoints if hasattr(kp, 'response')]
        sizes = [kp.size for kp in keypoints if hasattr(kp, 'size')]
        angles = [kp.angle for kp in keypoints if hasattr(kp, 'angle')]
        
        stats = {
            'count': len(keypoints),
            'avg_response': np.mean(responses) if responses else 0.0,
            'avg_size': np.mean(sizes) if sizes else 0.0,
            'avg_angle': np.mean(angles) if angles else 0.0,
            'response_range': (min(responses), max(responses)) if responses else (0.0, 0.0),
            'size_range': (min(sizes), max(sizes)) if sizes else (0.0, 0.0),
            'angle_range': (min(angles), max(angles)) if angles else (0.0, 0.0)
        }
        
        return stats
    
    def save_features(self, keypoints_dict: Dict[int, List[cv2.KeyPoint]], 
                     descriptors_dict: Dict[int, np.ndarray], 
                     output_dir: str):
        """特徴点とディスクリプタを保存
        
        Args:
            keypoints_dict: 特徴点辞書
            descriptors_dict: ディスクリプタ辞書
            output_dir: 出力ディレクトリ
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 特徴点を保存
        keypoints_file = output_path / "keypoints.npz"
        keypoints_data = {}
        for i, keypoints in keypoints_dict.items():
            if keypoints:
                # KeyPointオブジェクトをシリアライズ可能な形式に変換
                kp_data = []
                for kp in keypoints:
                    kp_data.append({
                        'pt': kp.pt,
                        'size': kp.size,
                        'angle': kp.angle,
                        'response': kp.response,
                        'octave': kp.octave,
                        'class_id': kp.class_id
                    })
                keypoints_data[f'keypoints_{i}'] = kp_data
        
        np.savez_compressed(keypoints_file, **keypoints_data)
        
        # ディスクリプタを保存
        descriptors_file = output_path / "descriptors.npz"
        descriptors_data = {}
        for i, descriptors in descriptors_dict.items():
            if len(descriptors) > 0:
                descriptors_data[f'descriptors_{i}'] = descriptors
        
        np.savez_compressed(descriptors_file, **descriptors_data)
        
        print(f"特徴点データを保存: {output_dir}")
    
    def load_features(self, input_dir: str) -> Tuple[Dict[int, List[cv2.KeyPoint]], Dict[int, np.ndarray]]:
        """特徴点とディスクリプタを読み込み
        
        Args:
            input_dir: 入力ディレクトリ
            
        Returns:
            (特徴点辞書, ディスクリプタ辞書)
        """
        input_path = Path(input_dir)
        
        keypoints_dict = {}
        descriptors_dict = {}
        
        # 特徴点を読み込み
        keypoints_file = input_path / "keypoints.npz"
        if keypoints_file.exists():
            keypoints_data = np.load(keypoints_file, allow_pickle=True)
            for key in keypoints_data.files:
                if key.startswith('keypoints_'):
                    i = int(key.split('_')[1])
                    kp_data = keypoints_data[key]
                    keypoints = []
                    for kp_info in kp_data:
                        kp = cv2.KeyPoint(
                            x=kp_info['pt'][0],
                            y=kp_info['pt'][1],
                            size=kp_info['size'],
                            angle=kp_info['angle'],
                            response=kp_info['response'],
                            octave=kp_info['octave'],
                            class_id=kp_info['class_id']
                        )
                        keypoints.append(kp)
                    keypoints_dict[i] = keypoints
        
        # ディスクリプタを読み込み
        descriptors_file = input_path / "descriptors.npz"
        if descriptors_file.exists():
            descriptors_data = np.load(descriptors_file)
            for key in descriptors_data.files:
                if key.startswith('descriptors_'):
                    i = int(key.split('_')[1])
                    descriptors_dict[i] = descriptors_data[key]
        
        print(f"特徴点データを読み込み: {len(keypoints_dict)} 画像")
        return keypoints_dict, descriptors_dict
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """画像の前処理を実行
        
        Args:
            image: 入力画像
            
        Returns:
            前処理された画像
        """
        if not self.preprocess or image is None:
            return image
        
        processed_image = image.copy()
        
        # グレースケールに変換
        if self.gray:
            if len(processed_image.shape) == 3:
                gray = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = processed_image
        
        # シャープ化
        if self.sharpen:
            # アンシャープマスク
            gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
            sharpened = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
            gray = sharpened
        
        # コントラスト強調
        if self.enhance_contrast:
            # CLAHE（Contrast Limited Adaptive Histogram Equalization）
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
        
        # ノイズ除去
        gray = cv2.medianBlur(gray, 3)
        
        # カラー画像の場合は、処理されたグレー画像を各チャンネルに適用
        if len(processed_image.shape) == 3:
            processed_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        else:
            processed_image = gray
        
        return processed_image
    
    def enable_sharpen_only(self):
        """シャープ化のみを有効にする"""
        self.preprocess = True
        self.sharpen = True
        self.enhance_contrast = False
        self.gray = False
        print("シャープ化のみを有効にしました")
    
    def enable_contrast_only(self):
        """コントラスト強調のみを有効にする"""
        self.preprocess = True
        self.sharpen = False
        self.enhance_contrast = True
        self.gray = False
        print("コントラスト強調のみを有効にしました")
    
    def enable_all_preprocessing(self):
        """全ての前処理を有効にする"""
        self.preprocess = True
        self.sharpen = True
        self.enhance_contrast = True
        self.gray = True
        print("全ての前処理を有効にしました")

    def enable_gray_only(self):
        """グレースケールのみを有効にする"""
        self.preprocess = True
        self.sharpen = False
        self.enhance_contrast = False
        self.gray = True
        print("グレースケールのみを有効にしました")
    
    def disable_preprocessing(self):
        """前処理を無効にする"""
        self.preprocess = False
        print("前処理を無効にしました")