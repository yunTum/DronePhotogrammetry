#!/usr/bin/env python3
"""
Structure from Motion (SfM) パイプラインモジュール
"""

import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import os
import json
from datetime import datetime
import time

from .image_loader import ImageLoader
from .metadata_extractor import MetadataExtractor
from .feature_extractor import FeatureExtractor
from .feature_matcher import FeatureMatcher
from .pose_estimator import PoseEstimator
from .bundle_adjuster import BundleAdjuster
from .point_cloud_exporter import PointCloudExporter
from .logger import SfMLogger


class SFMPipeline:
    """SfMパイプラインクラス"""
    
    def __init__(self, output_dir: str = "output/sfm_pipeline", 
                 log_dir: str = "logs", project_name: str = "sfm_pipeline"):
        """初期化
        
        Args:
            output_dir: 出力ディレクトリ
            log_dir: ログディレクトリ
            project_name: プロジェクト名
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # SfMLoggerを初期化
        self.logger = SfMLogger(log_dir=log_dir, project_name=project_name)
        
        # 各モジュールを初期化（ロガーを渡す）
        self.image_loader = ImageLoader()
        self.metadata_extractor = MetadataExtractor()
        self.feature_extractor = FeatureExtractor()
        self.feature_matcher = FeatureMatcher()
        self.pose_estimator = PoseEstimator()
        self.bundle_adjuster = BundleAdjuster()
        self.point_cloud_exporter = PointCloudExporter(str(self.output_dir))
        
        # データを保持
        self.images = {}
        self.image_paths = {}  # 画像パスを保持
        self.metadata_dict = {}
        self.keypoints_dict = {}
        self.descriptors_dict = {}
        self.matches_dict = {}
        self.poses_dict = {}
        self.points_3d = np.array([])
        self.point_colors = None
        self.image_points = {}
        
        # パイプラインの実行結果
        self.pipeline_results = {}
        
        print(f"SfMパイプラインを初期化: 出力ディレクトリ = {output_dir}")
        self.logger.log_step("pipeline_initialization", {
            "output_dir": str(output_dir),
            "log_dir": log_dir,
            "project_name": project_name
        })
    
    def load_images(self, image_dir: str, max_images: Optional[int] = None) -> Dict[int, np.ndarray]:
        """画像を読み込み
        
        Args:
            image_dir: 画像ディレクトリ
            max_images: 最大画像数（オプション）
            
        Returns:
            画像辞書
        """
        start_time = time.time()
        print(f"画像読み込みを開始: {image_dir}")
        
        # ImageLoaderのload_images_from_directoryは辞書を返す
        images_dict, paths_dict = self.image_loader.load_images_from_directory(image_dir)
        
        # max_imagesが指定されている場合は制限
        if max_images is not None and len(images_dict) > max_images:
            limited_images = {}
            limited_paths = {}
            for i in range(max_images):
                if i in images_dict:
                    limited_images[i] = images_dict[i]
                    limited_paths[i] = paths_dict[i]
            images_dict = limited_images
            paths_dict = limited_paths
            print(f"画像数を制限: {max_images} 画像")
        
        # データを保持
        self.images = images_dict
        self.image_paths = paths_dict
        
        processing_time = time.time() - start_time
        print(f"画像読み込み完了: {len(self.images)} 画像")
        
        # ログに記録
        self.logger.log_step("image_loading", {
            "image_dir": image_dir,
            "total_images": len(self.images),
            "max_images": max_images,
            "processing_time": processing_time,
            "image_paths": list(paths_dict.values())
        })
        
        return self.images
    
    def extract_metadata(self) -> Dict[int, Dict]:
        """メタデータを抽出
        
        Returns:
            メタデータ辞書
        """
        if not self.images or not self.image_paths:
            print("画像が読み込まれていません")
            return {}
        
        start_time = time.time()
        print("メタデータ抽出を開始")
        
        self.metadata_dict = {}
        for image_idx, image_path in self.image_paths.items():
            metadata = self.metadata_extractor.extract_metadata_from_image(image_path)
            self.metadata_dict[image_idx] = metadata
        
        # メタデータを保存
        metadata_file = self.output_dir / "metadata.json"
        self.metadata_extractor.save_metadata_json(self.metadata_dict, str(metadata_file))
        
        processing_time = time.time() - start_time
        print(f"メタデータ抽出完了: {len(self.metadata_dict)} 画像")
        
        # ログに記録
        self.logger.log_step("metadata_extraction", {
            "total_images": len(self.metadata_dict),
            "processing_time": processing_time,
            "metadata_file": str(metadata_file)
        })
        
        return self.metadata_dict
    
    def extract_features(self, detector_type: str = 'SIFT', 
                        max_features: int = 2000) -> Tuple[Dict[int, List[cv2.KeyPoint]], Dict[int, np.ndarray]]:
        """特徴点を抽出
        
        Args:
            detector_type: 検出器の種類
            max_features: 最大特徴点数
            
        Returns:
            (特徴点辞書, ディスクリプタ辞書)
        """
        if not self.images:
            print("画像が読み込まれていません")
            return {}, {}
        
        start_time = time.time()
        print(f"特徴点抽出を開始: {detector_type}, max_features={max_features}")
        
        # 検出器を再初期化
        self.feature_extractor = FeatureExtractor(detector_type, max_features)
        # 前処理
        self.feature_extractor.enable_all_preprocessing()
        
        # 特徴点抽出
        self.keypoints_dict, self.descriptors_dict = self.feature_extractor.extract_features_batch(
            self.images, str(self.output_dir / "keypoints")
        )
        
        # 特徴点データを保存
        features_dir = self.output_dir / "features"
        self.feature_extractor.save_features(
            self.keypoints_dict, self.descriptors_dict, str(features_dir)
        )
        
        processing_time = time.time() - start_time
        print(f"特徴点抽出完了: {len(self.keypoints_dict)} 画像")
        
        # ログに記録
        total_keypoints = sum(len(kpts) for kpts in self.keypoints_dict.values())
        self.logger.log_step("feature_extraction", {
            "detector_type": detector_type,
            "max_features": max_features,
            "total_images": len(self.keypoints_dict),
            "total_keypoints": total_keypoints,
            "avg_keypoints_per_image": total_keypoints / len(self.keypoints_dict) if self.keypoints_dict else 0,
            "processing_time": processing_time,
            "features_dir": str(features_dir)
        })
        
        return self.keypoints_dict, self.descriptors_dict
    
    def match_features(self, matcher_type: str = 'FLANN', 
                      ratio_threshold: float = 0.7, 
                      min_matches: int = 10) -> Dict[Tuple[int, int], List[cv2.DMatch]]:
        """特徴点をマッチング
        
        Args:
            matcher_type: マッチャーの種類
            ratio_threshold: Lowe's ratio testの閾値
            min_matches: 最小マッチング数
            
        Returns:
            マッチング結果辞書
        """
        if not self.descriptors_dict:
            print("特徴点が抽出されていません")
            return {}
        
        start_time = time.time()
        print(f"特徴点マッチングを開始: {matcher_type}, ratio={ratio_threshold}")
        
        # マッチャーを再初期化
        self.feature_matcher = FeatureMatcher(matcher_type, ratio_threshold, min_matches)
        
        # 全ペアマッチング
        self.matches_dict = self.feature_matcher.match_all_pairs(self.descriptors_dict)
        
        # マッチング結果を保存
        matches_dir = self.output_dir / "matches"
        self.feature_matcher.save_matches(self.matches_dict, str(matches_dir))
        
        # マッチング可視化
        self._visualize_matches()
        
        processing_time = time.time() - start_time
        print(f"特徴点マッチング完了: {len(self.matches_dict)} ペア")
        
        # ログに記録
        total_matches = sum(len(matches) for matches in self.matches_dict.values())
        self.logger.log_step("feature_matching", {
            "matcher_type": matcher_type,
            "ratio_threshold": ratio_threshold,
            "min_matches": min_matches,
            "total_pairs": len(self.matches_dict),
            "total_matches": total_matches,
            "avg_matches_per_pair": total_matches / len(self.matches_dict) if self.matches_dict else 0,
            "processing_time": processing_time,
            "matches_dir": str(matches_dir)
        })
        
        return self.matches_dict
    
    def estimate_poses(self) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
        """カメラ姿勢を推定
        
        Returns:
            姿勢辞書
        """
        if not self.matches_dict or not self.keypoints_dict:
            print("マッチング結果または特徴点が不足しています")
            return {}
        
        start_time = time.time()
        print("姿勢推定を開始")
        
        # カメラ行列を推定
        camera_matrix = self.pose_estimator.estimate_camera_matrix_from_metadata(self.metadata_dict)
        
        # 初期姿勢を推定
        self.poses_dict = self.pose_estimator.estimate_initial_poses(
            self.keypoints_dict, self.descriptors_dict, self.matches_dict, camera_matrix, self.metadata_dict
        )
        
        # 初期姿勢推定後の正規化（3D点生成前に実行）
        if len(self.poses_dict) > 0:
            print("初期姿勢推定後の正規化を開始")
            self.poses_dict = self.pose_estimator.normalize_all_poses(self.poses_dict, camera_matrix, self.metadata_dict)
            print("初期姿勢推定後の正規化完了")
        
        # 姿勢データを保存
        poses_dir = self.output_dir / "poses"
        self.pose_estimator.save_poses(self.poses_dict, str(poses_dir))
        
        processing_time = time.time() - start_time
        print(f"姿勢推定完了: {len(self.poses_dict)} カメラ")
        
        # ログに記録
        self.logger.log_step("pose_estimation", {
            "total_cameras": len(self.poses_dict),
            "camera_matrix_shape": camera_matrix.shape if camera_matrix is not None else None,
            "processing_time": processing_time,
            "poses_dir": str(poses_dir),
            "estimated_cameras": list(self.poses_dict.keys())
        })
        
        return self.poses_dict
    
    def triangulate_points(self) -> np.ndarray:
        """3D点を三角測量
        
        Returns:
            3D点の座標
        """
        if not self.poses_dict or not self.matches_dict:
            print("姿勢またはマッチング結果が不足しています")
            return np.array([])
        
        start_time = time.time()
        print("三角測量を開始")
        print(f"利用可能な姿勢: {list(self.poses_dict.keys())}")
        print(f"利用可能なマッチング: {list(self.matches_dict.keys())}")
        
        # カメラ行列を推定
        camera_matrix = self.pose_estimator.estimate_camera_matrix_from_metadata(self.metadata_dict)
        
        # 3D点を計算
        points_3d_list = []
        image_points_dict = {}  # 3D点と画像点の対応関係を保存
        
        # 各カメラの画像点を初期化
        for camera_idx in self.poses_dict.keys():
            image_points_dict[camera_idx] = []
        
        point_id = 0  # 3D点のID
        
        # より多くのマッチングペアを処理するために、追加のマッチングを生成
        additional_matches = self._generate_additional_matches()
        all_matches = {**self.matches_dict, **additional_matches}
        
        print(f"元のマッチング数: {len(self.matches_dict)}")
        print(f"追加マッチング数: {len(additional_matches)}")
        print(f"総マッチング数: {len(all_matches)}")
        
        for (idx1, idx2), matches in all_matches.items():
            print(f"マッチングペア ({idx1}, {idx2}): {len(matches)} マッチング")
            
            if idx1 in self.poses_dict and idx2 in self.poses_dict:
                print(f"  両方の姿勢が利用可能")
                
                # 対応点の座標を取得
                pts1, pts2 = self.feature_matcher.get_matched_points(
                    self.keypoints_dict[idx1], self.keypoints_dict[idx2], matches
                )
                
                print(f"  対応点: {len(pts1)} 点")
                
                if len(pts1) > 0 and len(pts2) > 0:
                    # 姿勢を取得
                    R1, t1 = self.poses_dict[idx1]
                    R2, t2 = self.poses_dict[idx2]
                    
                    print(f"  姿勢1: R shape={R1.shape}, t shape={t1.shape}")
                    print(f"  姿勢2: R shape={R2.shape}, t shape={t2.shape}")
                    
                    # 三角測量
                    points_3d = self.pose_estimator.triangulate_points(
                        pts1, pts2, R1, t1, R2, t2, camera_matrix
                    )
                    
                    if len(points_3d) > 0:
                        # Cheirality制約をチェック
                        # valid_indices = self.pose_estimator.check_cheirality(points_3d, R1, t1)
                        valid_indices = self.pose_estimator.check_cheirality_relaxed(points_3d, R1, t1)

                        if len(valid_indices) > 0:
                            valid_points_3d = points_3d[valid_indices]
                            points_3d_list.append(valid_points_3d)
                            
                            # 画像点の対応関係を保存
                            for i, valid_idx in enumerate(valid_indices):
                                # 各カメラの画像点を初期化（必要に応じて拡張）
                                while len(image_points_dict[idx1]) <= point_id + i:
                                    image_points_dict[idx1].append(None)
                                while len(image_points_dict[idx2]) <= point_id + i:
                                    image_points_dict[idx2].append(None)
                                
                                # 有効な画像点を保存
                                image_points_dict[idx1][point_id + i] = pts1[valid_idx]
                                image_points_dict[idx2][point_id + i] = pts2[valid_idx]
                            
                            point_id += len(valid_indices)
                            print(f"  有効な3D点: {len(valid_indices)} 点")
                        else:
                            print(f"  Cheirality制約で全ての点が除外されました")
                    else:
                        print(f"  三角測量で3D点が生成されませんでした")
                else:
                    print(f"  対応点が不足しています")
            else:
                print(f"  姿勢が不足: idx1={idx1 in self.poses_dict}, idx2={idx2 in self.poses_dict}")
        
        if points_3d_list:
            self.points_3d = np.vstack(points_3d_list)
            # 画像点の対応関係をNumPy配列に変換
            self.image_points = {}
            for camera_idx, points_list in image_points_dict.items():
                if points_list:
                    # NoneをNaNに変換してNumPy配列に変換
                    points_array = []
                    for point in points_list:
                        if point is None:
                            points_array.append([np.nan, np.nan])
                        else:
                            points_array.append(point)
                    self.image_points[camera_idx] = np.array(points_array)
            
            print(f"三角測量完了: {len(self.points_3d)} 3D点")
            print(f"画像点対応関係: {len(self.image_points)} カメラ")
            
            # デバッグ情報を追加
            for camera_idx, points_array in self.image_points.items():
                valid_points = np.sum(~np.isnan(points_array[:, 0]))
                print(f"  カメラ {camera_idx}: {len(points_array)} 点中 {valid_points} 点が有効")
        else:
            self.points_3d = np.array([])
            self.image_points = {}
            print("三角測量: 有効な3D点が生成されませんでした")
        
        processing_time = time.time() - start_time
        
        # ログに記録
        self.logger.log_triangulation(
            points_3d_count=len(self.points_3d),
            reprojection_error=0.0,  # 再投影誤差は後で計算
            processing_time=processing_time
        )
        
        return self.points_3d
    
    def run_bundle_adjustment(self) -> Tuple[np.ndarray, Dict[int, Tuple[np.ndarray, np.ndarray]]]:
        """バンドル調整を実行
        
        Returns:
            (最適化された3D点, 最適化された姿勢辞書)
        """
        if len(self.points_3d) == 0 or len(self.poses_dict) == 0:
            print("3D点または姿勢が不足しています")
            return self.points_3d, self.poses_dict
        
        start_time = time.time()
        print("バンドル調整を開始")
        
        try:
            # バンドル調整を実行（image_pointsを渡す）
            optimized_points_3d, optimized_poses_dict = self.bundle_adjuster.run_bundle_adjustment(
                self.keypoints_dict, self.matches_dict, self.poses_dict, 
                self.points_3d, self.metadata_dict, self.image_points
            )
            
            # 結果を更新
            self.points_3d = optimized_points_3d
            self.poses_dict = optimized_poses_dict
            
            # 結果を保存
            bundle_dir = self.output_dir / "bundle_adjustment"
            self.bundle_adjuster.save_bundle_adjustment_results(
                self.points_3d, self.poses_dict, str(bundle_dir)
            )
            
            processing_time = time.time() - start_time
            print("バンドル調整完了")
            
            # ログに記録
            self.logger.log_bundle_adjustment(
                initial_error=0.0,  # 初期誤差は後で計算
                final_error=0.0,    # 最終誤差は後で計算
                iterations=0,       # 反復回数は後で計算
                processing_time=processing_time,
                convergence=True
            )
            
            return self.points_3d, self.poses_dict
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"バンドル調整でエラーが発生しました: {e}")
            print("元のデータをそのまま使用します")
            
            # エラーをログに記録
            self.logger.log_bundle_adjustment(
                initial_error=0.0,
                final_error=0.0,
                iterations=0,
                processing_time=processing_time,
                convergence=False
            )
            
            return self.points_3d, self.poses_dict
    
    def create_colored_point_cloud(self) -> np.ndarray:
        """色付き点群を作成"""
        print("色付き点群を作成中...")
        if self.points_3d is not None and len(self.points_3d) > 0:
            self.point_colors = self.point_cloud_exporter.create_colored_point_cloud(
                self.points_3d, self.images, self.poses_dict, self.image_points
            )
            print("色付き点群作成完了")
            return self.point_colors
        else:
            print("警告: 3D点が存在しないため色付き点群を作成できません")
            return None
    
    def export_results(self, base_filename: str = "sfm_results") -> Dict[str, str]:
        """結果を出力"""
        print("結果を出力中...")
        
        # メタデータを準備
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "num_images": len(self.images),
            "num_points_3d": len(self.points_3d) if self.points_3d is not None else 0,
            "num_cameras": len(self.poses_dict),
            "num_matches": len(self.matches_dict)
        }
        
        # カメラ姿勢情報を準備
        camera_poses_export = {}
        for img_name, pose in self.poses_dict.items():
            camera_poses_export[img_name] = {
                "R": pose[0].tolist(),
                "t": pose[1].tolist(),
                "K": self.metadata_dict[img_name]['K'].tolist() if 'K' in self.metadata_dict[img_name] else None
            }
        
        # 点群データを出力
        output_files = self.point_cloud_exporter.export_point_cloud_with_metadata(
            points_3d=self.points_3d,
            colors=self.point_colors,
            camera_poses=camera_poses_export,
            metadata=metadata,
            base_filename=base_filename
        )
        
        # パイプライン結果を保存
        pipeline_file = self.output_dir / f"{base_filename}_pipeline.json"
        self.pipeline_results = {
            "metadata": metadata,
            "camera_poses": camera_poses_export,
            "output_files": output_files
        }
        
        with open(pipeline_file, 'w') as f:
            json.dump(self.pipeline_results, f, indent=2, default=str)
        
        output_files['pipeline'] = str(pipeline_file)
        print(f"パイプライン結果を保存しました: {pipeline_file}")
        
        return output_files
    
    def run_full_pipeline(self, image_dir: str, 
                         detector_type: str = 'SIFT',
                         max_features: int = 100000,
                         matcher_type: str = 'FLANN',
                         ratio_threshold: float = 0.7,
                         min_matches: int = 8,
                         max_images: Optional[int] = None) -> Dict:
        """完全なSfMパイプラインを実行
        
        Args:
            image_dir: 画像ディレクトリ
            detector_type: 特徴点検出器の種類
            max_features: 最大特徴点数
            matcher_type: マッチャーの種類
            ratio_threshold: Lowe's ratio testの閾値
            min_matches: 最小マッチング数
            max_images: 最大画像数
            
        Returns:
            結果辞書
        """
        pipeline_start_time = time.time()
        print("=" * 50)
        print("SfMパイプラインを開始")
        print("=" * 50)
        
        try:
            # 1. 画像読み込み
            self.load_images(image_dir, max_images)
            
            # 2. メタデータ抽出
            self.extract_metadata()
            
            # 3. 特徴点抽出
            self.extract_features(detector_type, max_features)
            
            # 4. 特徴点マッチング
            self.match_features(matcher_type, ratio_threshold, min_matches)
            
            # 5. 姿勢推定
            self.estimate_poses()
            
            # 6. 三角測量
            self.triangulate_points()
            
            # 7. バンドル調整
            # self.run_bundle_adjustment()
            
            # 8. 色付き点群作成
            self.create_colored_point_cloud()
            
            # 9. 結果出力
            output_files = self.export_results()
            
            # 全体の処理時間を計算
            total_processing_time = time.time() - pipeline_start_time
            
            # 結果をまとめる
            results = {
                'images': len(self.images),
                'keypoints': {idx: len(kpts) for idx, kpts in self.keypoints_dict.items()},
                'matches': len(self.matches_dict),
                'poses': len(self.poses_dict),
                'points_3d': len(self.points_3d),
                'output_dir': str(self.output_dir),
                'total_processing_time': total_processing_time
            }
            
            # 結果を保存
            results_file = self.output_dir / "pipeline_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            # 最終結果をログに記録
            output_file_list = list(output_files.values()) if output_files else []
            self.logger.log_final_results(
                total_points=len(self.points_3d),
                total_cameras=len(self.poses_dict),
                total_processing_time=total_processing_time,
                output_files=output_file_list
            )
            
            print("=" * 50)
            print("SfMパイプライン完了")
            print(f"結果: {results}")
            print("=" * 50)
            
            return results
            
        except Exception as e:
            total_processing_time = time.time() - pipeline_start_time
            print(f"SfMパイプラインエラー: {e}")
            
            # エラーをログに記録
            self.logger.log_step("pipeline_error", {
                "error_message": str(e),
                "total_processing_time": total_processing_time
            }, level="ERROR")
            
            return {}
        
        finally:
            # ログのクリーンアップ
            self.logger.cleanup()
    
    def _visualize_matches(self):
        """マッチング結果を可視化"""
        if not self.images or not self.matches_dict:
            return
        
        matches_vis_dir = self.output_dir / "matches_visualization"
        matches_vis_dir.mkdir(exist_ok=True)
        
        for (idx1, idx2), matches in self.matches_dict.items():
            if idx1 in self.images and idx2 in self.images:
                image1 = self.images[idx1]
                image2 = self.images[idx2]
                keypoints1 = self.keypoints_dict[idx1]
                keypoints2 = self.keypoints_dict[idx2]
                
                output_path = matches_vis_dir / f"matches_{idx1}_{idx2}.jpg"
                self.feature_matcher.visualize_matches(
                    image1, image2, keypoints1, keypoints2, matches, str(output_path)
                )
    
    def load_saved_data(self):
        """保存されたデータを読み込み"""
        # メタデータを読み込み
        metadata_file = self.output_dir / "metadata.json"
        if metadata_file.exists():
            self.metadata_dict = self.metadata_extractor.load_metadata_json(str(metadata_file))
        
        # 特徴点を読み込み
        features_dir = self.output_dir / "features"
        if features_dir.exists():
            self.keypoints_dict, self.descriptors_dict = self.feature_extractor.load_features(str(features_dir))
        
        # マッチング結果を読み込み
        matches_dir = self.output_dir / "matches"
        if matches_dir.exists():
            self.matches_dict = self.feature_matcher.load_matches(str(matches_dir))
        
        # 姿勢を読み込み
        poses_dir = self.output_dir / "poses"
        if poses_dir.exists():
            self.poses_dict = self.pose_estimator.load_poses(str(poses_dir))
        
        # バンドル調整結果を読み込み
        bundle_dir = self.output_dir / "bundle_adjustment"
        if bundle_dir.exists():
            self.points_3d, self.poses_dict = self.bundle_adjuster.load_bundle_adjustment_results(str(bundle_dir))
        
        print("保存されたデータを読み込み完了")

    def _generate_additional_matches(self) -> Dict[Tuple[int, int], List[cv2.DMatch]]:
        """追加のマッチングを生成して3D点の数を増やす
        
        Returns:
            追加のマッチング辞書
        """
        additional_matches = {}
        
        # 利用可能なカメラの組み合わせを生成
        camera_indices = list(self.poses_dict.keys())
        
        for i in range(len(camera_indices)):
            for j in range(i + 1, len(camera_indices)):
                idx1, idx2 = camera_indices[i], camera_indices[j]
                
                # 既にマッチングが存在する場合はスキップ
                if (idx1, idx2) in self.matches_dict or (idx2, idx1) in self.matches_dict:
                    continue
                
                # 新しいマッチングを生成
                try:
                    matches = self.feature_matcher.match_features(
                        self.descriptors_dict[idx1], 
                        self.descriptors_dict[idx2],
                        ratio_threshold=0.8,  # より緩い閾値
                        min_matches=5  # より少ない最小マッチング数
                    )
                    
                    if len(matches) >= 5:
                        additional_matches[(idx1, idx2)] = matches
                        print(f"追加マッチング生成: ({idx1}, {idx2}) -> {len(matches)} マッチング")
                        
                except Exception as e:
                    print(f"追加マッチング生成エラー ({idx1}, {idx2}): {e}")
                    continue
        
        return additional_matches


if __name__ == "__main__":
    # テスト用コード
    print("SfMパイプラインのテストを開始")
    
    # パイプラインを初期化（ログ機能付き）
    pipeline = SFMPipeline(
        output_dir="output/sfm_test",
        log_dir="output/sfm_test/logs",
        project_name="sfm_pipeline_test"
    )

    # 画像ディレクトリを指定（実際のパスに変更してください）
    image_dir = "../images"  # 相対パスで指定
    
    try:
        # 完全なパイプラインを実行
        results = pipeline.run_full_pipeline(
            image_dir=image_dir,
            detector_type='SIFT',
            max_features=10000,
            matcher_type='FLANN',
            ratio_threshold=0.9,
            min_matches=8,
            max_images=5  # テスト用に5枚に制限
        )
        
        print("テスト完了")
        print(f"結果: {results}")
        
        # 点群データを出力
        if len(pipeline.points_3d) > 0:
            output_files = pipeline.export_results("test_results")
            print(f"出力ファイル: {output_files}")
        
    except Exception as e:
        print(f"テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
