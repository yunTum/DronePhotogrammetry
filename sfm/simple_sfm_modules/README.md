# Simple SfM Modules

Structure from Motion解析のためのシンプルなモジュール群です。

## 概要

このパッケージは、SfM（Structure from Motion）パイプラインの前処理段階を担当する3つの主要モジュールを提供します：

1. **ImageLoader** - 画像ファイルの読み込み
2. **MetadataExtractor** - 画像メタデータの抽出
3. **FeatureExtractor** - 特徴点の抽出

## インストール

### 必要な依存関係

```bash
pip install opencv-python numpy pillow exifread
```

### オプションの依存関係

- `PIL/Pillow`: EXIFデータの抽出に使用
- `exifread`: より詳細なEXIFデータの抽出に使用

## 使用方法

### 基本的な使用例

```python
from simple_sfm_modules import ImageLoader, MetadataExtractor, FeatureExtractor

# 1. 画像読み込み
image_loader = ImageLoader()
images, image_paths = image_loader.load_images_from_directory("images/")

# 2. メタデータ抽出
metadata_extractor = MetadataExtractor()
metadata_dict = metadata_extractor.extract_metadata_batch(image_paths)

# 3. 特徴点抽出
feature_extractor = FeatureExtractor(detector_type='SIFT', max_features=3000)
keypoints_dict, descriptors_dict = feature_extractor.extract_features_batch(images)
```

### 詳細な使用例

```python
import os
from simple_sfm_modules import ImageLoader, MetadataExtractor, FeatureExtractor

def process_images(image_directory, output_directory):
    """画像処理の完全なワークフロー"""
    
    # 画像読み込み
    image_loader = ImageLoader()
    images, image_paths = image_loader.load_images_from_directory(image_directory)
    
    if not images:
        print("画像の読み込みに失敗しました")
        return
    
    # メタデータ抽出
    metadata_extractor = MetadataExtractor()
    metadata_dict = metadata_extractor.extract_metadata_batch(image_paths)
    
    # メタデータを保存
    metadata_path = os.path.join(output_directory, "metadata.json")
    metadata_extractor.save_metadata_json(metadata_dict, metadata_path)
    
    # 特徴点抽出
    feature_extractor = FeatureExtractor(
        detector_type='SIFT',
        max_features=5000
    )
    keypoints_dict, descriptors_dict = feature_extractor.extract_features_batch(images)
    
    # 特徴点データを保存
    features_dir = os.path.join(output_directory, "features")
    feature_extractor.save_features(keypoints_dict, descriptors_dict, features_dir)
    
    # 特徴点の可視化
    if images and keypoints_dict:
        vis_path = os.path.join(output_directory, "keypoints.jpg")
        feature_extractor.visualize_keypoints(images[0], keypoints_dict[0], vis_path)
    
    print(f"処理完了: {len(images)} 画像")

# 使用例
process_images("input_images/", "output/")
```

## モジュール詳細

### ImageLoader

画像ファイルの読み込みと管理を行います。

```python
from simple_sfm_modules import ImageLoader

# 初期化
loader = ImageLoader(supported_formats=['.jpg', '.png', '.tiff'])

# 画像ファイルのパスを取得
image_paths = loader.get_image_files("images/")

# 画像を読み込み
images, successful_paths = loader.load_images_from_directory("images/")

# 画像情報を取得
info = loader.get_image_info(images[0])

# 画像をリサイズ
resized = loader.resize_image(images[0], max_size=1920)

# グレースケール変換
gray = loader.convert_to_grayscale(images[0])
```

### MetadataExtractor

画像のEXIFメタデータとカメラパラメータを抽出します。

```python
from simple_sfm_modules import MetadataExtractor

# 初期化
extractor = MetadataExtractor()

# 単一画像のメタデータ抽出
metadata = extractor.extract_metadata_from_image("image.jpg")

# バッチ処理
metadata_dict = extractor.extract_metadata_batch(image_paths)

# メタデータを保存/読み込み
extractor.save_metadata_json(metadata_dict, "metadata.json")
loaded_metadata = extractor.load_metadata_json("metadata.json")
```

**抽出されるメタデータ:**
- ファイル情報（パス、サイズ、作成日時）
- 画像サイズ
- カメラ情報（メーカー、モデル）
- 撮影パラメータ（焦点距離、絞り値、シャッタースピード、ISO）
- GPS情報（緯度、経度、高度）
- 推定カメラパラメータ（カメラ行列、歪み係数）

### FeatureExtractor

画像から特徴点とディスクリプタを抽出します。

```python
from simple_sfm_modules import FeatureExtractor

# 初期化（複数の検出器をサポート）
extractor = FeatureExtractor(
    detector_type='SIFT',  # 'SIFT', 'SURF', 'ORB', 'AKAZE'
    max_features=5000
)

# 単一画像の特徴点抽出
keypoints, descriptors = extractor.extract_features(image)

# バッチ処理
keypoints_dict, descriptors_dict = extractor.extract_features_batch(images)

# 特徴点のフィルタリング
filtered_kps, filtered_desc = extractor.filter_keypoints_by_quality(
    keypoints, descriptors, min_quality=0.01
)

# 特徴点の可視化
vis_image = extractor.visualize_keypoints(image, keypoints, "output.jpg")

# 統計情報の取得
stats = extractor.get_keypoint_statistics(keypoints)

# 特徴点データの保存/読み込み
extractor.save_features(keypoints_dict, descriptors_dict, "features/")
loaded_kps, loaded_desc = extractor.load_features("features/")
```

## 設定オプション

### ImageLoader

- `supported_formats`: サポートする画像形式のリスト
- デフォルト: `['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']`

### MetadataExtractor

- カメラメーカー別のデフォルト焦点距離とセンサーサイズ
- EXIF抽出ライブラリの自動選択（PIL → exifread）

### FeatureExtractor

- `detector_type`: 特徴点検出器の種類
  - `'SIFT'`: 最も安定した結果（デフォルト）
  - `'SURF'`: 高速だが特許の問題で利用できない場合がある
  - `'ORB'`: 高速で特許フリー
  - `'AKAZE'`: 最新の検出器
- `max_features`: 最大特徴点数（デフォルト: 5000）

## 出力ファイル

### メタデータ（JSON形式）

```json
{
  "0": {
    "file_path": "images/IMG_001.jpg",
    "file_name": "IMG_001.jpg",
    "image_size": {"width": 1920, "height": 1080},
    "camera_make": "Canon",
    "camera_model": "EOS 5D Mark IV",
    "focal_length": 50.0,
    "estimated_focal_length": 50.0,
    "camera_matrix": [[...], [...], [...]],
    "distortion_coefficients": [0.0, 0.0, 0.0, 0.0, 0.0]
  }
}
```

### 特徴点データ（NPZ形式）

- `keypoints.npz`: 特徴点情報
- `descriptors.npz`: ディスクリプタ配列

## エラーハンドリング

各モジュールは適切なエラーハンドリングを実装しており、処理に失敗した画像はスキップして処理を継続します。

```python
try:
    images, paths = image_loader.load_images_from_directory("images/")
    print(f"成功: {len(images)} 画像")
except FileNotFoundError:
    print("ディレクトリが見つかりません")
except Exception as e:
    print(f"予期しないエラー: {e}")
```

## パフォーマンス

- **画像読み込み**: 並列処理は実装されていませんが、効率的なファイルI/Oを使用
- **メタデータ抽出**: EXIFライブラリの最適化された実装を使用
- **特徴点抽出**: OpenCVの最適化された実装を使用

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要求は、GitHubのIssueでお知らせください。プルリクエストも歓迎します。 