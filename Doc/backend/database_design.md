# データベース設計書

## 1. 概要

ドローン写真から3Dモデルを生成するシステムのデータベース設計です。
SQLiteを使用した開発環境向けの設計となっています。

## 2. エンティティ設計

### 2.1 User（ユーザー）
WebODMの認証情報を管理するテーブル

| カラム名 | 型 | 制約 | 説明 |
|---------|----|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | ユーザーID |
| username | VARCHAR(255) | UNIQUE, NOT NULL | WebODMユーザー名 |
| password | VARCHAR(255) | NOT NULL | パスワード（ハッシュ化） |
| email | VARCHAR(255) | UNIQUE | メールアドレス |
| first_name | VARCHAR(255) | | 名 |
| last_name | VARCHAR(255) | | 姓 |
| is_admin | BOOLEAN | DEFAULT FALSE | 管理者フラグ（trueで管理者） |
| webodm_user_id | INT | | WebODMユーザーID |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

### 2.2 Project（プロジェクト）
1ユーザ1プロジェクトのため、user_idにUNIQUE制約を追加

| カラム名 | 型 | 制約 | 説明 |
|---------|----|------|------|
| id | VARCHAR(36) | PRIMARY KEY | プロジェクトID（UUID） |
| user_id | INT | FOREIGN KEY, UNIQUE | ユーザーID（1ユーザ1プロジェクト） |
| name | VARCHAR(255) | NOT NULL | プロジェクト名 |
| description | TEXT | | プロジェクト説明 |
| webodm_project_id | VARCHAR(255) | | WebODMプロジェクトID |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

### 2.3 Task（タスク）
プロジェクトに紐づくタスクテーブル

| カラム名 | 型 | 制約 | 説明 |
|---------|----|------|------|
| id | VARCHAR(36) | PRIMARY KEY | タスクID（UUID） |
| project_id | VARCHAR(36) | FOREIGN KEY | プロジェクトID |
| name | VARCHAR(255) | NOT NULL | タスク名 |
| status | INT | NOT NULL | タスクのステータス（WebODM APIの数値） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

### 2.4 ModelResult（3Dモデル結果）
Taskと1対1で紐づくようにtask_idを追加

| カラム名 | 型 | 制約 | 説明 |
|---------|----|------|------|
| id | VARCHAR(36) | PRIMARY KEY | 結果ID（UUID） |
| task_id | VARCHAR(36) | FOREIGN KEY, UNIQUE | タスクID（1タスク1モデル） |
| glb_file_path | VARCHAR(500) | | GLBファイルパス |
| thumbnail_path | VARCHAR(500) | | サムネイル画像パス |
| vertex_count | INT | | 頂点数 |
| face_count | INT | | 面数 |
| texture_count | INT | | テクスチャ数 |
| model_size | BIGINT | | モデルファイルサイズ |
| processing_time | INT | | 処理時間（秒） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 作成日時 |

**ステータス定義:**
- `started`: 開始
- `in_progress`: 進行中
- `completed`: 完了
- `failed`: 失敗

**処理ステップ定義:**
- `file_upload`: ファイルアップロード
- `webodm_processing`: WebODM処理
- `model_conversion`: モデル変換
- `thumbnail_generation`: サムネイル生成
- `metadata_extraction`: メタデータ抽出

## 3. リレーションシップ

```
User (1) ←→ (1) Project
Project (1) ←→ (N) Task
Task (1) ←→ (1) ModelResult
```

## 4. インデックス設計

### 4.1 主キーインデックス
- 全てのテーブルのidカラム

### 4.2 外部キーインデックス
- Project.user_id
- Task.project_id
- ModelResult.task_id

### 4.3 検索用インデックス
- User.username
- User.email
- Project.created_at
- Task.status
- Task.created_at

## 5. データ型の詳細

### 5.1 ENUM定義

（WebODM APIの数値ステータスを使用するため、ENUM定義は不要）

**WebODM Taskステータス（数値）:**
- 10: 待機中（QUEUED）
- 20: 処理中（RUNNING）
- 30: 失敗（FAILED）
- 40: 完了（COMPLETED）
- 50: キャンセル（CANCELED）

### 5.2 制約

**NOT NULL制約:**
- User.username, User.password
- User.is_admin
- Project.name
- Task.name, Task.status
- UploadedFile.original_filename, UploadedFile.stored_filename, UploadedFile.file_path, UploadedFile.file_size, UploadedFile.mime_type

