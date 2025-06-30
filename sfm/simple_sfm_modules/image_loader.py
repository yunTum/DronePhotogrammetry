#!/usr/bin/env python3
"""
画像読み込みモジュール
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import os


class ImageLoader:
    """画像読み込みクラス"""
    
    def __init__(self, supported_formats: Optional[List[str]] = None):
        """初期化"""
        if supported_formats is None:
            self.supported_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']
        else:
            self.supported_formats = supported_formats
    
    def get_image_files(self, directory: str) -> List[str]:
        """指定ディレクトリから画像ファイルのパスを取得
        
        Args:
            directory: 画像が格納されているディレクトリのパス
            
        Returns:
            画像ファイルパスのリスト（ソート済み、重複除去済み）
        """
        directory_path = Path(directory)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"ディレクトリが存在しません: {directory}")
        
        if not directory_path.is_dir():
            raise NotADirectoryError(f"指定されたパスはディレクトリではありません: {directory}")
        
        image_paths = set()  # 重複を避けるためにsetを使用
        seen_names = set()   # ファイル名の重複チェック用
        
        # サポートされている形式のファイルを検索
        for ext in self.supported_formats:
            # 大文字小文字両方を検索
            for pattern in [f"*{ext}", f"*{ext.upper()}"]:
                for path in directory_path.glob(pattern):
                    # ファイル名を正規化（小文字に統一）
                    normalized_name = path.name.lower()
                    
                    # 既に見たファイル名でない場合のみ追加
                    if normalized_name not in seen_names:
                        image_paths.add(path)
                        seen_names.add(normalized_name)
        
        # パスを文字列に変換してソート
        image_paths = sorted([str(path) for path in image_paths])
        
        print(f"画像ファイルを検出: {len(image_paths)} 個")
        for i, path in enumerate(image_paths[:5]):  # 最初の5個を表示
            print(f"  {i+1}: {Path(path).name}")
        if len(image_paths) > 5:
            print(f"  ... 他 {len(image_paths) - 5} 個")
        
        return image_paths
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """単一画像を読み込み
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            読み込まれた画像（失敗時はNone）
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"画像を読み込めません: {image_path}")
                return None
            
            print(f"画像読み込み成功: {Path(image_path).name} ({image.shape[1]}x{image.shape[0]})")
            return image
            
        except Exception as e:
            print(f"画像読み込みエラー {Path(image_path).name}: {e}")
            return None
    
    def load_images(self, image_paths: List[str]) -> List[np.ndarray]:
        """複数画像を読み込み
        
        Args:
            image_paths: 画像ファイルパスのリスト
            
        Returns:
            読み込まれた画像のリスト
        """
        images = []
        failed_count = 0
        
        print(f"画像読み込みを開始: {len(image_paths)} ファイル")
        
        for i, image_path in enumerate(image_paths):
            image = self.load_image(image_path)
            if image is not None:
                images.append(image)
            else:
                failed_count += 1
        
        print(f"画像読み込み完了: {len(images)} 成功, {failed_count} 失敗")
        
        return images
    
    def load_images_from_directory(self, directory: str) -> Tuple[Dict[int, np.ndarray], Dict[int, str]]:
        """ディレクトリから画像を読み込み
        
        Args:
            directory: 画像が格納されているディレクトリのパス
            
        Returns:
            (画像辞書, 画像パス辞書)
        """
        # 画像ファイルのパスを取得
        image_paths = self.get_image_files(directory)
        
        if not image_paths:
            print("画像ファイルが見つかりません")
            return {}, {}
        
        # 画像を読み込み
        images_dict = {}
        paths_dict = {}
        
        for i, image_path in enumerate(image_paths):
            image = self.load_image(image_path)
            if image is not None:
                images_dict[i] = image
                paths_dict[i] = image_path
        
        print(f"画像読み込み完了: {len(images_dict)} 成功")
        
        return images_dict, paths_dict
    
    def get_image_info(self, image: np.ndarray) -> Dict:
        """画像の基本情報を取得
        
        Args:
            image: 画像データ
            
        Returns:
            画像情報の辞書
        """
        if image is None:
            return {}
        
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1
        
        info = {
            'width': width,
            'height': height,
            'channels': channels,
            'dtype': str(image.dtype),
            'size_bytes': image.nbytes,
            'aspect_ratio': width / height if height > 0 else 0
        }
        
        return info
    
    def resize_image(self, image: np.ndarray, max_size: int = 1920) -> np.ndarray:
        """画像をリサイズ（アスペクト比を保持）
        
        Args:
            image: 元画像
            max_size: 最大サイズ（幅または高さ）
            
        Returns:
            リサイズされた画像
        """
        if image is None:
            return image
        
        height, width = image.shape[:2]
        
        # アスペクト比を計算
        aspect_ratio = width / height
        
        if width > height:
            new_width = max_size
            new_height = int(max_size / aspect_ratio)
        else:
            new_height = max_size
            new_width = int(max_size * aspect_ratio)
        
        # リサイズ
        resized_image = cv2.resize(image, (new_width, new_height))
        
        return resized_image
    
    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """画像をグレースケールに変換
        
        Args:
            image: カラー画像
            
        Returns:
            グレースケール画像
        """
        if image is None:
            return image
        
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            return image
    
    def validate_image(self, image: np.ndarray) -> bool:
        """画像の妥当性をチェック
        
        Args:
            image: 画像データ
            
        Returns:
            妥当な場合はTrue
        """
        if image is None:
            return False
        
        # サイズチェック
        if image.shape[0] < 10 or image.shape[1] < 10:
            return False
        
        # データ型チェック
        if image.dtype != np.uint8:
            return False
        
        # 値の範囲チェック
        if np.min(image) < 0 or np.max(image) > 255:
            return False
        
        return True 