import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np


class SfMLogger:
    """SfM処理の統計情報とログを管理するクラス"""
    
    def __init__(self, log_dir: str = "logs", project_name: str = "sfm_project"):
        """初期化
        
        Args:
            log_dir: ログディレクトリのパス
            project_name: プロジェクト名
        """
        self.log_dir = Path(log_dir)
        self.project_name = project_name
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # ログディレクトリを作成
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # セッション固有のログディレクトリ
        self.session_log_dir = self.log_dir / f"{project_name}_{self.session_id}"
        self.session_log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログファイルの設定
        self.setup_logging()
        
        # 統計情報を格納する辞書
        self.stats = {
            "session_info": {
                "project_name": project_name,
                "session_id": self.session_id,
                "start_time": datetime.now().isoformat(),
                "end_time": None
            },
            "processing_steps": [],
            "feature_extraction": {},
            "matching": {},
            "pose_estimation": {},
            "triangulation": {},
            "bundle_adjustment": {},
            "final_results": {}
        }
        
        print(f"SfM Logger初期化: {self.session_log_dir}")
    
    def setup_logging(self):
        """ログ設定を初期化"""
        log_file = self.session_log_dir / "sfm_processing.log"
        
        # ログフォーマット
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # ファイルハンドラー
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # ロガーの設定
        self.logger = logging.getLogger(f"SfM_{self.session_id}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 重複ログを防ぐ
        self.logger.propagate = False
    
    def log_step(self, step_name: str, details: Dict[str, Any], level: str = "INFO"):
        """処理ステップをログに記録
        
        Args:
            step_name: ステップ名
            details: 詳細情報
            level: ログレベル
        """
        timestamp = datetime.now().isoformat()
        
        # ステップ情報を統計に追加
        step_info = {
            "timestamp": timestamp,
            "step_name": step_name,
            "details": details
        }
        self.stats["processing_steps"].append(step_info)
        
        # ログメッセージを作成
        message = f"STEP: {step_name} - {json.dumps(details, ensure_ascii=False, default=str)}"
        
        # ログレベルに応じて出力
        if level.upper() == "DEBUG":
            self.logger.debug(message)
        elif level.upper() == "WARNING":
            self.logger.warning(message)
        elif level.upper() == "ERROR":
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def log_feature_extraction(self, image_id: int, keypoints_count: int, 
                              descriptors_shape: tuple, processing_time: float):
        """特徴点抽出の統計を記録
        
        Args:
            image_id: 画像ID
            keypoints_count: 特徴点数
            descriptors_shape: ディスクリプタの形状
            processing_time: 処理時間（秒）
        """
        stats = {
            "image_id": image_id,
            "keypoints_count": keypoints_count,
            "descriptors_shape": descriptors_shape,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        if "images" not in self.stats["feature_extraction"]:
            self.stats["feature_extraction"]["images"] = {}
        
        self.stats["feature_extraction"]["images"][image_id] = stats
        
        self.log_step("feature_extraction", stats)
    
    def log_matching(self, image_pair: tuple, matches_count: int, 
                    inliers_count: int, processing_time: float):
        """マッチングの統計を記録
        
        Args:
            image_pair: 画像ペア (image1_id, image2_id)
            matches_count: マッチング数
            inliers_count: インライア数
            processing_time: 処理時間（秒）
        """
        pair_key = f"{image_pair[0]}_{image_pair[1]}"
        stats = {
            "image_pair": image_pair,
            "matches_count": matches_count,
            "inliers_count": inliers_count,
            "inlier_ratio": inliers_count / matches_count if matches_count > 0 else 0,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        if "pairs" not in self.stats["matching"]:
            self.stats["matching"]["pairs"] = {}
        
        self.stats["matching"]["pairs"][pair_key] = stats
        
        self.log_step("matching", stats)
    
    def log_pose_estimation(self, image_id: int, rotation_matrix: np.ndarray, 
                           translation_vector: np.ndarray, inliers_count: int,
                           processing_time: float):
        """姿勢推定の統計を記録
        
        Args:
            image_id: 画像ID
            rotation_matrix: 回転行列
            translation_vector: 並進ベクトル
            inliers_count: インライア数
            processing_time: 処理時間（秒）
        """
        stats = {
            "image_id": image_id,
            "rotation_matrix_shape": rotation_matrix.shape,
            "translation_vector_shape": translation_vector.shape,
            "inliers_count": inliers_count,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        if "poses" not in self.stats["pose_estimation"]:
            self.stats["pose_estimation"]["poses"] = {}
        
        self.stats["pose_estimation"]["poses"][image_id] = stats
        
        self.log_step("pose_estimation", stats)
    
    def log_triangulation(self, points_3d_count: int, reprojection_error: float,
                         processing_time: float):
        """三角測量の統計を記録
        
        Args:
            points_3d_count: 3D点の数
            reprojection_error: 再投影誤差
            processing_time: 処理時間（秒）
        """
        stats = {
            "points_3d_count": points_3d_count,
            "reprojection_error": reprojection_error,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        self.stats["triangulation"] = stats
        
        self.log_step("triangulation", stats)
    
    def log_bundle_adjustment(self, initial_error: float, final_error: float,
                             iterations: int, processing_time: float,
                             convergence: bool):
        """バンドル調整の統計を記録
        
        Args:
            initial_error: 初期誤差
            final_error: 最終誤差
            iterations: 反復回数
            processing_time: 処理時間（秒）
            convergence: 収束したかどうか
        """
        stats = {
            "initial_error": initial_error,
            "final_error": final_error,
            "error_reduction": initial_error - final_error,
            "iterations": iterations,
            "processing_time": processing_time,
            "convergence": convergence,
            "timestamp": datetime.now().isoformat()
        }
        
        self.stats["bundle_adjustment"] = stats
        
        self.log_step("bundle_adjustment", stats)
    
    def log_final_results(self, total_points: int, total_cameras: int,
                         total_processing_time: float, output_files: List[str]):
        """最終結果の統計を記録
        
        Args:
            total_points: 総3D点数
            total_cameras: 総カメラ数
            total_processing_time: 総処理時間（秒）
            output_files: 出力ファイルのリスト
        """
        stats = {
            "total_points": total_points,
            "total_cameras": total_cameras,
            "total_processing_time": total_processing_time,
            "output_files": output_files,
            "timestamp": datetime.now().isoformat()
        }
        
        self.stats["final_results"] = stats
        self.stats["session_info"]["end_time"] = datetime.now().isoformat()
        
        self.log_step("final_results", stats)
    
    def save_stats(self, filename: Optional[str] = None):
        """統計情報をJSONファイルに保存
        
        Args:
            filename: ファイル名（指定しない場合は自動生成）
        """
        if filename is None:
            filename = f"stats_{self.session_id}.json"
        
        stats_file = self.session_log_dir / filename
        
        # numpy配列をリストに変換
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {key: convert_numpy(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            else:
                return obj
        
        converted_stats = convert_numpy(self.stats)
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(converted_stats, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"統計情報を保存: {stats_file}")
        return str(stats_file)
    
    def get_summary(self) -> Dict[str, Any]:
        """統計情報のサマリーを取得
        
        Returns:
            統計情報のサマリー
        """
        summary = {
            "session_id": self.session_id,
            "project_name": self.project_name,
            "total_steps": len(self.stats["processing_steps"]),
            "feature_extraction": {
                "total_images": len(self.stats["feature_extraction"].get("images", {})),
                "avg_keypoints": 0,
                "total_processing_time": 0
            },
            "matching": {
                "total_pairs": len(self.stats["matching"].get("pairs", {})),
                "avg_inlier_ratio": 0,
                "total_processing_time": 0
            },
            "pose_estimation": {
                "total_poses": len(self.stats["pose_estimation"].get("poses", {})),
                "total_processing_time": 0
            },
            "triangulation": self.stats.get("triangulation", {}),
            "bundle_adjustment": self.stats.get("bundle_adjustment", {}),
            "final_results": self.stats.get("final_results", {})
        }
        
        # 特徴点抽出の統計を計算
        if "images" in self.stats["feature_extraction"]:
            images = self.stats["feature_extraction"]["images"]
            if images:
                total_keypoints = sum(img["keypoints_count"] for img in images.values())
                total_time = sum(img["processing_time"] for img in images.values())
                summary["feature_extraction"]["avg_keypoints"] = total_keypoints / len(images)
                summary["feature_extraction"]["total_processing_time"] = total_time
        
        # マッチングの統計を計算
        if "pairs" in self.stats["matching"]:
            pairs = self.stats["matching"]["pairs"]
            if pairs:
                total_inlier_ratio = sum(pair["inlier_ratio"] for pair in pairs.values())
                total_time = sum(pair["processing_time"] for pair in pairs.values())
                summary["matching"]["avg_inlier_ratio"] = total_inlier_ratio / len(pairs)
                summary["matching"]["total_processing_time"] = total_time
        
        # 姿勢推定の統計を計算
        if "poses" in self.stats["pose_estimation"]:
            poses = self.stats["pose_estimation"]["poses"]
            if poses:
                total_time = sum(pose["processing_time"] for pose in poses.values())
                summary["pose_estimation"]["total_processing_time"] = total_time
        
        return summary
    
    def print_summary(self):
        """統計情報のサマリーをコンソールに出力"""
        summary = self.get_summary()
        
        print("\n" + "="*50)
        print("SfM処理統計サマリー")
        print("="*50)
        print(f"セッションID: {summary['session_id']}")
        print(f"プロジェクト名: {summary['project_name']}")
        print(f"総処理ステップ数: {summary['total_steps']}")
        
        print(f"\n特徴点抽出:")
        print(f"  処理画像数: {summary['feature_extraction']['total_images']}")
        print(f"  平均特徴点数: {summary['feature_extraction']['avg_keypoints']:.1f}")
        print(f"  総処理時間: {summary['feature_extraction']['total_processing_time']:.2f}秒")
        
        print(f"\nマッチング:")
        print(f"  処理ペア数: {summary['matching']['total_pairs']}")
        print(f"  平均インライア率: {summary['matching']['avg_inlier_ratio']:.3f}")
        print(f"  総処理時間: {summary['matching']['total_processing_time']:.2f}秒")
        
        print(f"\n姿勢推定:")
        print(f"  推定姿勢数: {summary['pose_estimation']['total_poses']}")
        print(f"  総処理時間: {summary['pose_estimation']['total_processing_time']:.2f}秒")
        
        if summary['triangulation']:
            print(f"\n三角測量:")
            print(f"  3D点数: {summary['triangulation'].get('points_3d_count', 0)}")
            print(f"  再投影誤差: {summary['triangulation'].get('reprojection_error', 0):.4f}")
            print(f"  処理時間: {summary['triangulation'].get('processing_time', 0):.2f}秒")
        
        if summary['bundle_adjustment']:
            print(f"\nバンドル調整:")
            print(f"  初期誤差: {summary['bundle_adjustment'].get('initial_error', 0):.4f}")
            print(f"  最終誤差: {summary['bundle_adjustment'].get('final_error', 0):.4f}")
            print(f"  誤差削減: {summary['bundle_adjustment'].get('error_reduction', 0):.4f}")
            print(f"  反復回数: {summary['bundle_adjustment'].get('iterations', 0)}")
            print(f"  収束: {summary['bundle_adjustment'].get('convergence', False)}")
            print(f"  処理時間: {summary['bundle_adjustment'].get('processing_time', 0):.2f}秒")
        
        if summary['final_results']:
            print(f"\n最終結果:")
            print(f"  総3D点数: {summary['final_results'].get('total_points', 0)}")
            print(f"  総カメラ数: {summary['final_results'].get('total_cameras', 0)}")
            print(f"  総処理時間: {summary['final_results'].get('total_processing_time', 0):.2f}秒")
            print(f"  出力ファイル数: {len(summary['final_results'].get('output_files', []))}")
        
        print("="*50)
    
    def cleanup(self):
        """ログのクリーンアップ"""
        self.logger.info("SfM Loggerセッション終了")
        
        # 統計情報を保存
        self.save_stats()
        
        # サマリーを出力
        self.print_summary() 