**UNIQUE制約:**
- User.username
- User.email
- Project.id
- Project.user_id
- Task.id
- UploadedFile.id
- ModelResult.id
- ModelResult.task_id

## 6. ファイル保存戦略

### 6.1 ディレクトリ構造
```
uploads/
├── projects/
│   └── {project_id}/
│       ├── original/          # 元のアップロードファイル
│       ├── tasks/
│       │   └── {task_id}/
│       │       ├── models/   # 3Dモデルファイル
│       │       │   ├── gltf/
│       │       │   ├── glb/
│       │       │   └── obj/
│       │       ├── thumbnails/ # サムネイル画像
│       │       └── temp/     # 一時ファイル
```

### 6.2 ファイル命名規則
- glTFファイル: `model_{task_id}.gltf`
- GLBファイル: `model_{task_id}.glb`
- OBJファイル: `model_{task_id}.obj`
- サムネイル: `thumbnail_{task_id}.png`

## 7. パフォーマンス考慮事項

### 7.1 クエリ最適化
- プロジェクト一覧取得時のJOIN最小化
- ステータス別のインデックス活用
- ページネーション対応

### 7.2 ストレージ最適化
- 古いファイルの自動削除
- 圧縮ファイルの活用
- CDN連携の考慮

### 7.3 バックアップ戦略
- 定期的なDBバックアップ
- ファイルシステムのバックアップ
- 災害復旧計画

## 8. セキュリティ考慮事項

### 8.1 データ保護
- 個人情報の暗号化
- ファイルアクセス制御
- SQLインジェクション対策

### 8.2 監査ログ
- ファイルアップロードログ
- 処理実行ログ
- エラーログ

## 9. マイグレーション戦略

### 9.1 初期マイグレーション
- 全テーブルの作成
- インデックスの作成
- 初期データの投入

### 9.2 スキーマ変更
- 後方互換性の維持
- データ移行計画
- ロールバック計画 

---

## 付録：この設計でDBを作成するためのSQL（MySQL用DDL例）

```sql
-- ユーザーテーブル
CREATE TABLE User (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    webodm_user_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- プロジェクトテーブル（1ユーザ1プロジェクト）
CREATE TABLE Project (
    id VARCHAR(36) PRIMARY KEY,
    user_id INT UNIQUE, -- 1ユーザ1プロジェクト
    name VARCHAR(255) NOT NULL,
    description TEXT,
    webodm_project_id VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(id)
);

-- タスクテーブル（1プロジェクトNタスク）
CREATE TABLE Task (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36),
    name VARCHAR(255) NOT NULL,
    status INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES Project(id)
);

-- モデル結果テーブル（1タスク1モデル）
CREATE TABLE ModelResult (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) UNIQUE, -- 1タスク1モデル
    glb_file_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    vertex_count INT,
    face_count INT,
    texture_count INT,
    model_size BIGINT,
    processing_time INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES Task(id)
);
```

-- 必要に応じてインデックスや他の制約も追加してください。 

---

## 10. WebODM管理者API連携

### 管理者APIエンドポイント例
- GET    /api/admin/users/      : ユーザー一覧取得（管理者のみ）
- POST   /api/admin/users/      : ユーザー新規作成（管理者のみ）
- GET    /api/admin/users/:id   : ユーザー詳細取得（管理者のみ）
- PUT    /api/admin/users/:id   : ユーザー情報更新（管理者のみ）
- DELETE /api/admin/users/:id   : ユーザー削除（管理者のみ）

### サインアップAPI
- POST   /api/signup           : ユーザー新規登録（一般ユーザー向け）

#### サインアップAPI パラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|----|------|------|
| username | string | ○ | ユーザー名 |
| password | string | ○ | パスワード |
| email | string | | メールアドレス |
| first_name | string | | 名 |
| last_name | string | | 姓 |

#### サインアップAPI 利用例
```bash
curl -X POST http://localhost:3000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "password123",
    "email": "user@example.com",
    "first_name": "太郎",
    "last_name": "山田"
  }'
```

### 利用例
- JWTトークンをAuthorizationヘッダーに付与してリクエスト
- isAdmin判定で認可制御
- サインアップは管理者権限でWebODMにユーザー作成

### 環境変数設定
```
WEBODM_ADMIN_TOKEN=your_admin_jwt_token
```

### 参考
- [WebODM公式ドキュメント 管理者API](https://docs.webodm.org/#admin-users) 