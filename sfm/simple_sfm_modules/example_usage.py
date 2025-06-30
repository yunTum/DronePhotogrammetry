#!/usr/bin/env python3
"""
Simple SfM Modules 使用例

このスクリプトは、作成したモジュールの基本的な使用方法を示します。
"""

import os
import sys
from pathlib import Path

# モジュールをインポート
from image_loader import ImageLoader
from metadata_extractor import MetadataExtractor
from feature_extractor import FeatureExtractor


def main():
    """メイン処理"""
    
    # 設定
    image_directory = "../images"  # 画像が格納されているディレクトリ
    output_directory = "output"  # 出力ディレクトリ
    
    print("=== Simple SfM Modules 使用例 ===")
    
    # 1. 画像読み込み
    print("\n1. 画像読み込み")
    image_loader = ImageLoader()
    
    try:
        # 画像ファイルのパスを取得
        image_paths = image_loader.get_image_files(image_directory)
        
        if not image_paths:
            print(f"画像ファイルが見つかりません: {image_directory}")
            return
        
        # 画像を読み込み
        images, successful_paths = image_loader.load_images_from_directory(image_directory)
        
        if not images:
            print("画像の読み込みに失敗しました")
            return
        
        print(f"画像読み込み完了: {len(images)} 枚")
        
    except Exception as e:
        print(f"画像読み込みエラー: {e}")
        return
    
    # 2. メタデータ抽出
    print("\n2. メタデータ抽出")
    metadata_extractor = MetadataExtractor()
    
    try:
        # メタデータを一括抽出
        metadata_dict = metadata_extractor.extract_metadata_batch(successful_paths)
        
        # メタデータを保存
        metadata_output_path = os.path.join(output_directory, "metadata.json")
        metadata_extractor.save_metadata_json(metadata_dict, metadata_output_path)
        
        print(f"メタデータ抽出完了: {len(metadata_dict)} 画像")
        
        # 最初の画像のメタデータを表示
        if metadata_dict:
            first_metadata = metadata_dict[0]
            print(f"最初の画像のメタデータ:")
            print(f"  ファイル名: {first_metadata.get('file_name', 'Unknown')}")
            print(f"  サイズ: {first_metadata.get('image_size', 'Unknown')}")
            print(f"  カメラ: {first_metadata.get('camera_make', 'Unknown')} {first_metadata.get('camera_model', 'Unknown')}")
            print(f"  焦点距離: {first_metadata.get('focal_length', 'Unknown')}mm")
        
    except Exception as e:
        print(f"メタデータ抽出エラー: {e}")
        return
    
    # 3. 特徴点抽出
    print("\n3. 特徴点抽出")
    feature_extractor = FeatureExtractor(detector_type='SIFT', max_features=50000)
    
    try:
        # 特徴点を一括抽出（可視化も同時に保存）
        keypoints_dict, descriptors_dict = feature_extractor.extract_features_batch(images, output_directory)
        
        # 特徴点データを保存
        features_output_dir = os.path.join(output_directory, "features")
        feature_extractor.save_features(keypoints_dict, descriptors_dict, features_output_dir)
        
        print(f"特徴点抽出完了: {len(keypoints_dict)} 画像")
        
        # 統計情報を表示
        total_keypoints = sum(len(kps) for kps in keypoints_dict.values())
        print(f"総特徴点数: {total_keypoints}")
        
        # 最初の画像の特徴点統計を表示
        if keypoints_dict and 0 in keypoints_dict:
            stats = feature_extractor.get_keypoint_statistics(keypoints_dict[0])
            print(f"最初の画像の特徴点統計:")
            print(f"  特徴点数: {stats['count']}")
            print(f"  平均応答値: {stats['avg_response']:.3f}")
            print(f"  平均サイズ: {stats['avg_size']:.1f}")
        
        # 特徴点の可視化は既にextract_features_batchで実行済み
        print(f"特徴点可視化は {os.path.join(output_directory, 'keypoints')} に保存されました")
        
    except Exception as e:
        print(f"特徴点抽出エラー: {e}")
        return
    
    print("\n=== 処理完了 ===")
    print(f"出力ディレクトリ: {output_directory}")
    print("以下のファイルが生成されました:")
    print(f"  - {os.path.join(output_directory, 'metadata.json')}")
    print(f"  - {os.path.join(output_directory, 'features/')}")

    print("\n" + "="*50)
    print("SfMパイプラインの使用例")
    print("="*50)

    # SfMパイプラインを使用した完全な処理
    from sfm_pipeline import SFMPipeline

    # パイプラインを初期化
    pipeline = SFMPipeline(output_dir="output/sfm_pipeline_example")

    # 完全なSfMパイプラインを実行
    results = pipeline.run_full_pipeline(
        image_dir=image_directory,
        detector_type='SIFT',
        max_features=10000,
        matcher_type='FLANN',
        ratio_threshold=0.7,
        min_matches=8,
        max_images=10  # 最大10枚の画像を使用
    )

    print(f"SfMパイプライン結果: {results}")

    # 点群をPLY形式で保存
    if len(pipeline.points_3d) > 0:
        pipeline.save_point_cloud("sfm_point_cloud.ply")
        print(f"点群を保存: {len(pipeline.points_3d)} 点")

    print("SfMパイプラインの使用例完了")

def create_sample_directory():
    """サンプルディレクトリ構造を作成"""
    print("サンプルディレクトリ構造を作成中...")
    
    # ディレクトリを作成
    os.makedirs("images", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    print("ディレクトリ構造:")
    print("  images/     - 画像ファイルを配置")
    print("  output/     - 処理結果が保存される")
    print("\n使用方法:")
    print("1. images/ ディレクトリに画像ファイル（.jpg, .png等）を配置")
    print("2. このスクリプトを実行")
    print("3. output/ ディレクトリに結果が保存される")


if __name__ == "__main__":
    # コマンドライン引数の処理
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        create_sample_directory()
    else:
        main() 