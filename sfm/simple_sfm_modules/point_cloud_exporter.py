import numpy as np
import os
from typing import Dict, List, Tuple, Optional
import json


class PointCloudExporter:
    """点群データをPLYファイル形式で出力するクラス"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def export_point_cloud_ply(self, 
                              points_3d: np.ndarray, 
                              colors: Optional[np.ndarray] = None,
                              filename: str = "point_cloud.ply") -> str:
        """
        3D点群をPLYファイルとして出力
        
        Args:
            points_3d: 3D点の座標 (N, 3)
            colors: 点の色情報 (N, 3) - RGB値（0-255）
            filename: 出力ファイル名
        
        Returns:
            出力ファイルのパス
        """
        if points_3d is None or len(points_3d) == 0:
            print("警告: 3D点が存在しません")
            return None
        
        filepath = os.path.join(self.output_dir, filename)
        
        num_points = len(points_3d)
        
        # PLYファイルヘッダーを作成
        header = [
            "ply",
            "format ascii 1.0",
            f"element vertex {num_points}",
            "property float x",
            "property float y", 
            "property float z"
        ]
        
        if colors is not None:
            header.extend([
                "property uchar red",
                "property uchar green",
                "property uchar blue"
            ])
        
        header.append("end_header")
        
        # ファイルに書き込み
        with open(filepath, 'w') as f:
            # ヘッダーを書き込み
            for line in header:
                f.write(line + '\n')
            
            # 点データを書き込み
            for i in range(num_points):
                line = f"{points_3d[i, 0]:.6f} {points_3d[i, 1]:.6f} {points_3d[i, 2]:.6f}"
                
                if colors is not None:
                    line += f" {int(colors[i, 0])} {int(colors[i, 1])} {int(colors[i, 2])}"
                
                f.write(line + '\n')
        
        print(f"点群データを保存しました: {filepath}")
        print(f"点の数: {num_points}")
        
        return filepath
    
    def export_point_cloud_binary_ply(self, 
                                     points_3d: np.ndarray, 
                                     colors: Optional[np.ndarray] = None,
                                     filename: str = "point_cloud_binary.ply") -> str:
        """
        3D点群をバイナリPLYファイルとして出力（高速）
        
        Args:
            points_3d: 3D点の座標 (N, 3)
            colors: 点の色情報 (N, 3) - RGB値（0-255）
            filename: 出力ファイル名
        
        Returns:
            出力ファイルのパス
        """
        if points_3d is None or len(points_3d) == 0:
            print("警告: 3D点が存在しません")
            return None
        
        filepath = os.path.join(self.output_dir, filename)
        
        num_points = len(points_3d)
        
        # PLYファイルヘッダーを作成
        header = [
            "ply",
            "format binary_little_endian 1.0",
            f"element vertex {num_points}",
            "property float x",
            "property float y", 
            "property float z"
        ]
        
        if colors is not None:
            header.extend([
                "property uchar red",
                "property uchar green",
                "property uchar blue"
            ])
        
        header.append("end_header")
        
        # ファイルに書き込み
        with open(filepath, 'wb') as f:
            # ヘッダーを書き込み
            for line in header:
                f.write((line + '\n').encode('ascii'))
            
            # 点データをバイナリで書き込み
            for i in range(num_points):
                # 座標データ
                f.write(points_3d[i].astype(np.float32).tobytes())
                
                # 色データ
                if colors is not None:
                    f.write(colors[i].astype(np.uint8).tobytes())
        
        print(f"バイナリ点群データを保存しました: {filepath}")
        print(f"点の数: {num_points}")
        
        return filepath
    
    def export_point_cloud_numpy(self, 
                                points_3d: np.ndarray, 
                                filename: str = "point_cloud.npy") -> str:
        """
        3D点群をNumPy配列として保存
        
        Args:
            points_3d: 3D点の座標 (N, 3)
            filename: 出力ファイル名
        
        Returns:
            出力ファイルのパス
        """
        if points_3d is None or len(points_3d) == 0:
            print("警告: 3D点が存在しません")
            return None
        
        filepath = os.path.join(self.output_dir, filename)
        np.save(filepath, points_3d)
        
        print(f"NumPy点群データを保存しました: {filepath}")
        print(f"点の数: {len(points_3d)}")
        
        return filepath
    
    def export_point_cloud_with_metadata(self, 
                                        points_3d: np.ndarray,
                                        colors: Optional[np.ndarray] = None,
                                        camera_poses: Optional[Dict] = None,
                                        metadata: Optional[Dict] = None,
                                        base_filename: str = "point_cloud") -> Dict[str, str]:
        """
        点群データとメタデータを複数形式で出力
        
        Args:
            points_3d: 3D点の座標 (N, 3)
            colors: 点の色情報 (N, 3)
            camera_poses: カメラ姿勢情報
            metadata: 追加メタデータ
            base_filename: 基本ファイル名
        
        Returns:
            出力ファイルパスの辞書
        """
        output_files = {}
        
        # 点群データを出力
        if points_3d is not None and len(points_3d) > 0:
            # PLYファイル（ASCII）
            ply_file = self.export_point_cloud_ply(
                points_3d, colors, f"{base_filename}.ply"
            )
            if ply_file:
                output_files['ply'] = ply_file
            
            # PLYファイル（バイナリ）
            binary_ply_file = self.export_point_cloud_binary_ply(
                points_3d, colors, f"{base_filename}_binary.ply"
            )
            if binary_ply_file:
                output_files['binary_ply'] = binary_ply_file
            
            # NumPy配列
            npy_file = self.export_point_cloud_numpy(
                points_3d, f"{base_filename}.npy"
            )
            if npy_file:
                output_files['numpy'] = npy_file
        
        # カメラ姿勢情報を出力
        if camera_poses:
            camera_file = os.path.join(self.output_dir, f"{base_filename}_cameras.json")
            with open(camera_file, 'w') as f:
                json.dump(camera_poses, f, indent=2, default=str)
            output_files['cameras'] = camera_file
            print(f"カメラ姿勢情報を保存しました: {camera_file}")
        
        # メタデータを出力
        if metadata:
            metadata_file = os.path.join(self.output_dir, f"{base_filename}_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            output_files['metadata'] = metadata_file
            print(f"メタデータを保存しました: {metadata_file}")
        
        return output_files
    
    def create_colored_point_cloud(self, 
                                  points_3d: np.ndarray, 
                                  images: Dict[str, np.ndarray],
                                  camera_poses: Dict,
                                  image_points: Dict) -> np.ndarray:
        """
        画像から色情報を取得して点群に色を付ける
        
        Args:
            points_3d: 3D点の座標 (N, 3)
            images: 画像辞書
            camera_poses: カメラ姿勢情報
            image_points: 画像上の点座標
        
        Returns:
            色情報付きの点群
        """
        if points_3d is None or len(points_3d) == 0:
            return None
        
        colors = np.zeros((len(points_3d), 3), dtype=np.uint8)
        
        # 各3D点について、対応する画像から色を取得
        for i, point_3d in enumerate(points_3d):
            # この点に対応する画像と座標を探す
            point_color = [128, 128, 128]  # デフォルトはグレー
            
            for img_name, img in images.items():
                if img_name in image_points and i < len(image_points[img_name]):
                    img_point = image_points[img_name][i]
                    if img_point is not None:
                        x, y = int(img_point[0]), int(img_point[1])
                        if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
                            if len(img.shape) == 3:  # カラー画像
                                # OpenCVのBGR順序をRGB順序に変換
                                bgr_color = img[y, x]
                                point_color = [bgr_color[2], bgr_color[1], bgr_color[0]]  # BGR → RGB
                            else:  # グレースケール画像
                                point_color = [img[y, x]] * 3
                            break
            
            colors[i] = point_color
        
        return colors


if __name__ == "__main__":
    # テスト用コード
    exporter = PointCloudExporter()
    
    # サンプル点群データを作成
    num_points = 1000
    points_3d = np.random.randn(num_points, 3) * 10
    colors = np.random.randint(0, 256, (num_points, 3))
    
    # 点群を出力
    output_files = exporter.export_point_cloud_with_metadata(
        points_3d=points_3d,
        colors=colors,
        camera_poses={"test": "camera_data"},
        metadata={"num_points": num_points, "description": "テスト点群"}
    )
    
    print("出力ファイル:", output_files) 