# データベース実装手順書

## 1. 概要

このドキュメントは、ドローン写真3Dモデル生成システムのデータベース実装手順を説明します。

## 2. 前提条件

- Node.js v18以上
- npm または yarn
- Prisma CLI

## 3. 実装手順

### 3.1 Prismaのインストール

```bash
cd backend
npm install prisma @prisma/client
```

### 3.2 スキーマファイルの配置

1. `Doc/backend/prisma_schema.prisma` を `backend/prisma/schema.prisma` にコピー
2. 既存のスキーマファイルを上書き

### 3.3 環境変数の設定

`.env` ファイルに以下を追加：

```env
DATABASE_URL="file:./dev.db"
```

### 3.4 データベースの初期化

```bash
# マイグレーションの生成と適用
npx prisma migrate dev --name init_drone_photo_schema

# Prismaクライアントの生成
npx prisma generate
```

### 3.5 データベースの確認

```bash
# Prisma Studioでデータベースを確認
npx prisma studio
```

## 4. NestJSとの統合

### 4.1 PrismaServiceの作成

`backend/src/prisma/prisma.service.ts` を作成：

```typescript
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '../generated/prisma';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  async onModuleInit() {
    await this.$connect();
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }
}
```

### 4.2 PrismaModuleの作成

`backend/src/prisma/prisma.module.ts` を作成：

```typescript
import { Global, Module } from '@nestjs/common';
import { PrismaService } from './prisma.service';

@Global()
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class PrismaModule {}
```

### 4.3 AppModuleの更新

`backend/src/app.module.ts` にPrismaModuleを追加：

```typescript
import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PrismaModule } from './prisma/prisma.module';
// ... 他のインポート

@Module({
  imports: [PrismaModule, /* 他のモジュール */],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
```

## 5. サービス層の実装例

### 5.1 UserService

```typescript
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { User } from '../generated/prisma';

@Injectable()
export class UserService {
  constructor(private prisma: PrismaService) {}

  async createUser(data: {
    username: string;
    email?: string;
    webodm_token?: string;
    token_expires_at?: Date;
  }): Promise<User> {
    return this.prisma.user.create({
      data,
    });
  }

  async findUserByUsername(username: string): Promise<User | null> {
    return this.prisma.user.findUnique({
      where: { username },
    });
  }

  async updateWebODMToken(
    userId: number,
    token: string,
    expiresAt: Date,
  ): Promise<User> {
    return this.prisma.user.update({
      where: { id: userId },
      data: {
        webodm_token: token,
        token_expires_at: expiresAt,
      },
    });
  }
}
```

### 5.2 ProjectService

```typescript
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { Project, ProjectStatus } from '../generated/prisma';

@Injectable()
export class ProjectService {
  constructor(private prisma: PrismaService) {}

  async createProject(data: {
    userId: number;
    name: string;
    description?: string;
  }): Promise<Project> {
    return this.prisma.project.create({
      data: {
        ...data,
        status: ProjectStatus.PENDING,
      },
    });
  }

  async updateProjectStatus(
    projectId: string,
    status: ProjectStatus,
  ): Promise<Project> {
    return this.prisma.project.update({
      where: { id: projectId },
      data: { status },
    });
  }

  async getProjectsByUserId(userId: number): Promise<Project[]> {
    return this.prisma.project.findMany({
      where: { user_id: userId },
      include: {
        model_result: true,
        processing_logs: {
          orderBy: { created_at: 'desc' },
          take: 1,
        },
      },
    });
  }
}
```

## 6. ファイルアップロード処理

### 6.1 UploadedFileService

```typescript
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { UploadedFile } from '../generated/prisma';
import * as fs from 'fs';
import * as path from 'path';

@Injectable()
export class UploadedFileService {
  constructor(private prisma: PrismaService) {}

  async saveFile(
    projectId: string,
    file: Express.Multer.File,
  ): Promise<UploadedFile> {
    const timestamp = Date.now();
    const storedFilename = `${timestamp}_${file.originalname}`;
    const filePath = path.join('uploads', 'projects', projectId, 'original', storedFilename);

    // ディレクトリの作成
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // ファイルの保存
    fs.writeFileSync(filePath, file.buffer);

    // データベースに記録
    return this.prisma.uploadedFile.create({
      data: {
        project_id: projectId,
        original_filename: file.originalname,
        stored_filename: storedFilename,
        file_path: filePath,
        file_size: BigInt(file.size),
        mime_type: file.mimetype,
      },
    });
  }
}
```

## 7. 処理ログの管理

### 7.1 ProcessingLogService

```typescript
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { ProcessingLog, ProcessingStep, ProcessingStatus } from '../generated/prisma';

@Injectable()
export class ProcessingLogService {
  constructor(private prisma: PrismaService) {}

  async createLog(data: {
    projectId: string;
    step: ProcessingStep;
    message?: string;
  }): Promise<ProcessingLog> {
    return this.prisma.processingLog.create({
      data: {
        ...data,
        status: ProcessingStatus.STARTED,
        progress: 0,
      },
    });
  }

  async updateLogProgress(
    logId: string,
    progress: number,
    status: ProcessingStatus,
    message?: string,
  ): Promise<ProcessingLog> {
    return this.prisma.processingLog.update({
      where: { id: logId },
      data: {
        progress,
        status,
        message,
      },
    });
  }

  async logError(
    logId: string,
    errorDetails: string,
  ): Promise<ProcessingLog> {
    return this.prisma.processingLog.update({
      where: { id: logId },
      data: {
        status: ProcessingStatus.FAILED,
        error_details: errorDetails,
      },
    });
  }
}
```

## 8. テストデータの投入

### 8.1 シードスクリプト

`backend/prisma/seed.ts` を作成：

```typescript
import { PrismaClient } from '../src/generated/prisma';

const prisma = new PrismaClient();

async function main() {
  // テストユーザーの作成
  const user = await prisma.user.create({
    data: {
      username: 'testuser',
      email: 'test@example.com',
    },
  });

  // テストプロジェクトの作成
  const project = await prisma.project.create({
    data: {
      user_id: user.id,
      name: 'テストプロジェクト',
      description: 'ドローン写真のテストプロジェクト',
      status: 'PENDING',
    },
  });

  console.log('シードデータが作成されました:', { user, project });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
```

### 8.2 シードの実行

```bash
npx ts-node prisma/seed.ts
```

## 9. 運用・保守

### 9.1 バックアップ

```bash
# データベースのバックアップ
cp dev.db dev.db.backup.$(date +%Y%m%d_%H%M%S)
```

### 9.2 ログローテーション

古いログの削除：

```sql
DELETE FROM processing_logs 
WHERE created_at < datetime('now', '-30 days');
```

### 9.3 パフォーマンス監視

```bash
# データベースサイズの確認
ls -lh dev.db

# テーブルサイズの確認
sqlite3 dev.db "SELECT name, sql FROM sqlite_master WHERE type='table';"
```

## 10. トラブルシューティング

### 10.1 よくある問題

1. **マイグレーションエラー**
   ```bash
   npx prisma migrate reset
   npx prisma migrate dev
   ```

2. **Prismaクライアントの再生成**
   ```bash
   npx prisma generate
   ```

3. **データベースのリセット**
   ```bash
   rm dev.db
   npx prisma migrate dev
   ```

### 10.2 デバッグ

```bash
# Prisma Studioでデータベースを確認
npx prisma studio

# クエリのログを有効化
# .env に追加: DEBUG="prisma:query"
```

## 11. 次のステップ

1. コントローラーの実装
2. バリデーションの追加
3. 認証・認可の実装
4. エラーハンドリングの強化
5. テストの作成 