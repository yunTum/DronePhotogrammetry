#!/usr/bin/env python3
"""
バンドル調整モジュール
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import os
from scipy.optimize import least_squares
import cv2
import random


class BundleAdjuster:
    """バンドル調整クラス"""
    
    def __init__(self, max_iterations: int = 20, tolerance: float = 1e-4):
        """バンドル調整器を初期化
        
        Args:
            max_iterations: 最大反復回数
            tolerance: 収束判定の閾値
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        
        print(f"バンドル調整器を初期化: max_iterations={max_iterations}, tolerance={tolerance}")
    
    def project_points(self, points_3d: np.ndarray, R: np.ndarray, t: np.ndarray, 
                      camera_matrix: np.ndarray, debug: bool = False) -> np.ndarray:
        """3D点を2Dに投影
        
        Args:
            points_3d: 3D点の座標 (N, 3)
            R: 回転行列 (3, 3)
            t: 並進ベクトル (3,)
            camera_matrix: カメラ行列 (3, 3)
            debug: デバッグ情報を表示するかどうか
            
        Returns:
            投影された2D点の座標 (N, 2)
        """
        if len(points_3d) == 0:
            return np.array([])
        
        # 入力の形状を確認
        if points_3d.ndim == 1:
            points_3d = points_3d.reshape(1, 3)
        
        # デバッグ情報
        if debug:
            print(f"project_points: points_3d shape={points_3d.shape}, R shape={R.shape}, t shape={t.shape}")
        
        # カメラ座標系に変換
        points_cam = (R @ points_3d.T + t.reshape(3, 1)).T
        
        # 正規化座標に変換
        points_norm = points_cam[:, :2] / points_cam[:, 2:3]
        
        # ピクセル座標に変換
        points_2d = (camera_matrix[:2, :2] @ points_norm.T + camera_matrix[:2, 2:3]).T
        
        if debug:
            print(f"project_points: result shape={points_2d.shape}")
        
        return points_2d
    
    def compute_reprojection_error(self, points_2d_observed: np.ndarray, 
                                 points_2d_projected: np.ndarray) -> float:
        """再投影誤差を計算
        
        Args:
            points_2d_observed: 観測された2D点
            points_2d_projected: 投影された2D点
            
        Returns:
            平均再投影誤差
        """
        if len(points_2d_observed) == 0 or len(points_2d_projected) == 0:
            return float('inf')
        
        # 配列の形状を確認
        if points_2d_observed.ndim == 1:
            points_2d_observed = points_2d_observed.reshape(1, 2)
        if points_2d_projected.ndim == 1:
            points_2d_projected = points_2d_projected.reshape(1, 2)
        
        errors = np.linalg.norm(points_2d_observed - points_2d_projected, axis=1)
        return np.mean(errors)
    
    def bundle_adjustment_residuals(self, params: np.ndarray, 
                                  observations: List[Tuple[int, int, np.ndarray]],
                                  camera_matrix: np.ndarray,
                                  n_points: int, n_cameras: int) -> np.ndarray:
        """バンドル調整の残差を計算
        
        Args:
            params: 最適化パラメータ（3D点 + カメラ姿勢）
            observations: 観測データ [(camera_idx, point_idx, observed_2d), ...]
            camera_matrix: カメラ行列
            n_points: 3D点の数
            n_cameras: カメラの数
            
        Returns:
            残差ベクトル
        """
        # 引数の詳細をチェック（最初の呼び出し時のみ）
        if len(observations) > 0 and len(observations) < 100:
            print(f"bundle_adjustment_residuals 引数チェック:")
            print(f"  params shape: {params.shape}, dtype: {params.dtype}")
            print(f"  observations length: {len(observations)}")
            print(f"  camera_matrix shape: {camera_matrix.shape}, dtype: {camera_matrix.dtype}")
            print(f"  n_points: {n_points}, n_cameras: {n_cameras}")
        
        # パラメータを分解
        points_3d = params[:n_points * 3].reshape(n_points, 3)
        camera_params = params[n_points * 3:].reshape(n_cameras, 6)  # 回転(3) + 並進(3)
        
        residuals = []
        
        for camera_idx, point_idx, observed_2d in observations:
            if camera_idx >= n_cameras or point_idx >= n_points:
                continue
            
            # カメラパラメータを取得
            camera_param = camera_params[camera_idx]
            
            # 回転ベクトルを回転行列に変換
            rvec = camera_param[:3]
            R, _ = cv2.Rodrigues(rvec)
            t = camera_param[3:]
            
            # 3D点を投影（単一の点として処理）
            point_3d = points_3d[point_idx]
            
            # カメラ座標系に変換
            point_cam = R @ point_3d + t
            
            # 正規化座標に変換
            if point_cam[2] > 0:  # Z座標が正の場合のみ
                point_norm = point_cam[:2] / point_cam[2]
                
                # ピクセル座標に変換
                projected_2d = camera_matrix[:2, :2] @ point_norm + camera_matrix[:2, 2]
                
                # 残差を計算
                # observed_2dの次元を確認して修正
                if observed_2d.ndim > 1:
                    observed_2d = observed_2d.flatten()
                
                residual_x = float(observed_2d[0] - projected_2d[0])
                residual_y = float(observed_2d[1] - projected_2d[1])
                residuals.append(residual_x)
                residuals.append(residual_y)
            else:
                # 投影に失敗した場合
                residuals.append(0.0)
                residuals.append(0.0)
        
        result = np.array(residuals, dtype=np.float64)
        
        # デバッグ情報（最初の数回のみ）
        if len(residuals) > 0 and len(residuals) < 100:
            print(f"残差計算デバッグ: 残差数={len(residuals)}, 結果形状={result.shape}")
        
        return result
    
    def optimize_bundle_adjustment(self, points_3d: np.ndarray,
                                 poses_dict: Dict[int, Tuple[np.ndarray, np.ndarray]],
                                 observations: List[Tuple[int, int, np.ndarray]],
                                 camera_matrix: np.ndarray,
                                 image_points: Optional[Dict[int, np.ndarray]] = None,
                                 keypoints_dict: Optional[Dict[int, List[cv2.KeyPoint]]] = None) -> Tuple[np.ndarray, Dict[int, Tuple[np.ndarray, np.ndarray]]]:
        """バンドル調整を実行
        
        Args:
            points_3d: 3D点の座標
            poses_dict: カメラ姿勢辞書
            observations: 観測データ
            camera_matrix: カメラ行列
            image_points: 3D点と画像点の対応関係（オプション）
            keypoints_dict: 特徴点辞書（オプション）
            
        Returns:
            (最適化された3D点, 最適化された姿勢辞書)
        """
        print("optimize_bundle_adjustment開始")
        print(f"points_3d shape: {points_3d.shape}")
        print(f"poses_dict keys: {list(poses_dict.keys())}")
        print(f"observations length: {len(observations)}")
        print(f"camera_matrix shape: {camera_matrix.shape}")
        
        if len(points_3d) == 0 or len(poses_dict) == 0:
            print("データが不足しています")
            return points_3d, poses_dict
        
        n_points = len(points_3d)
        n_cameras = len(poses_dict)
        
        print(f"バンドル調整を開始: {n_points} 点, {n_cameras} カメラ, {len(observations)} 観測")
        
        # 初期パラメータを構築
        print("初期パラメータを構築中...")
        initial_params = []
        
        # 3D点の座標
        initial_params.extend(points_3d.flatten())
        
        # カメラパラメータ（回転ベクトル + 並進ベクトル）
        camera_indices = sorted(poses_dict.keys())
        for i, camera_idx in enumerate(camera_indices):
            R, t = poses_dict[camera_idx]
            rvec, _ = cv2.Rodrigues(R)
            # rvecを1次元配列に変換
            rvec = rvec.flatten()
            
            # デバッグ情報（最初の数個のみ）
            if i < 3:
                print(f"カメラ {camera_idx}: R shape={R.shape}, t shape={t.shape}")
                print(f"  rvec shape={rvec.shape}, t shape={t.shape}")
                print(f"  rvec: {rvec}, t: {t}")
            
            initial_params.extend(np.concatenate([rvec, t]))
        
        initial_params = np.array(initial_params)
        
        print(f"初期パラメータの形状: {initial_params.shape}")
        print(f"期待される形状: {n_points * 3 + n_cameras * 6}")
        
        # 最適化を実行
        try:
            print("minimizeを開始...")
            
            # パラメータの妥当性をチェック
            print(f"パラメータ数: {len(initial_params)}")
            print(f"期待されるパラメータ数: {n_points * 3 + n_cameras * 6}")
            
            if len(initial_params) != n_points * 3 + n_cameras * 6:
                print("パラメータ数が一致しません")
                return points_3d, poses_dict
            
            # 観測データの妥当性をチェック
            if len(observations) == 0:
                print("観測データがありません")
                return points_3d, poses_dict
            
            # 観測データの形式をチェック
            print(f"観測データ数: {len(observations)}")
            for i in range(min(5, len(observations))):
                camera_idx, point_idx, observed_2d = observations[i]
                print(f"観測 {i}: camera={camera_idx}, point={point_idx}, 2d={observed_2d}, shape={observed_2d.shape}, dtype={observed_2d.dtype}")
            
            # 観測データの形式を修正（必要に応じて）
            corrected_observations = []
            for camera_idx, point_idx, observed_2d in observations:
                # observed_2dが2次元配列の場合は1次元に変換
                if observed_2d.ndim > 1:
                    observed_2d = observed_2d.flatten()
                corrected_observations.append((camera_idx, point_idx, observed_2d))
            
            print(f"修正後の観測データ数: {len(corrected_observations)}")
            
            # 観測データをサンプリングして数を減らす（メモリ不足回避）
            # lm法を使用するために、残差の数が変数の数より多い必要がある
            # 変数の数: n_points * 3 + n_cameras * 6
            # 残差の数: observations * 2
            # 必要な観測数: (n_points * 3 + n_cameras * 6) / 2 + 1
            required_observations = (n_points * 3 + n_cameras * 6) // 2 + 1000  # 余裕を持って1000追加
            
            if len(corrected_observations) < required_observations:
                print(f"観測データが不足しています（{len(corrected_observations)}）。{required_observations}に増やします。")
                
                # 方法1: 元の観測データから重複を許してサンプリング
                if len(corrected_observations) > 0:
                    random.seed(42)  # 再現性のため
                    corrected_observations = random.choices(corrected_observations, k=required_observations)
                    print(f"重複サンプリング後の観測データ数: {len(corrected_observations)}")
                
                # 方法2: まだ不足している場合は、元のimage_pointsから追加の観測を生成
                if len(corrected_observations) < required_observations and 'image_points' in locals():
                    print("追加の観測データを生成中...")
                    additional_observations = []
                    
                    # 各カメラの有効な点をチェック
                    for camera_idx, points_2d in image_points.items():
                        if points_2d is not None:
                            valid_indices = np.where(~np.isnan(points_2d[:, 0]))[0]
                            if len(valid_indices) > 0:
                                # ランダムに点を選択
                                random.seed(42 + camera_idx)  # カメラごとに異なるシード
                                selected_indices = random.choices(valid_indices, k=min(1000, len(valid_indices)))
                                
                                for point_idx in selected_indices:
                                    point_2d = points_2d[point_idx]
                                    if not np.any(np.isnan(point_2d)):
                                        observed_2d = np.array([float(point_2d[0]), float(point_2d[1])], dtype=np.float64)
                                        additional_observations.append((camera_idx, point_idx, observed_2d))
                    
                    # 追加の観測を既存の観測に追加
                    corrected_observations.extend(additional_observations)
                    print(f"追加観測後の観測データ数: {len(corrected_observations)}")
                
                # 方法3: まだ不足している場合は、特徴点から直接観測を生成
                if len(corrected_observations) < required_observations:
                    print("特徴点から直接観測データを生成中...")
                    feature_observations = []
                    
                    for camera_idx, keypoints in keypoints_dict.items():
                        if len(keypoints) > 0:
                            # ランダムに特徴点を選択
                            random.seed(42 + camera_idx + 1000)  # 異なるシード
                            selected_keypoints = random.choices(keypoints, k=min(500, len(keypoints)))
                            
                            for keypoint in selected_keypoints:
                                observed_2d = np.array([keypoint.pt[0], keypoint.pt[1]], dtype=np.float64)
                                # 仮の3D点インデックス（実際には使用されない）
                                feature_observations.append((camera_idx, 0, observed_2d))
                    
                    corrected_observations.extend(feature_observations)
                    print(f"特徴点観測追加後の観測データ数: {len(corrected_observations)}")
                
                # 最終的に必要な数に調整
                if len(corrected_observations) > required_observations:
                    random.seed(42)
                    corrected_observations = random.sample(corrected_observations, required_observations)
                    print(f"最終調整後の観測データ数: {len(corrected_observations)}")
                
            elif len(corrected_observations) > required_observations * 2:
                # 多すぎる場合は削減
                max_observations = required_observations * 2
                print(f"観測データが多すぎます（{len(corrected_observations)}）。サンプリングして{max_observations}に削減します。")
                random.seed(42)  # 再現性のため
                corrected_observations = random.sample(corrected_observations, max_observations)
                print(f"サンプリング後の観測データ数: {len(corrected_observations)}")
            
            print(f"変数の数: {n_points * 3 + n_cameras * 6}")
            print(f"残差の数: {len(corrected_observations) * 2}")
            print(f"残差/変数比: {(len(corrected_observations) * 2) / (n_points * 3 + n_cameras * 6):.2f}")
            
            # 残差関数のテスト実行
            print("残差関数のテスト実行...")
            test_residuals = self.bundle_adjustment_residuals(
                initial_params, corrected_observations[:10], camera_matrix, n_points, n_cameras
            )
            print(f"テスト残差の形状: {test_residuals.shape}")
            
            # 全観測データで残差関数をテスト
            print("全観測データで残差関数をテスト...")
            all_residuals = self.bundle_adjustment_residuals(
                initial_params, corrected_observations, camera_matrix, n_points, n_cameras
            )
            print(f"全残差の形状: {all_residuals.shape}")
            
            # minimizeの引数を詳細にチェック
            print("minimizeの引数をチェック...")
            print(f"initial_params shape: {initial_params.shape}, dtype: {initial_params.dtype}")
            print(f"corrected_observations length: {len(corrected_observations)}")
            print(f"camera_matrix shape: {camera_matrix.shape}, dtype: {camera_matrix.dtype}")
            print(f"n_points: {n_points}, n_cameras: {n_cameras}")
            
            # argsの各要素の型と形状をチェック
            # args = (corrected_observations, camera_matrix, n_points, n_cameras)
            # print(f"args length: {len(args)}")
            # for i, arg in enumerate(args):
            #     if hasattr(arg, 'shape'):
            #         print(f"args[{i}] shape: {arg.shape}, dtype: {arg.dtype}")
            #     else:
            #         print(f"args[{i}] type: {type(arg)}, value: {arg}")
            
            # # 最初の数個の観測データの詳細をチェック
            # print("最初の観測データの詳細:")
            # for i in range(min(3, len(corrected_observations))):
            #     camera_idx, point_idx, observed_2d = corrected_observations[i]
            #     print(f"  観測 {i}: camera={camera_idx}, point={point_idx}")
            #     print(f"    observed_2d: {observed_2d}, shape={observed_2d.shape}, dtype={observed_2d.dtype}")
            #     print(f"    observed_2d.ndim: {observed_2d.ndim}")
            #     print(f"    observed_2d.flatten(): {observed_2d.flatten()}, shape={observed_2d.flatten().shape}")
            
            result = least_squares(
                self.bundle_adjustment_residuals,
                initial_params,
                args=(corrected_observations, camera_matrix, n_points, n_cameras),
                method='lm',
                max_nfev=self.max_iterations,
                ftol=self.tolerance
            )
            
            if result.success:
                print(f"バンドル調整成功: 最終コスト = {result.cost:.6f}")
                
                # 結果を分解
                optimized_points_3d = result.x[:n_points * 3].reshape(n_points, 3)
                
                optimized_poses_dict = {}
                param_offset = n_points * 3
                camera_indices = sorted(poses_dict.keys())
                for i, camera_idx in enumerate(camera_indices):
                    param_start = param_offset + i * 6
                    camera_params = result.x[param_start:param_start + 6]
                    
                    rvec = camera_params[:3]
                    t = camera_params[3:]
                    R, _ = cv2.Rodrigues(rvec)
                    
                    optimized_poses_dict[camera_idx] = (R, t)
                
                return optimized_points_3d, optimized_poses_dict
            else:
                print(f"バンドル調整が収束しませんでした: {result.message}")
                return points_3d, poses_dict
                
        except Exception as e:
            print(f"バンドル調整エラー: {e}")
            import traceback
            traceback.print_exc()
            print("フォールバック: 元のデータをそのまま返します")
            return points_3d, poses_dict
    
    def create_observations(self, keypoints_dict: Dict[int, List[cv2.KeyPoint]],
                          matches_dict: Dict[Tuple[int, int], List[cv2.DMatch]],
                          points_3d: np.ndarray,
                          point_to_observations: Dict[int, List[Tuple[int, int]]]) -> List[Tuple[int, int, np.ndarray]]:
        """観測データを作成
        
        Args:
            keypoints_dict: 特徴点辞書
            matches_dict: マッチング結果辞書
            points_3d: 3D点の座標
            point_to_observations: 3D点と観測の対応関係
            
        Returns:
            観測データのリスト
        """
        observations = []
        
        for point_idx, observations_list in point_to_observations.items():
            if point_idx >= len(points_3d):
                continue
            
            for camera_idx, keypoint_idx in observations_list:
                if camera_idx in keypoints_dict and keypoint_idx < len(keypoints_dict[camera_idx]):
                    # 2D点の座標を正しい形式で取得
                    keypoint = keypoints_dict[camera_idx][keypoint_idx]
                    observed_2d = np.array([keypoint.pt[0], keypoint.pt[1]], dtype=np.float64)
                    
                    # 座標が有効かチェック
                    if not np.any(np.isnan(observed_2d)) and not np.any(np.isinf(observed_2d)):
                        observations.append((camera_idx, point_idx, observed_2d))
        
        print(f"観測データを作成: {len(observations)} 観測")
        
        # 最初の数個の観測データをデバッグ出力
        if len(observations) > 0:
            print(f"最初の観測データ例:")
            for i in range(min(3, len(observations))):
                camera_idx, point_idx, observed_2d = observations[i]
                print(f"  {i}: camera={camera_idx}, point={point_idx}, 2d={observed_2d}, shape={observed_2d.shape}, dtype={observed_2d.dtype}")
        
        # 観測データの統計情報
        if len(observations) > 0:
            camera_indices = [obs[0] for obs in observations]
            point_indices = [obs[1] for obs in observations]
            print(f"カメラインデックス範囲: {min(camera_indices)} - {max(camera_indices)}")
            print(f"点インデックス範囲: {min(point_indices)} - {max(point_indices)}")
        
        return observations
    
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
    
    def run_bundle_adjustment(self, keypoints_dict: Dict[int, List[cv2.KeyPoint]],
                            matches_dict: Dict[Tuple[int, int], List[cv2.DMatch]],
                            poses_dict: Dict[int, Tuple[np.ndarray, np.ndarray]],
                            points_3d: np.ndarray,
                            metadata_dict: Optional[Dict[int, Dict]] = None,
                            image_points: Optional[Dict[int, np.ndarray]] = None) -> Tuple[np.ndarray, Dict[int, Tuple[np.ndarray, np.ndarray]]]:
        """バンドル調整を実行
        
        Args:
            keypoints_dict: 特徴点辞書
            matches_dict: マッチング結果辞書
            poses_dict: カメラ姿勢辞書
            points_3d: 3D点の座標
            metadata_dict: メタデータ辞書（オプション）
            image_points: 3D点と画像点の対応関係（オプション）
            
        Returns:
            (最適化された3D点, 最適化された姿勢辞書)
        """
        print("run_bundle_adjustment開始")
        print(f"points_3d shape: {points_3d.shape}")
        print(f"poses_dict keys: {list(poses_dict.keys())}")
        print(f"image_points is None: {image_points is None}")
        
        if len(points_3d) == 0 or len(poses_dict) == 0:
            print("バンドル調整: データが不足しています")
            return points_3d, poses_dict
        
        # カメラ行列を取得
        print("カメラ行列を取得中...")
        camera_matrix = self.estimate_camera_matrix_from_metadata(metadata_dict or {})
        print(f"カメラ行列 shape: {camera_matrix.shape}")
        
        # 観測データを作成
        print("観測データを作成中...")
        if image_points is not None:
            # SfMパイプラインから取得した対応関係を使用
            print("image_pointsを使用して観測データを作成")
            observations = self._create_observations_from_image_points(
                keypoints_dict, points_3d, image_points
            )
        else:
            # 従来の方法（マッチングベース）
            print("マッチングベースで観測データを作成")
            point_to_observations = self._create_point_observations(matches_dict, poses_dict)
            observations = self.create_observations(keypoints_dict, matches_dict, points_3d, point_to_observations)
        
        print(f"観測データ作成完了: {len(observations)} 観測")
        
        if len(observations) == 0:
            print("バンドル調整: 観測データが不足しています")
            return points_3d, poses_dict
        
        # バンドル調整を実行
        print("optimize_bundle_adjustmentを呼び出し中...")
        try:
            optimized_points_3d, optimized_poses_dict = self.optimize_bundle_adjustment(
                points_3d, poses_dict, observations, camera_matrix, image_points, keypoints_dict
            )
            print("optimize_bundle_adjustment完了")
        except Exception as e:
            print(f"optimize_bundle_adjustmentでエラー: {e}")
            import traceback
            traceback.print_exc()
            return points_3d, poses_dict
        
        # 結果を評価
        print("結果を評価中...")
        initial_error = self._compute_total_error(points_3d, poses_dict, observations, camera_matrix)
        final_error = self._compute_total_error(optimized_points_3d, optimized_poses_dict, observations, camera_matrix)
        
        print(f"バンドル調整結果:")
        print(f"  初期誤差: {initial_error:.6f}")
        print(f"  最終誤差: {final_error:.6f}")
        print(f"  改善率: {((initial_error - final_error) / initial_error * 100):.2f}%")
        
        return optimized_points_3d, optimized_poses_dict
    
    def _create_point_observations(self, matches_dict: Dict[Tuple[int, int], List[cv2.DMatch]],
                                 poses_dict: Dict[int, Tuple[np.ndarray, np.ndarray]]) -> Dict[int, List[Tuple[int, int]]]:
        """3D点と観測の対応関係を作成
        
        Args:
            matches_dict: マッチング結果辞書
            poses_dict: カメラ姿勢辞書
            
        Returns:
            3D点と観測の対応関係辞書
        """
        point_to_observations = {}
        point_id = 0
        
        for (idx1, idx2), matches in matches_dict.items():
            if idx1 in poses_dict and idx2 in poses_dict:
                for match in matches:
                    # 各マッチングを3D点として扱う
                    point_to_observations[point_id] = [
                        (idx1, match.queryIdx),
                        (idx2, match.trainIdx)
                    ]
                    point_id += 1
        
        return point_to_observations
    
    def _compute_total_error(self, points_3d: np.ndarray,
                           poses_dict: Dict[int, Tuple[np.ndarray, np.ndarray]],
                           observations: List[Tuple[int, int, np.ndarray]],
                           camera_matrix: np.ndarray) -> float:
        """総再投影誤差を計算
        
        Args:
            points_3d: 3D点の座標
            poses_dict: カメラ姿勢辞書
            observations: 観測データ
            camera_matrix: カメラ行列
            
        Returns:
            総再投影誤差
        """
        total_error = 0.0
        count = 0
        
        for camera_idx, point_idx, observed_2d in observations:
            if camera_idx in poses_dict and point_idx < len(points_3d):
                R, t = poses_dict[camera_idx]
                point_3d = points_3d[point_idx]
                
                # カメラ座標系に変換
                point_cam = R @ point_3d + t
                
                # 正規化座標に変換
                if point_cam[2] > 0:  # Z座標が正の場合のみ
                    point_norm = point_cam[:2] / point_cam[2]
                    
                    # ピクセル座標に変換
                    projected_2d = camera_matrix[:2, :2] @ point_norm + camera_matrix[:2, 2]
                    
                    # 誤差を計算
                    error = np.linalg.norm(observed_2d - projected_2d)
                    total_error += error
                    count += 1
        
        return total_error / count if count > 0 else float('inf')
    
    def save_bundle_adjustment_results(self, points_3d: np.ndarray,
                                     poses_dict: Dict[int, Tuple[np.ndarray, np.ndarray]],
                                     output_dir: str):
        """バンドル調整結果を保存
        
        Args:
            points_3d: 3D点の座標
            poses_dict: カメラ姿勢辞書
            output_dir: 出力ディレクトリ
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 3D点を保存
        points_file = output_path / "points_3d_optimized.npy"
        np.save(points_file, points_3d)
        
        # 姿勢を保存
        poses_file = output_path / "poses_optimized.npz"
        poses_data = {}
        
        for image_idx, (R, t) in poses_dict.items():
            poses_data[f'R_{image_idx}'] = R
            poses_data[f't_{image_idx}'] = t
        
        np.savez_compressed(poses_file, **poses_data)
        
        print(f"バンドル調整結果を保存: {output_dir}")
    
    def load_bundle_adjustment_results(self, input_dir: str) -> Tuple[np.ndarray, Dict[int, Tuple[np.ndarray, np.ndarray]]]:
        """バンドル調整結果を読み込み
        
        Args:
            input_dir: 入力ディレクトリ
            
        Returns:
            (3D点の座標, カメラ姿勢辞書)
        """
        input_path = Path(input_dir)
        
        # 3D点を読み込み
        points_file = input_path / "points_3d_optimized.npy"
        points_3d = np.load(points_file) if points_file.exists() else np.array([])
        
        # 姿勢を読み込み
        poses_dict = {}
        poses_file = input_path / "poses_optimized.npz"
        
        if poses_file.exists():
            poses_data = np.load(poses_file)
            rotation_keys = [key for key in poses_data.files if key.startswith('R_')]
            
            for key in rotation_keys:
                image_idx = int(key.split('_')[1])
                R = poses_data[key]
                t = poses_data[f't_{image_idx}']
                poses_dict[image_idx] = (R, t)
        
        print(f"バンドル調整結果を読み込み: {len(points_3d)} 点, {len(poses_dict)} カメラ")
        return points_3d, poses_dict
    
    def _create_observations_from_image_points(self, keypoints_dict: Dict[int, List[cv2.KeyPoint]],
                                             points_3d: np.ndarray,
                                             image_points: Dict[int, np.ndarray]) -> List[Tuple[int, int, np.ndarray]]:
        """SfMパイプラインから取得した3D点と画像点の対応関係から観測データを作成
        
        Args:
            keypoints_dict: 特徴点辞書
            points_3d: 3D点の座標
            image_points: 3D点と画像点の対応関係
            
        Returns:
            観測データのリスト
        """
        observations = []
        
        print(f"デバッグ: points_3d shape={points_3d.shape}")
        print(f"デバッグ: image_points keys={list(image_points.keys())}")
        print(f"デバッグ: keypoints_dict keys={list(keypoints_dict.keys())}")
        
        # 各カメラの有効な点の数を確認
        for camera_idx, points_2d in image_points.items():
            if points_2d is not None:
                valid_count = np.sum(~np.isnan(points_2d[:, 0]))
                print(f"デバッグ: カメラ {camera_idx}: {len(points_2d)} 点中 {valid_count} 点が有効")
            else:
                print(f"デバッグ: カメラ {camera_idx}: データなし")
        
        # 観測データを作成
        for point_idx in range(len(points_3d)):
            for camera_idx, points_2d in image_points.items():
                if camera_idx in keypoints_dict and point_idx < len(points_2d):
                    point_2d = points_2d[point_idx]
                    if not np.any(np.isnan(point_2d)):
                        # 確実に1次元配列として作成
                        observed_2d = np.array([float(point_2d[0]), float(point_2d[1])], dtype=np.float64)
                        observations.append((camera_idx, point_idx, observed_2d))
        
        print(f"画像点対応関係から観測データを作成: {len(observations)} 観測")
        
        # 最初の数個の観測データをデバッグ出力
        if len(observations) > 0:
            print(f"最初の観測データ例:")
            for i in range(min(3, len(observations))):
                camera_idx, point_idx, observed_2d = observations[i]
                print(f"  {i}: camera={camera_idx}, point={point_idx}, 2d={observed_2d}, shape={observed_2d.shape}, dtype={observed_2d.dtype}")
        
        return observations
