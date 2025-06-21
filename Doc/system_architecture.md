# システム構成案（drone_photo）

## 1. 全体構成図

```
[frontend] ⇄ [backend (NestJS)] ⇄ [webodrm]
```

## 2. 各コンポーネントの役割

### frontend
- 画像・動画のアップロードUI
- 処理状況・3Dモデル結果の表示
- webodrm認証情報の管理

### backend (NestJS)
- アップロードファイルの受け取りAPI
- webodrm認証管理
- webodrmへの処理リクエスト
- 3Dモデル（zip）の受け取り・保存
- 3Dモデルをfrontで表示できる形式（例：glTF, obj, 画像サムネイル等）に変換するAPI
- サムネイル生成・メタデータ抽出・管理

### webodrm
- 画像・動画から3Dモデルを生成
- 生成した3Dモデルをzipで返却
- 処理ステータス管理
- ユーザー認証・セッション管理

## 3. データフロー

1. frontでwebodrmにログイン
2. frontで画像・動画をアップロード
3. backendがファイルを受け取り、webodrmに処理依頼（認証トークン付き）
4. webodrmが3Dモデル（zip）を生成しbackendへ返却
5. backendが3Dモデルを保存し、必要に応じて変換
6. backendがサムネイル生成・メタデータ抽出を実行
7. frontendが3Dモデルをダウンロードまたは表示

## 4. 詳細API仕様

### 4.1 webodrm認証
- **エンドポイント**: `POST /api/auth/login`
- **リクエスト**:
  ```json
  {
    "username": "webodrm_username",
    "password": "webodrm_password"
  }
  ```
- **レスポンス**:
  ```json
  {
    "token": "webodrm_auth_token",
    "expiresAt": "2024-01-01T00:00:00Z"
  }
  ```

- **エンドポイント**: `POST /api/auth/logout`
- **リクエスト**: なし
- **レスポンス**:
  ```json
  {
    "message": "ログアウトしました"
  }
  ```

### 4.2 画像・動画アップロード
- **エンドポイント**: `POST /api/upload`
- **リクエスト**: multipart/form-data
  - `file`: 画像または動画ファイル（必須）
  - `description`: 説明文（任意）
- **認証**: webodrm認証トークン必須
- **レスポンス**:
  ```json
  {
    "id": "uuid-string",
    "status": "processing",
    "message": "ファイルが正常にアップロードされました"
  }
  ```

### 4.3 処理状況取得
- **エンドポイント**: `GET /api/status/:id`
- **パスパラメータ**:
  - `id`: アップロード時に発行された処理ID
- **認証**: webodrm認証トークン必須
- **レスポンス**:
  ```json
  {
    "id": "uuid-string",
    "status": "processing|done|error",
    "progress": 0-100,
    "message": "処理状況の説明"
  }
  ```
- **備考**: webodrmからステータスを取得

### 4.4 3Dモデル取得
- **エンドポイント**: `GET /api/result/:id`
- **パスパラメータ**:
  - `id`: アップロード時に発行された処理ID
- **認証**: webodrm認証トークン必須
- **レスポンス**:
  - 200 OK: 3DモデルのglTF/GLBファイル
  - 404 Not Found: 処理中または存在しない場合
- **備考**: webodrmからzipを取得後、バックエンドでglTF/GLBに変換

### 4.5 サムネイル取得
- **エンドポイント**: `GET /api/thumbnail/:id`
- **パスパラメータ**:
  - `id`: アップロード時に発行された処理ID
- **レスポンス**:
  - 200 OK: サムネイル画像（PNG/JPG）
  - 404 Not Found: 存在しない場合
- **備考**: バックエンドで生成・管理

### 4.6 メタデータ取得
- **エンドポイント**: `GET /api/metadata/:id`
- **パスパラメータ**:
  - `id`: アップロード時に発行された処理ID
- **レスポンス**:
  ```json
  {
    "id": "uuid-string",
    "originalFile": {
      "name": "filename.jpg",
      "size": 1024000,
      "type": "image/jpeg"
    },
    "modelInfo": {
      "format": "glTF",
      "fileSize": 512000,
      "vertexCount": 10000,
      "textureCount": 2
    },
    "createdAt": "2024-01-01T00:00:00Z",
    "processedAt": "2024-01-01T00:05:00Z"
  }
  ```
- **備考**: バックエンドで生成・管理

## 5. Backend変換機能詳細

### 5.1 変換処理フロー
```
webodrm(zip) → 解凍 → 3D形式変換 → glTF/GLB + サムネイル + メタデータ
```

### 5.2 変換対象形式
- **入力**: OBJ, PLY, FBX, DAE等
- **出力**: glTF/GLB（推奨）、OBJ+MTL

### 5.3 変換ライブラリ
- **Python**: Blender Python API, Assimp
- **Node.js**: gltf-pipeline, obj2gltf
- **C++**: Assimp, OpenCOLLADA

### 5.4 サムネイル生成
- 3Dモデルから複数角度のスクリーンショット生成
- 代表的な1枚をサムネイルとして保存

## 6. Frontend表示詳細

### 6.1 3D表示ライブラリ
- **Three.js**: 汎用的な3D表示
- **Babylon.js**: 高機能な3D表示
- **model-viewer**: Web Componentsベースの3D表示

### 6.2 表示機能
- 3Dモデルの回転・ズーム・パン
- ワイヤーフレーム表示
- テクスチャ切り替え
- アニメーション再生（対応する場合）

### 6.3 レスポンシブ対応
- モバイル・タブレット・デスクトップ対応
- タッチ操作対応

## 7. エラーハンドリング

### 7.1 アップロードエラー
- ファイルサイズ制限（例：100MB）
- 対応形式チェック（画像：JPG, PNG / 動画：MP4, MOV）
- ネットワークエラー

### 7.2 処理エラー
- webodrm処理失敗
- 変換処理失敗
- ファイル破損

### 7.3 エラーレスポンス形式
```json
{
  "error": "ERROR_CODE",
  "message": "エラーの詳細説明",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 8. セキュリティ考慮事項

### 8.1 ファイルアップロード
- ファイル形式検証
- ファイルサイズ制限
- マルウェアスキャン

### 8.2 API認証
- JWT認証
- APIキー認証
- レート制限

### 8.3 データ保護
- 一時ファイルの自動削除
- 個人情報の暗号化
- アクセスログ記録

## 9. パフォーマンス最適化

### 9.1 ファイル処理
- 非同期処理
- プログレス表示
- キャッシュ機能

### 9.2 3D表示
- LOD（Level of Detail）
- テクスチャ圧縮
- 遅延読み込み

### 9.3 スケーラビリティ
- マイクロサービス化
- ロードバランサー
- CDN活用 