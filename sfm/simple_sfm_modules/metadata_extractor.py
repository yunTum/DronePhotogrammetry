#!/usr/bin/env python3
"""
メタデータ抽出モジュール
Metadata extraction module for SfM pipeline
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import os

try:
    from PIL import Image, ExifTags
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL/Pillowが利用できません。EXIFデータの取得が制限されます。")

try:
    import exifread
    EXIFREAD_AVAILABLE = True
except ImportError:
    EXIFREAD_AVAILABLE = False
    print("警告: exifreadが利用できません。EXIFデータの取得が制限されます。")


class MetadataExtractor:
    """画像ファイルからメタデータを抽出するクラス"""
    
    def __init__(self):
        """メタデータ抽出器の初期化"""
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
        
        # カメラメーカーのデフォルト焦点距離（mm）
        self.default_focal_lengths = {
            'Canon': 50.0,
            'Nikon': 50.0,
            'Sony': 50.0,
            'Fujifilm': 50.0,
            'Panasonic': 50.0,
            'Olympus': 50.0,
            'Pentax': 50.0,
            'Leica': 50.0,
            'Sigma': 50.0,
            'Tamron': 50.0,
            'default': 50.0
        }
        
        # センサーサイズのデフォルト値（mm）
        self.default_sensor_sizes = {
            'Canon': {'width': 22.3, 'height': 14.9},  # APS-C
            'Nikon': {'width': 23.5, 'height': 15.6},  # APS-C
            'Sony': {'width': 23.5, 'height': 15.6},   # APS-C
            'Fujifilm': {'width': 23.5, 'height': 15.6}, # APS-C
            'Panasonic': {'width': 17.3, 'height': 13.0}, # Micro Four Thirds
            'Olympus': {'width': 17.3, 'height': 13.0},   # Micro Four Thirds
            'Pentax': {'width': 23.5, 'height': 15.6},    # APS-C
            'Leica': {'width': 23.9, 'height': 35.8},     # Full Frame
            'Sigma': {'width': 20.7, 'height': 13.8},     # APS-C
            'Tamron': {'width': 23.5, 'height': 15.6},    # APS-C
            'default': {'width': 23.5, 'height': 15.6}    # APS-C
        }
    
    def extract_metadata_from_image(self, image_path: str) -> Dict[str, Any]:
        """画像ファイルからメタデータを抽出
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            メタデータ辞書
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")
        
        if image_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"サポートされていない画像形式: {image_path.suffix}")
        
        # 基本メタデータを作成
        metadata = self._create_basic_metadata(image_path)
        
        # 画像サイズを取得
        self._extract_image_size(image_path, metadata)
        
        # EXIFデータを取得
        exif_data = self._extract_exif_data(image_path)
        if exif_data:
            metadata.update(exif_data)
        
        # カメラパラメータを推定
        camera_params = self._estimate_camera_parameters(metadata)
        metadata.update(camera_params)
        
        return metadata
    
    def _create_basic_metadata(self, image_path: Path) -> Dict[str, Any]:
        """基本メタデータを作成"""
        return {
            'file_path': str(image_path),
            'file_name': image_path.name,
            'file_size': image_path.stat().st_size,
            'creation_time': datetime.fromtimestamp(image_path.stat().st_ctime).isoformat(),
            'modification_time': datetime.fromtimestamp(image_path.stat().st_mtime).isoformat(),
            'image_size': None,
            'camera_make': None,
            'camera_model': None,
            'focal_length': None,
            'focal_length_35mm': None,
            'aperture': None,
            'max_aperture': None,
            'shutter_speed': None,
            'iso': None,
            'exposure_time': None,
            'exposure_bias': None,
            'metering_mode': None,
            'flash': None,
            'white_balance': None,
            'sensor_size': None,
            'gps_latitude': None,
            'gps_longitude': None,
            'gps_altitude': None,
            'gps_timestamp': None,
            'orientation': 1,
            'color_space': None,
            'software': None,
            'artist': None,
            'copyright': None,
            'datetime': None
        }
    
    def _extract_image_size(self, image_path: Path, metadata: Dict[str, Any]):
        """画像サイズを抽出"""
        try:
            img = cv2.imread(str(image_path))
            if img is not None:
                height, width = img.shape[:2]
                metadata['image_size'] = {'width': width, 'height': height}
        except Exception as e:
            print(f"画像サイズの取得に失敗: {e}")
    
    def _extract_exif_data(self, image_path: Path) -> Dict[str, Any]:
        """EXIFデータを抽出"""
        exif_data = {}
        
        # PILを使用したEXIF抽出
        if PIL_AVAILABLE:
            self._extract_exif_with_pil(image_path, exif_data)
        
        # exifreadを使用したEXIF抽出
        if EXIFREAD_AVAILABLE:
            self._extract_exif_with_exifread(image_path, exif_data)
        
        return exif_data
    
    def _extract_exif_with_pil(self, image_path: Path, exif_data: Dict[str, Any]):
        """PILを使用してEXIFデータを抽出"""
        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if exif:
                    self._process_pil_exif_tags(exif, exif_data)
                    
                    # GPS情報を取得
                    gps_info = self._extract_gps_info(exif)
                    if gps_info:
                        exif_data.update(gps_info)
        except Exception as e:
            print(f"PILでのEXIF抽出に失敗: {e}")
    
    def _process_pil_exif_tags(self, exif: Dict, exif_data: Dict[str, Any]):
        """PILのEXIFタグを処理"""
        tag_mappings = {
            'Make': 'camera_make',
            'Model': 'camera_model',
            'FocalLength': 'focal_length',
            'FocalLengthIn35mmFilm': 'focal_length_35mm',
            'FNumber': 'aperture',
            'MaxApertureValue': 'max_aperture',
            'ExposureTime': 'exposure_time',
            'ISOSpeedRatings': 'iso',
            'DateTime': 'datetime',
            'Software': 'software',
            'Artist': 'artist',
            'Copyright': 'copyright',
            'Orientation': 'orientation',
            'ColorSpace': 'color_space'
        }
        
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            
            if tag in tag_mappings:
                field_name = tag_mappings[tag]
                exif_data[field_name] = self._convert_exif_value(value)
    
    def _convert_exif_value(self, value: Any) -> Any:
        """EXIF値を適切な型に変換"""
        if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
            try:
                return float(value.numerator) / float(value.denominator)
            except (ZeroDivisionError, AttributeError):
                return str(value)
        elif isinstance(value, (int, float)):
            return value
        else:
            return str(value)
    
    def _extract_exif_with_exifread(self, image_path: Path, exif_data: Dict[str, Any]):
        """exifreadを使用してEXIFデータを抽出"""
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
            
            self._process_exifread_tags(tags, exif_data)
            
            # GPS情報を取得
            if not any(key.startswith('gps_') for key in exif_data.keys()):
                gps_info = self._extract_gps_info_exifread(tags)
                if gps_info:
                    exif_data.update(gps_info)
        except Exception as e:
            print(f"exifreadでのEXIF抽出に失敗: {e}")
    
    def _process_exifread_tags(self, tags: Dict, exif_data: Dict[str, Any]):
        """exifreadのタグを処理"""
        # カメラ情報（PILで取得できていない場合のみ）
        if 'camera_make' not in exif_data and 'Image Make' in tags:
            exif_data['camera_make'] = str(tags['Image Make'])
        if 'camera_model' not in exif_data and 'Image Model' in tags:
            exif_data['camera_model'] = str(tags['Image Model'])
        
        # 焦点距離
        self._extract_focal_length_exifread(tags, exif_data)
        
        # 絞り値
        self._extract_aperture_exifread(tags, exif_data)
        
        # シャッタースピード
        self._extract_shutter_speed_exifread(tags, exif_data)
        
        # ISO感度
        self._extract_iso_exifread(tags, exif_data)
        
        # 追加のEXIFタグ
        self._extract_additional_exif_tags(tags, exif_data)
    
    def _extract_focal_length_exifread(self, tags: Dict, exif_data: Dict[str, Any]):
        """exifreadから焦点距離を抽出"""
        if 'focal_length' not in exif_data and 'EXIF FocalLength' in tags:
            focal_length = tags['EXIF FocalLength']
            exif_data['focal_length'] = self._convert_exifread_rational(focal_length)
        
        if 'focal_length_35mm' not in exif_data and 'EXIF FocalLengthIn35mmFilm' in tags:
            focal_length_35mm = tags['EXIF FocalLengthIn35mmFilm']
            exif_data['focal_length_35mm'] = self._convert_exifread_rational(focal_length_35mm)
    
    def _extract_aperture_exifread(self, tags: Dict, exif_data: Dict[str, Any]):
        """exifreadから絞り値を抽出"""
        if 'aperture' not in exif_data and 'EXIF FNumber' in tags:
            fnumber = tags['EXIF FNumber']
            exif_data['aperture'] = self._convert_exifread_rational(fnumber)
        
        if 'max_aperture' not in exif_data and 'EXIF MaxApertureValue' in tags:
            max_aperture = tags['EXIF MaxApertureValue']
            exif_data['max_aperture'] = self._convert_exifread_rational(max_aperture)
    
    def _extract_shutter_speed_exifread(self, tags: Dict, exif_data: Dict[str, Any]):
        """exifreadからシャッタースピードを抽出"""
        if 'exposure_time' not in exif_data and 'EXIF ExposureTime' in tags:
            exposure_time = tags['EXIF ExposureTime']
            exif_data['exposure_time'] = self._convert_exifread_rational(exposure_time)
    
    def _extract_iso_exifread(self, tags: Dict, exif_data: Dict[str, Any]):
        """exifreadからISO感度を抽出"""
        if 'iso' not in exif_data and 'EXIF ISOSpeedRatings' in tags:
            iso = tags['EXIF ISOSpeedRatings']
            exif_data['iso'] = int(self._convert_exifread_rational(iso))
    
    def _extract_additional_exif_tags(self, tags: Dict, exif_data: Dict[str, Any]):
        """追加のEXIFタグを抽出"""
        if 'EXIF ExposureBiasValue' in tags:
            exposure_bias = tags['EXIF ExposureBiasValue']
            exif_data['exposure_bias'] = self._convert_exifread_rational(exposure_bias)
        
        if 'EXIF MeteringMode' in tags:
            exif_data['metering_mode'] = str(tags['EXIF MeteringMode'])
        
        if 'EXIF Flash' in tags:
            exif_data['flash'] = str(tags['EXIF Flash'])
        
        if 'EXIF WhiteBalance' in tags:
            exif_data['white_balance'] = str(tags['EXIF WhiteBalance'])
    
    def _convert_exifread_rational(self, value: Any) -> Any:
        """exifreadの有理数を変換"""
        if hasattr(value, 'values'):
            if hasattr(value.values[0], 'numerator') and hasattr(value.values[0], 'denominator'):
                try:
                    return float(value.values[0].numerator) / float(value.values[0].denominator)
                except (ZeroDivisionError, AttributeError):
                    return str(value.values[0])
            else:
                return float(value.values[0])
        return str(value)
    
    def _extract_gps_info(self, exif: Dict) -> Dict[str, Any]:
        """PILからGPS情報を抽出"""
        gps_info = {}
        
        if not PIL_AVAILABLE:
            return gps_info
        
        try:
            # GPSタグのマッピング
            gps_tags = {}
            for tag_id, tag_name in ExifTags.TAGS.items():
                if tag_name.startswith('GPS'):
                    gps_tags[tag_id] = tag_name
            
            for tag_id, value in exif.items():
                if tag_id in gps_tags:
                    tag_name = gps_tags[tag_id]
                    if tag_name == 'GPSLatitude':
                        gps_info['gps_latitude'] = self._convert_gps_coordinate(value)
                    elif tag_name == 'GPSLongitude':
                        gps_info['gps_longitude'] = self._convert_gps_coordinate(value)
                    elif tag_name == 'GPSAltitude':
                        gps_info['gps_altitude'] = float(value)
                    elif tag_name == 'GPSTimeStamp':
                        gps_info['gps_timestamp'] = str(value)
        except Exception as e:
            print(f"GPS情報の抽出に失敗: {e}")
        
        return gps_info
    
    def _extract_gps_info_exifread(self, tags: Dict) -> Dict[str, Any]:
        """exifreadからGPS情報を抽出"""
        gps_info = {}
        
        try:
            if 'GPS GPSLatitude' in tags and 'GPS GPSLatitudeRef' in tags:
                lat = tags['GPS GPSLatitude']
                lat_ref = tags['GPS GPSLatitudeRef']
                gps_info['gps_latitude'] = self._convert_gps_coordinate_exifread(lat, lat_ref)
            
            if 'GPS GPSLongitude' in tags and 'GPS GPSLongitudeRef' in tags:
                lon = tags['GPS GPSLongitude']
                lon_ref = tags['GPS GPSLongitudeRef']
                gps_info['gps_longitude'] = self._convert_gps_coordinate_exifread(lon, lon_ref)
            
            if 'GPS GPSAltitude' in tags:
                alt = tags['GPS GPSAltitude']
                gps_info['gps_altitude'] = self._convert_exifread_rational(alt)
        except Exception as e:
            print(f"exifread GPS情報の抽出に失敗: {e}")
        
        return gps_info
    
    def _convert_gps_coordinate(self, coord_tuple: tuple) -> Optional[float]:
        """GPS座標を10進数に変換（PIL用）"""
        try:
            degrees = float(coord_tuple[0])
            minutes = float(coord_tuple[1])
            seconds = float(coord_tuple[2])
            
            decimal_degrees = degrees + (minutes / 60.0) + (seconds / 3600.0)
            return decimal_degrees
        except Exception:
            return None
    
    def _convert_gps_coordinate_exifread(self, coord: Any, ref: Any) -> Optional[float]:
        """GPS座標を10進数に変換（exifread用）"""
        try:
            if hasattr(coord, 'values'):
                def convert_rational(value: Any) -> float:
                    if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                        try:
                            return float(value.numerator) / float(value.denominator)
                        except (ZeroDivisionError, AttributeError):
                            return 0.0
                    else:
                        return float(value)
                
                degrees = convert_rational(coord.values[0])
                minutes = convert_rational(coord.values[1])
                seconds = convert_rational(coord.values[2])
                
                decimal_degrees = degrees + (minutes / 60.0) + (seconds / 3600.0)
                
                # 南緯・西経の場合は負の値にする
                if str(ref) in ['S', 'W']:
                    decimal_degrees = -decimal_degrees
                
                return decimal_degrees
        except Exception:
            return None
        
        return None
    
    def _estimate_camera_parameters(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """カメラパラメータを推定"""
        camera_params = {
            'estimated_focal_length': None,
            'estimated_sensor_size': None,
            'camera_matrix': None,
            'distortion_coefficients': None
        }
        
        # カメラメーカーを取得
        camera_make = metadata.get('camera_make', 'default')
        if camera_make:
            camera_make = camera_make.strip().split()[0]  # 最初の単語のみ使用
        
        # 焦点距離を推定
        focal_length = metadata.get('focal_length')
        focal_length_35mm = metadata.get('focal_length_35mm')
        
        if focal_length_35mm:
            # 35mm換算焦点距離から実際の焦点距離を推定
            sensor_size = self.default_sensor_sizes.get(camera_make, self.default_sensor_sizes['default'])
            crop_factor = 43.27 / max(sensor_size['width'], sensor_size['height'])  # 35mm対角線長
            camera_params['estimated_focal_length'] = focal_length_35mm / crop_factor
        elif focal_length:
            camera_params['estimated_focal_length'] = focal_length
        else:
            # デフォルト焦点距離を使用
            camera_params['estimated_focal_length'] = self.default_focal_lengths.get(
                camera_make, self.default_focal_lengths['default']
            )
        
        # センサーサイズを推定
        camera_params['estimated_sensor_size'] = self.default_sensor_sizes.get(
            camera_make, self.default_sensor_sizes['default']
        )
        
        # カメラ行列を推定
        if metadata.get('image_size') and camera_params['estimated_focal_length']:
            width = metadata['image_size']['width']
            height = metadata['image_size']['height']
            focal_length = camera_params['estimated_focal_length']
            
            # ピクセル単位の焦点距離を推定
            sensor_width = camera_params['estimated_sensor_size']['width']
            focal_length_pixels = (focal_length * width) / sensor_width
            
            camera_matrix = np.array([
                [focal_length_pixels, 0, width / 2],
                [0, focal_length_pixels, height / 2],
                [0, 0, 1]
            ])
            
            camera_params['camera_matrix'] = camera_matrix.tolist()
            
            # 歪み係数（デフォルト値）
            camera_params['distortion_coefficients'] = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        return camera_params
    
    def extract_metadata_batch(self, image_paths: List[str]) -> Dict[int, Dict[str, Any]]:
        """複数画像のメタデータを一括抽出"""
        metadata_dict = {}
        
        print(f"メタデータ抽出を開始: {len(image_paths)} 画像")
        
        for i, image_path in enumerate(image_paths):
            try:
                metadata = self.extract_metadata_from_image(image_path)
                metadata_dict[i] = metadata
                print(f"メタデータ抽出成功: {Path(image_path).name}")
            except Exception as e:
                print(f"メタデータ抽出失敗 {Path(image_path).name}: {e}")
                # デフォルトメタデータを設定
                metadata_dict[i] = self._create_default_metadata(image_path)
        
        print(f"メタデータ抽出完了: {len(metadata_dict)} 画像")
        return metadata_dict
    
    def _create_default_metadata(self, image_path: str) -> Dict[str, Any]:
        """デフォルトメタデータを作成"""
        image_path = Path(image_path)
        
        # 画像サイズを取得
        try:
            img = cv2.imread(str(image_path))
            if img is not None:
                height, width = img.shape[:2]
                image_size = {'width': width, 'height': height}
                
                # デフォルトカメラ行列を作成
                focal_length_pixels = max(width, height) * 0.8
                camera_matrix = np.array([
                    [focal_length_pixels, 0, width / 2],
                    [0, focal_length_pixels, height / 2],
                    [0, 0, 1]
                ])
            else:
                image_size = None
                camera_matrix = None
        except Exception:
            image_size = None
            camera_matrix = None
        
        return {
            'file_path': str(image_path),
            'file_name': image_path.name,
            'file_size': image_path.stat().st_size if image_path.exists() else 0,
            'creation_time': datetime.fromtimestamp(image_path.stat().st_ctime).isoformat() if image_path.exists() else None,
            'modification_time': datetime.fromtimestamp(image_path.stat().st_mtime).isoformat() if image_path.exists() else None,
            'image_size': image_size,
            'camera_make': 'Unknown',
            'camera_model': 'Unknown',
            'focal_length': None,
            'focal_length_35mm': None,
            'aperture': None,
            'max_aperture': None,
            'shutter_speed': None,
            'iso': None,
            'exposure_time': None,
            'exposure_bias': None,
            'metering_mode': None,
            'flash': None,
            'white_balance': None,
            'sensor_size': self.default_sensor_sizes['default'],
            'gps_latitude': None,
            'gps_longitude': None,
            'gps_altitude': None,
            'gps_timestamp': None,
            'orientation': 1,
            'color_space': None,
            'software': None,
            'artist': None,
            'copyright': None,
            'datetime': None,
            'estimated_focal_length': self.default_focal_lengths['default'],
            'estimated_sensor_size': self.default_sensor_sizes['default'],
            'camera_matrix': camera_matrix.tolist() if camera_matrix is not None else None,
            'distortion_coefficients': [0.0, 0.0, 0.0, 0.0, 0.0]
        }
    
    def save_metadata_json(self, metadata_dict: Dict[int, Dict[str, Any]], output_path: str):
        """メタデータをJSONファイルに保存"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # numpy配列とIFDRationalオブジェクトをリストに変換
        serializable_metadata = self._make_metadata_serializable(metadata_dict)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"メタデータを保存しました: {output_path}")
    
    def _make_metadata_serializable(self, metadata_dict: Dict[int, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """メタデータをシリアライズ可能な形式に変換"""
        serializable_metadata = {}
        for key, metadata in metadata_dict.items():
            serializable_metadata[str(key)] = {}
            for k, v in metadata.items():
                if isinstance(v, np.ndarray):
                    serializable_metadata[str(key)][k] = v.tolist()
                elif hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                    # IFDRationalオブジェクトの場合
                    try:
                        serializable_metadata[str(key)][k] = float(v.numerator) / float(v.denominator)
                    except (ZeroDivisionError, AttributeError):
                        serializable_metadata[str(key)][k] = str(v)
                elif hasattr(v, 'values'):
                    # exifreadの特殊オブジェクトの場合
                    try:
                        if hasattr(v, '__iter__'):
                            serializable_metadata[str(key)][k] = [str(item) for item in v.values]
                        else:
                            serializable_metadata[str(key)][k] = str(v)
                    except:
                        serializable_metadata[str(key)][k] = str(v)
                else:
                    serializable_metadata[str(key)][k] = v
        
        return serializable_metadata
    
    def load_metadata_json(self, input_path: str) -> Dict[int, Dict[str, Any]]:
        """JSONファイルからメタデータを読み込み"""
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"メタデータファイルが見つかりません: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 文字列キーを整数キーに変換
        metadata_dict = {}
        for key, metadata in data.items():
            metadata_dict[int(key)] = metadata
        
        return metadata_dict 