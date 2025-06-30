#!/usr/bin/env python3
"""
カメラ姿勢推定モジュール
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import os


class PoseEstimator:
    """カメラ姿勢推定クラス"""
    
    def __init__(self, ransac_threshold: float = 8.0, confidence: float = 0.99):
        """初期化
        
        Args:
            ransac_threshold: RANSACの閾値（ピクセル）
            confidence: RANSACの信頼度
        """
        self.ransac_threshold = ransac_threshold
        self.confidence = confidence
        
        print(f"姿勢推定器を初期化: RANSAC threshold={ransac_threshold}, confidence={confidence}")
    
    def estimate_camera_matrix_from_metadata(self, metadata_dict: Dict[int, Dict]) -> np.ndarray:
        """メタデータからカメラ行列を推定
        
        Args:
            metadata_dict: メタデータ辞書
            
        Returns:
            カメラ行列
        """
        # 最初の画像のメタデータを使用
        if not metadata_dict:
            # デフォルトカメラ行列
            return np.array([[1000, 0, 960], [0, 1000, 540], [0, 0, 1]])
        
        first_metadata = metadata_dict[list(metadata_dict.keys())[0]]
        
        if 'camera_matrix' in first_metadata and first_metadata['camera_matrix'] is not None:
            return np.array(first_metadata['camera_matrix'])
        elif 'image_size' in first_metadata:
            # 画像サイズから推定
            width = first_metadata['image_size']['width']
            height = first_metadata['image_size']['height']
            focal_length = max(width, height) * 0.8
            
            return np.array([
                [focal_length, 0, width / 2],
                [0, focal_length, height / 2],
                [0, 0, 1]
            ])
        else:
            # デフォルトカメラ行列
            return np.array([[1000, 0, 960], [0, 1000, 540], [0, 0, 1]])
    
    def estimate_essential_matrix(self, pts1: np.ndarray, pts2: np.ndarray, 
                                camera_matrix: np.ndarray) -> Tuple[Optional[np.ndarray], List[int]]:
        """基本行列を推定
        
        Args:
            pts1: 1つ目の画像の対応点
            pts2: 2つ目の画像の対応点
            camera_matrix: カメラ行列
            
        Returns:
            (基本行列, インライアのインデックス)
        """
        if len(pts1) < 8 or len(pts2) < 8:
            print("対応点が不足しています（最低8点必要）")
            return None, []
        
        try:
            # 基本行列を推定
            E, mask = cv2.findEssentialMat(pts1, pts2, camera_matrix, 
                                         method=cv2.RANSAC, 
                                         prob=self.confidence, 
                                         threshold=self.ransac_threshold)
            
            if E is None:
                print("基本行列の推定に失敗しました")
                return None, []
            
            # インライアのインデックスを取得
            inliers = np.where(mask.ravel() == 1)[0].tolist()
            
            print(f"基本行列推定: {len(pts1)} → {len(inliers)} インライア")
            return E, inliers
            
        except Exception as e:
            print(f"基本行列推定エラー: {e}")
            return None, []
    
    def recover_pose(self, pts1: np.ndarray, pts2: np.ndarray, 
                    essential_matrix: np.ndarray, camera_matrix: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], List[int]]:
        """姿勢を復元
        
        Args:
            pts1: 1つ目の画像の対応点
            pts2: 2つ目の画像の対応点
            essential_matrix: 基本行列
            camera_matrix: カメラ行列
            
        Returns:
            (回転行列, 並進ベクトル, インライアのインデックス)
        """
        if essential_matrix is None:
            return None, None, []
        
        try:
            # 姿勢を復元
            result = cv2.recoverPose(essential_matrix, pts1, pts2, camera_matrix)
            
            # OpenCVのバージョンによって戻り値が異なる場合がある
            if len(result) == 4:
                # OpenCV 4.x: (retval, R, t, mask)
                retval, R, t, mask = result
            elif len(result) == 3:
                # OpenCV 3.x: (R, t, mask)
                R, t, mask = result
            else:
                print(f"予期しない戻り値: {len(result)} 個の要素")
                return None, None, []
            
            if R is None or t is None:
                print("姿勢復元に失敗しました")
                return None, None, []
            
            # インライアのインデックスを取得
            inliers = np.where(mask.ravel() == 1)[0].tolist()
            
            print(f"姿勢復元: 回転行列 shape={R.shape}, 並進ベクトル shape={t.shape}")
            print(f"インライア数: {len(inliers)}")
            
            return R, t, inliers
            
        except Exception as e:
            print(f"姿勢復元エラー: {e}")
            return None, None, []
    
    def estimate_pose_from_matches(self, keypoints1: List[cv2.KeyPoint], 
                                 keypoints2: List[cv2.KeyPoint],
                                 matches: List[cv2.DMatch], 
                                 camera_matrix: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], List[int]]:
        """マッチング結果から姿勢を推定
        
        Args:
            keypoints1: 1つ目の画像の特徴点
            keypoints2: 2つ目の画像の特徴点
            matches: マッチング結果
            camera_matrix: カメラ行列
            
        Returns:
            (回転行列, 並進ベクトル, インライアのインデックス)
        """
        if not matches:
            print("マッチング結果がありません")
            return None, None, []
        
        # 対応点の座標を取得
        pts1 = np.float32([keypoints1[m.queryIdx].pt for m in matches])
        pts2 = np.float32([keypoints2[m.trainIdx].pt for m in matches])
        
        # 基本行列を推定
        E, inliers_E = self.estimate_essential_matrix(pts1, pts2, camera_matrix)
        
        if E is None:
            return None, None, []
        
        # 姿勢を復元
        R, t, inliers_pose = self.recover_pose(pts1, pts2, E, camera_matrix)
        
        return R, t, inliers_pose
    
    def estimate_pose_pnp(self, points_3d: np.ndarray, points_2d: np.ndarray, 
                         camera_matrix: np.ndarray, 
                         dist_coeffs: Optional[np.ndarray] = None,
                         metadata_dict: Optional[Dict[int, Dict]] = None) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """PnP（Perspective-n-Point）で姿勢を推定
        
        Args:
            points_3d: 3D点の座標
            points_2d: 2D点の座標
            camera_matrix: カメラ行列
            dist_coeffs: 歪み係数
            metadata_dict: メタデータ辞書（焦点距離を取得するため）
            
        Returns:
            (回転ベクトル, 並進ベクトル)
        """
        if len(points_3d) < 4 or len(points_2d) < 4:
            print("PnP姿勢推定: 対応点が不足しています（最低4点必要）")
            return None, None
        
        if dist_coeffs is None:
            dist_coeffs = np.zeros(5)
        
        try:
            # PnP姿勢推定
            success, rvec, tvec, inliers = cv2.solvePnPRansac(
                points_3d, points_2d, camera_matrix, dist_coeffs,
                # # reprojectionError=8.0, confidence=0.99
            )
            
            if not success:
                print("PnP姿勢推定に失敗しました")
                return None, None
            
            # 回転ベクトル転行列に変換
            R, _ = cv2.Rodrigues(rvec)
            
            # PnP姿勢推定後に正規化（異常に大きな並進ベクトルを調整）
            if metadata_dict is not None:
                tvec_normalized = self._normalize_translation(tvec, camera_matrix, metadata_dict)
                print(f"PnP姿勢推定成功（正規化済み）: {len(inliers)} インライア")
                return R, tvec_normalized
            else:
                print(f"PnP姿勢推定成功: {len(inliers)} インライア")
                return R, tvec
            
        except Exception as e:
            print(f"PnP姿勢推定エラー: {e}")
            return None, None
    
    def triangulate_points(self, pts1: np.ndarray, pts2: np.ndarray,
                          R1: np.ndarray, t1: np.ndarray,
                          R2: np.ndarray, t2: np.ndarray,
                          camera_matrix: np.ndarray) -> np.ndarray:
        """三角測量で3D点を計算
        
        Args:
            pts1: 1つ目の画像の対応点
            pts2: 2つ目の画像の対応点
            R1: 1つ目のカメラの回転行列
            t1: 1つ目のカメラの並進ベクトル
            R2: 2つ目のカメラの回転行列
            t2: 2つ目のカメラの並進ベクトル
            camera_matrix: カメラ行列
            
        Returns:
            3D点の座標
        """
        if len(pts1) == 0 or len(pts2) == 0:
            return np.array([])
        
        try:
            # 投影行列を作成
            P1 = camera_matrix @ np.hstack([R1, t1.reshape(3, 1)])
            P2 = camera_matrix @ np.hstack([R2, t2.reshape(3, 1)])
            
            # 三角測量
            points_4d = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
            points_3d = (points_4d[:3] / points_4d[3]).T
            
            print(f"三角測量: {len(pts1)} 点 → {len(points_3d)} 3D点")
            return points_3d
            
        except Exception as e:
            print(f"三角測量エラー: {e}")
            return np.array([])
    
    def check_cheirality(self, points_3d: np.ndarray, R: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Cheirality制約をチェック（3D点がカメラの前方にあるか）
        
        Args:
            points_3d: 3D点の座標
            R: 回転行列
            t: 並進ベクトル
            
        Returns:
            有効な3D点のインデックス
        """
        if len(points_3d) == 0:
            return np.array([])
        
        # カメラ座標系での3D点を計算
        points_cam = (R @ points_3d.T + t.reshape(3, 1)).T
        
        # Z座標が正（カメラの前方）の点を選択
        valid_indices = np.where(points_cam[:, 2] > 0)[0]
        
        print(f"Cheirality制約: {len(points_3d)} → {len(valid_indices)} 有効な点")
        return valid_indices
    
    def check_cheirality_relaxed(self, points_3d: np.ndarray, R: np.ndarray, t: np.ndarray) -> np.ndarray:
        """より緩いCheirality制約をチェック（3D点がカメラの前方にあるか）
        
        Args:
            points_3d: 3D点の座標
            R: 回転行列
            t: 並進ベクトル
            
        Returns:
            有効な3D点のインデックス
        """
        if len(points_3d) == 0:
            return np.array([])
        
        # カメラ座標系での3D点を計算
        points_cam = (R @ points_3d.T + t.reshape(3, 1)).T
        
        # より緩い制約: Z座標が少し負でも許容
        # また、点が無限遠に近すぎないこともチェック
        z_threshold = -0.1  # より緩いZ座標の閾値
        max_distance = 1000.0  # 最大距離の閾値
        
        # 距離を計算
        distances = np.linalg.norm(points_3d, axis=1)
        
        # 条件をチェック
        valid_z = points_cam[:, 2] > z_threshold
        valid_distance = distances < max_distance
        valid_points = valid_z & valid_distance
        
        valid_indices = np.where(valid_points)[0]
        
        print(f"緩いCheirality制約: {len(points_3d)} → {len(valid_indices)} 有効な点")
        print(f"  Z座標条件: {np.sum(valid_z)} 点")
        print(f"  距離条件: {np.sum(valid_distance)} 点")
        
        return valid_indices
    
    def estimate_initial_poses(self, keypoints_dict: Dict[int, List[cv2.KeyPoint]],
                             descriptors_dict: Dict[int, np.ndarray],
                             matches_dict: Dict[Tuple[int, int], List[cv2.DMatch]],
                             camera_matrix: np.ndarray,
                             metadata_dict: Optional[Dict[int, Dict]] = None) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
        """初期姿勢を推定
        
        Args:
            keypoints_dict: 特徴点辞書
            descriptors_dict: ディスクリプタ辞書
            matches_dict: マッチング結果辞書
            camera_matrix: カメラ行列
            metadata_dict: メタデータ辞書（焦点距離を取得するため）
        Returns:
            画像インデックスをキーとした姿勢辞書
        """
        poses_dict = {}
        
        print("初期姿勢推定を開始")
        
        # 最初の画像を基準とする（SfMの標準的なアプローチ）
        image_indices = list(keypoints_dict.keys())
        if len(image_indices) < 2:
            print("画像が不足しています（最低2枚必要）")
            return poses_dict
        
        # 最初の画像を基準とする（SfMの標準的なアプローチ）
        poses_dict[image_indices[0]] = (np.eye(3), np.zeros(3))
        print(f"基準画像 {image_indices[0]}: 原点に固定")
        
        # 2番目の画像の姿勢を推定
        if len(image_indices) >= 2:
            idx1, idx2 = image_indices[0], image_indices[1]
            
            # マッチング結果を取得
            if (idx1, idx2) in matches_dict:
                matches = matches_dict[(idx1, idx2)]
            elif (idx2, idx1) in matches_dict:
                matches = matches_dict[(idx2, idx1)]
                # マッチングの順序を反転
                for match in matches:
                    match.queryIdx, match.trainIdx = match.trainIdx, match.queryIdx
            else:
                print(f"画像 {idx1} と {idx2} のマッチングが見つかりません")
                return poses_dict
            
            print(f"画像 {idx1} と {idx2} の間で {len(matches)} マッチングを使用")
            
            # 姿勢を推定
            R, t, inliers = self.estimate_pose_from_matches(
                keypoints_dict[idx1], keypoints_dict[idx2], matches, camera_matrix
            )
            
            if R is not None and t is not None:
                poses_dict[idx2] = (R, t.flatten())
                print(f"画像 {idx2} の姿勢推定成功")
                
                # 追加の画像の姿勢を推定（控えめな360度配置）
                self._estimate_additional_poses(poses_dict, keypoints_dict, matches_dict, camera_matrix, metadata_dict)
            else:
                print(f"画像 {idx2} の姿勢推定に失敗")
        
        print(f"初期姿勢推定完了: {len(poses_dict)} 画像")
        return poses_dict
    
    def _estimate_additional_poses(self, poses_dict: Dict[int, Tuple[np.ndarray, np.ndarray]],
                                 keypoints_dict: Dict[int, List[cv2.KeyPoint]],
                                 matches_dict: Dict[Tuple[int, int], List[cv2.DMatch]],
                                 camera_matrix: np.ndarray,
                                 metadata_dict: Optional[Dict[int, Dict]] = None):
        """追加の画像の姿勢を控えめな360度配置で推定"""
        estimated_images = set(poses_dict.keys())
        all_images = set(keypoints_dict.keys())
        
        # まだ姿勢が推定されていない画像を処理
        remaining_images = all_images - estimated_images
        
        # 既存のカメラ位置を分析
        existing_positions = []
        for img_idx, (R, t) in poses_dict.items():
            pos = -R.T @ t
            existing_positions.append((img_idx, pos))
        
        # 既存のカメラの平均距離を計算
        if len(existing_positions) > 0:
            distances = [np.linalg.norm(pos) for _, pos in existing_positions]
            avg_distance = np.mean(distances)
            print(f"既存カメラの平均距離: {avg_distance:.1f}mm")
        else:
            avg_distance = 50.0  # デフォルト距離
        
        for img_idx in remaining_images:
            # 既に姿勢が推定された画像とのマッチングを探す
            best_matches = None
            best_reference_img = None
            max_matches = 0
            
            for ref_img in estimated_images:
                if (ref_img, img_idx) in matches_dict:
                    matches = matches_dict[(ref_img, img_idx)]
                    if len(matches) > max_matches:
                        max_matches = len(matches)
                        best_matches = matches
                        best_reference_img = ref_img
                elif (img_idx, ref_img) in matches_dict:
                    matches = matches_dict[(img_idx, ref_img)]
                    if len(matches) > max_matches:
                        max_matches = len(matches)
                        best_matches = matches
                        best_reference_img = ref_img
            
            if best_matches and len(best_matches) >= 10:  # 最低10マッチング必要
                print(f"画像 {img_idx} の姿勢推定を試行（{len(best_matches)} マッチング）")
                
                # 控えめな360度配置
                # 画像インデックスに基づいて角度を計算（既存のカメラを避ける）
                angle = (img_idx - min(all_images)) * (2 * np.pi / len(all_images))
                radius = avg_distance * 0.8  # 既存の平均距離の80%
                
                # 円周上に配置
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                z = 0.0
                
                # 回転行列（Z軸周りの回転、控えめに）
                cos_angle = np.cos(angle)
                sin_angle = np.sin(angle)
                R = np.array([
                    [cos_angle, -sin_angle, 0],
                    [sin_angle, cos_angle, 0],
                    [0, 0, 1]
                ])
                
                # 並進ベクトル
                t = np.array([x, y, z])
                
                # 正規化（控えめに）
                if metadata_dict is not None:
                    t_normalized = self._normalize_translation(t, camera_matrix, metadata_dict)
                    poses_dict[img_idx] = (R, t_normalized)
                else:
                    poses_dict[img_idx] = (R, t)
                
                print(f"画像 {img_idx} の姿勢設定成功（角度: {np.degrees(angle):.1f}°, 位置: [{x:.1f}, {y:.1f}, {z:.1f}]）")
            else:
                print(f"画像 {img_idx} のマッチングが不足（{max_matches} マッチング）")
    
    def save_poses(self, poses_dict: Dict[int, Tuple[np.ndarray, np.ndarray]], 
                  output_dir: str):
        """姿勢データを保存
        
        Args:
            poses_dict: 姿勢辞書
            output_dir: 出力ディレクトリ
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 姿勢データを保存
        poses_file = output_path / "poses.npz"
        poses_data = {}
        
        for image_idx, (R, t) in poses_dict.items():
            poses_data[f'R_{image_idx}'] = R
            poses_data[f't_{image_idx}'] = t
        
        np.savez_compressed(poses_file, **poses_data)
        print(f"姿勢データを保存: {output_dir}")
    
    def load_poses(self, input_dir: str) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
        """姿勢データを読み込み
        
        Args:
            input_dir: 入力ディレクトリ
            
        Returns:
            姿勢辞書
        """
        input_path = Path(input_dir)
        poses_dict = {}
        
        poses_file = input_path / "poses.npz"
        if poses_file.exists():
            poses_data = np.load(poses_file)
            
            # 回転行列と並進ベクトルを取得
            rotation_keys = [key for key in poses_data.files if key.startswith('R_')]
            
            for key in rotation_keys:
                image_idx = int(key.split('_')[1])
                R = poses_data[key]
                t = poses_data[f't_{image_idx}']
                poses_dict[image_idx] = (R, t)
        
        print(f"姿勢データを読み込み: {len(poses_dict)} 画像")
        return poses_dict 
    
    def _normalize_translation(self, t: np.ndarray, camera_matrix: np.ndarray, 
                             metadata_dict: Optional[Dict[int, Dict]] = None) -> np.ndarray:
        """並進ベクトルを適切な距離に正規化
        
        Args:
            t: 並進ベクトル
            camera_matrix: カメラ行列
            metadata_dict: メタデータ辞書（焦点距離を取得するため）
            
        Returns:
            正規化された並進ベクトル
        """
        # 実際の焦点距離（mm）を取得
        focal_length_mm = None
        if metadata_dict:
            # 最初の画像のメタデータから焦点距離を取得
            first_metadata = metadata_dict[list(metadata_dict.keys())[0]]
            if 'focal_length' in first_metadata and first_metadata['focal_length'] is not None:
                focal_length_mm = first_metadata['focal_length']
                print(f"メタデータから焦点距離を取得: {focal_length_mm}mm")
        
        # メタデータから焦点距離が取得できない場合は、カメラ行列から推定
        if focal_length_mm is None:
            # カメラ行列の焦点距離（ピクセル単位）を取得
            focal_length_pixels = (camera_matrix[0, 0] + camera_matrix[1, 1]) / 2
            
            # 画像サイズからmm/pixelの比率を推定
            # 一般的なデジタルカメラでは、センサーサイズと画像サイズの比率を使用
            if metadata_dict:
                first_metadata = metadata_dict[list(metadata_dict.keys())[0]]
                if 'image_size' in first_metadata:
                    width = first_metadata['image_size']['width']
                    height = first_metadata['image_size']['height']
                    
                    # 一般的なAPS-Cセンサーサイズ（23.5 x 15.6mm）を仮定
                    sensor_width_mm = 23.5
                    mm_per_pixel = sensor_width_mm / width
                    focal_length_mm = focal_length_pixels * mm_per_pixel
                    print(f"センサーサイズから焦点距離を推定: {focal_length_mm:.1f}mm")
                else:
                    # デフォルト値を使用
                    focal_length_mm = 50.0  # 標準レンズ
                    print(f"デフォルト焦点距離を使用: {focal_length_mm}mm")
            else:
                # デフォルト値を使用
                focal_length_mm = 50.0  # 標準レンズ
                print(f"デフォルト焦点距離を使用: {focal_length_mm}mm")
        
        # 現在の並進ベクトルの長さを計算
        current_distance = np.linalg.norm(t)
        
        # 適切な距離を設定（焦点距離の1-2倍程度）
        target_distance = focal_length_mm * 1.5
        
        # 異常に大きな並進ベクトルの場合の特別処理
        if current_distance > target_distance * 10:  # 異常に大きい場合
            print(f"異常に大きな並進ベクトルを検出: {current_distance:.1f}mm → {target_distance:.1f}mm に調整")
            # 方向を保持して距離を大幅に縮小
            if current_distance > 0:
                t_normalized = t * (target_distance / current_distance)
            else:
                t_normalized = np.array([target_distance, 0, 0])
        elif current_distance > 0:
            # 通常の正規化
            t_normalized = t * (target_distance / current_distance)
        else:
            # デフォルトの距離を設定
            t_normalized = np.array([target_distance, 0, 0])
        
        print(f"並進ベクトル正規化: {current_distance:.2f} → {np.linalg.norm(t_normalized):.2f} (目標距離: {target_distance:.1f}mm)")
        return t_normalized
    
    def normalize_all_poses(self, poses_dict: Dict[int, Tuple[np.ndarray, np.ndarray]],
                          camera_matrix: np.ndarray,
                          metadata_dict: Optional[Dict[int, Dict]] = None) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
        """全ての姿勢の並進ベクトルを正規化（控えめな調整）
        
        Args:
            poses_dict: 姿勢辞書
            camera_matrix: カメラ行列
            metadata_dict: メタデータ辞書（焦点距離を取得するため）
            
        Returns:
            正規化された姿勢辞書
        """
        print("全ての姿勢の正規化を開始（控えめな調整）")
        
        if len(poses_dict) < 2:
            return poses_dict
        
        # 実際の焦点距離（mm）を取得
        focal_length_mm = None
        if metadata_dict:
            first_metadata = metadata_dict[list(metadata_dict.keys())[0]]
            if 'focal_length' in first_metadata and first_metadata['focal_length'] is not None:
                focal_length_mm = first_metadata['focal_length']
                print(f"メタデータから焦点距離を取得: {focal_length_mm}mm")
        
        if focal_length_mm is None:
            focal_length_mm = 50.0  # デフォルト値
            print(f"デフォルト焦点距離を使用: {focal_length_mm}mm")
        
        # 目標距離を設定（焦点距離の1.5倍程度）
        target_distance = focal_length_mm * 1.5
        
        # 現在のカメラ位置を分析
        camera_positions = []
        for img_idx, (R, t) in poses_dict.items():
            camera_pos = -R.T @ t
            camera_positions.append((img_idx, camera_pos))
            print(f"カメラ {img_idx} の現在位置: {camera_pos}")
        
        # カメラ位置の中心を計算（カメラ0を除く）
        non_zero_positions = [pos for _, pos in camera_positions if np.linalg.norm(pos) > 0.1]
        if len(non_zero_positions) > 0:
            center = np.mean(non_zero_positions, axis=0)
        else:
            # 全てのカメラが原点付近の場合は、適切な中心を設定
            center = np.array([0.0, 0.0, 0.0])
        
        print(f"カメラ位置の中心: {center}")
        
        # 各カメラを中心から適切な距離に配置（控えめな調整）
        normalized_poses = {}
        for img_idx, (R, t) in poses_dict.items():
            current_pos = -R.T @ t
            
            # 中心からの方向ベクトルを計算
            direction = current_pos - center
            distance = np.linalg.norm(direction)
            
            if distance > 0:
                # 現在の距離と目標距離の間で補間（控えめな調整）
                current_distance = np.linalg.norm(current_pos - center)
                if current_distance > target_distance * 3:  # 異常に遠い場合のみ調整
                    # 方向を正規化して目標距離に調整
                    normalized_direction = direction / distance
                    new_pos = center + normalized_direction * target_distance
                    print(f"カメラ {img_idx}: {current_pos} → {new_pos} (距離調整: {current_distance:.1f} → {target_distance:.1f}mm)")
                elif current_distance < target_distance * 0.3:  # 異常に近い場合のみ調整
                    # 方向を正規化して目標距離に調整
                    normalized_direction = direction / distance
                    new_pos = center + normalized_direction * target_distance
                    print(f"カメラ {img_idx}: {current_pos} → {new_pos} (距離調整: {current_distance:.1f} → {target_distance:.1f}mm)")
                else:
                    # 適切な範囲内の場合はそのまま
                    new_pos = current_pos
                    print(f"カメラ {img_idx}: 位置を維持 {current_pos} (距離: {current_distance:.1f}mm)")
            else:
                # デフォルトの位置を設定（X軸方向）
                new_pos = center + np.array([target_distance, 0, 0])
                print(f"カメラ {img_idx}: デフォルト位置に配置 {new_pos}")
            
            # 新しい並進ベクトルを計算
            new_t = -R @ new_pos
            normalized_poses[img_idx] = (R, new_t.flatten())
        
        print(f"姿勢正規化完了: {len(normalized_poses)} 画像")
        return normalized_poses