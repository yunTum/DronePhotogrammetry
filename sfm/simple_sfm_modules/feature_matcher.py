#!/usr/bin/env python3
"""
特徴点マッチングモジュール
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import os


class FeatureMatcher:
    """特徴点マッチングクラス"""
    
    def __init__(self, matcher_type: str = 'FLANN', ratio_threshold: float = 0.7, 
                 min_matches: int = 10):
        """初期化
        
        Args:
            matcher_type: マッチャーの種類 ('FLANN', 'BF')
            ratio_threshold: Lowe's ratio testの閾値
            min_matches: 最小マッチング数
        """
        self.matcher_type = matcher_type.upper()
        self.ratio_threshold = ratio_threshold
        self.min_matches = min_matches
        self.matcher = self._create_matcher()
        
        print(f"特徴点マッチャーを初期化: {self.matcher_type} (ratio={ratio_threshold}, min_matches={min_matches})")
    
    def _create_matcher(self):
        """マッチャーを作成"""
        if self.matcher_type == 'FLANN':
            # FLANNパラメータ
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            return cv2.FlannBasedMatcher(index_params, search_params)
        elif self.matcher_type == 'BF':
            # ブルートフォースマッチャー
            return cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        else:
            print(f"未知のマッチャータイプ: {self.matcher_type}。FLANNを使用します。")
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            return cv2.FlannBasedMatcher(index_params, search_params)
    
    def match_features(self, descriptors1: np.ndarray, descriptors2: np.ndarray) -> List[cv2.DMatch]:
        """2つの画像の特徴点をマッチング
        
        Args:
            descriptors1: 1つ目の画像のディスクリプタ
            descriptors2: 2つ目の画像のディスクリプタ
            
        Returns:
            マッチング結果のリスト
        """
        if len(descriptors1) == 0 or len(descriptors2) == 0:
            return []
        
        try:
            # k=2でマッチング（Lowe's ratio test用）
            matches = self.matcher.knnMatch(descriptors1, descriptors2, k=2)
            
            # Lowe's ratio testでフィルタリング
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < self.ratio_threshold * n.distance:
                        good_matches.append(m)
            
            print(f"マッチング: {len(matches)} → {len(good_matches)} 良好なマッチング")
            return good_matches
            
        except Exception as e:
            print(f"マッチングエラー: {e}")
            return []
    
    def match_all_pairs(self, descriptors_dict: Dict[int, np.ndarray]) -> Dict[Tuple[int, int], List[cv2.DMatch]]:
        """全画像ペアのマッチングを実行
        
        Args:
            descriptors_dict: 画像インデックスをキーとしたディスクリプタ辞書
            
        Returns:
            画像ペアをキーとしたマッチング結果辞書
        """
        matches_dict = {}
        image_indices = list(descriptors_dict.keys())
        
        print(f"全ペアマッチングを開始: {len(image_indices)} 画像")
        
        for i, idx1 in enumerate(image_indices):
            for j, idx2 in enumerate(image_indices[i+1:], i+1):
                if idx1 in descriptors_dict and idx2 in descriptors_dict:
                    descriptors1 = descriptors_dict[idx1]
                    descriptors2 = descriptors_dict[idx2]
                    
                    matches = self.match_features(descriptors1, descriptors2)
                    
                    if len(matches) >= self.min_matches:
                        matches_dict[(idx1, idx2)] = matches
                        print(f"ペア ({idx1}, {idx2}): {len(matches)} マッチング")
                    else:
                        print(f"ペア ({idx1}, {idx2}): マッチング不足 ({len(matches)} < {self.min_matches})")
        
        print(f"全ペアマッチング完了: {len(matches_dict)} ペア")
        return matches_dict
    
    def filter_matches_by_distance(self, matches: List[cv2.DMatch], 
                                 max_distance: float = 100.0) -> List[cv2.DMatch]:
        """距離に基づいてマッチングをフィルタリング
        
        Args:
            matches: マッチング結果
            max_distance: 最大距離閾値
            
        Returns:
            フィルタリングされたマッチング結果
        """
        filtered_matches = [m for m in matches if m.distance < max_distance]
        print(f"距離フィルタリング: {len(matches)} → {len(filtered_matches)} マッチング")
        return filtered_matches
    
    def get_matched_points(self, keypoints1: List[cv2.KeyPoint], 
                          keypoints2: List[cv2.KeyPoint], 
                          matches: List[cv2.DMatch]) -> Tuple[np.ndarray, np.ndarray]:
        """マッチング結果から対応点の座標を取得
        
        Args:
            keypoints1: 1つ目の画像の特徴点
            keypoints2: 2つ目の画像の特徴点
            matches: マッチング結果
            
        Returns:
            (1つ目の画像の対応点座標, 2つ目の画像の対応点座標)
        """
        if not matches:
            return np.array([]), np.array([])
        
        pts1 = np.float32([keypoints1[m.queryIdx].pt for m in matches])
        pts2 = np.float32([keypoints2[m.trainIdx].pt for m in matches])
        
        return pts1, pts2
    
    def visualize_matches(self, image1: np.ndarray, image2: np.ndarray,
                         keypoints1: List[cv2.KeyPoint], keypoints2: List[cv2.KeyPoint],
                         matches: List[cv2.DMatch], output_path: Optional[str] = None) -> np.ndarray:
        """マッチング結果を可視化
        
        Args:
            image1: 1つ目の画像
            image2: 2つ目の画像
            keypoints1: 1つ目の画像の特徴点
            keypoints2: 2つ目の画像の特徴点
            matches: マッチング結果
            output_path: 出力ファイルパス
            
        Returns:
            可視化された画像
        """
        if image1 is None or image2 is None:
            return None
        
        # マッチングを描画
        vis_image = cv2.drawMatches(image1, keypoints1, image2, keypoints2, matches, None,
                                  flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        
        # マッチング数の情報を追加
        text = f"Matches: {len(matches)}"
        cv2.putText(vis_image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 保存
        if output_path:
            cv2.imwrite(output_path, vis_image)
            print(f"マッチング可視化を保存: {output_path}")
        
        return vis_image
    
    def save_matches(self, matches_dict: Dict[Tuple[int, int], List[cv2.DMatch]], 
                    output_dir: str):
        """マッチング結果を保存
        
        Args:
            matches_dict: マッチング結果辞書
            output_dir: 出力ディレクトリ
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # マッチング結果を保存
        matches_file = output_path / "matches.npz"
        matches_data = {}
        
        for (idx1, idx2), matches in matches_dict.items():
            if matches:
                # DMatchオブジェクトをシリアライズ可能な形式に変換
                match_data = []
                for match in matches:
                    match_data.append({
                        'queryIdx': match.queryIdx,
                        'trainIdx': match.trainIdx,
                        'distance': match.distance
                    })
                matches_data[f'matches_{idx1}_{idx2}'] = match_data
        
        np.savez_compressed(matches_file, **matches_data)
        print(f"マッチング結果を保存: {output_dir}")
    
    def load_matches(self, input_dir: str) -> Dict[Tuple[int, int], List[cv2.DMatch]]:
        """マッチング結果を読み込み
        
        Args:
            input_dir: 入力ディレクトリ
            
        Returns:
            マッチング結果辞書
        """
        input_path = Path(input_dir)
        matches_dict = {}
        
        matches_file = input_path / "matches.npz"
        if matches_file.exists():
            matches_data = np.load(matches_file, allow_pickle=True)
            
            for key in matches_data.files:
                if key.startswith('matches_'):
                    parts = key.split('_')
                    if len(parts) >= 3:
                        idx1 = int(parts[1])
                        idx2 = int(parts[2])
                        
                        match_data = matches_data[key]
                        matches = []
                        for match_info in match_data:
                            match = cv2.DMatch(
                                queryIdx=match_info['queryIdx'],
                                trainIdx=match_info['trainIdx'],
                                distance=match_info['distance']
                            )
                            matches.append(match)
                        
                        matches_dict[(idx1, idx2)] = matches
        
        print(f"マッチング結果を読み込み: {len(matches_dict)} ペア")
        return matches_dict 