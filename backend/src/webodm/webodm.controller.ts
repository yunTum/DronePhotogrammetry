import { Controller, Get, Post, Put, Delete, Body, Param, Query, Res, Req, UseInterceptors, UploadedFiles, ForbiddenException } from '@nestjs/common';
import { FilesInterceptor } from '@nestjs/platform-express';
import { Response, Request } from 'express';
import { ApiTags, ApiSecurity, ApiOperation, ApiParam, ApiBody, ApiResponse, ApiConsumes } from '@nestjs/swagger';
import { WebodmService } from './webodm.service';
import { UserService } from '../user.service';
import { 
  CreateProjectDto, 
  CreateTaskDto, 
  CreateAdminUserDto, 
  UpdateAdminUserDto, 
  SignupDto,
  ProjectResponseDto,
  TaskResponseDto,
  UserResponseDto 
} from './webodm.dto';
import * as fs from 'fs';
import * as path from 'path';


@ApiTags('webodm')
@ApiSecurity('JWT-auth')
@Controller('api')
export class WebodmController {
  constructor(
    private readonly webodmService: WebodmService,
    private readonly userService: UserService
  ) {}

  // プロジェクト一覧の取得
  @ApiOperation({ summary: 'プロジェクト一覧取得' })
  @ApiResponse({ 
    status: 200, 
    description: 'プロジェクト一覧取得成功',
    type: [ProjectResponseDto]
  })
  @Get('projects/')
  async getProjects(@Req() req: Request, @Res() res: Response) {
    try {
      const token = this.extractToken(req);
      const user = (req as any).user;
      const projects = await this.webodmService.getProjects(token);
      let filtered = projects;
      if (!user?.isAdmin) {
        filtered = projects.filter((p: any) => p.user_id === user?.id);
      }
      res.json(filtered);
    } catch (error) {
      console.error('プロジェクト一覧取得エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // プロジェクト作成
  @ApiOperation({ summary: 'プロジェクト作成' })
  @ApiBody({ type: CreateProjectDto })
  @ApiResponse({ 
    status: 201, 
    description: 'プロジェクト作成成功',
    type: ProjectResponseDto
  })
  @Post('projects/')
  async createProject(@Body() body: CreateProjectDto, @Req() req: Request, @Res() res: Response) {
    try {
      const token = this.extractToken(req);
      const user = (req as any).user;
      // 一般ユーザーは自分のプロジェクトのみ作成可
      // 管理者は任意のユーザーのプロジェクト作成可（必要ならbodyにuser_idを追加）
      const project = await this.webodmService.createProject(body.name, token);
      res.json(project);
    } catch (error) {
      console.error('プロジェクト作成エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // プロジェクト取得
  @ApiOperation({ summary: 'プロジェクト詳細取得' })
  @ApiParam({ name: 'id', description: 'プロジェクトID', type: String })
  @ApiResponse({ 
    status: 200, 
    description: 'プロジェクト詳細取得成功',
    type: ProjectResponseDto
  })
  @Get('projects/:id')
  async getProject(@Param('id') id: string, @Req() req: Request, @Res() res: Response) {
    try {
      const token = this.extractToken(req);
      const project = await this.webodmService.getProject(parseInt(id), token);
      res.json(project);
    } catch (error) {
      console.error('プロジェクト取得エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // タスク一覧取得
  @ApiOperation({ summary: 'タスク一覧取得' })
  @ApiParam({ name: 'projectId', description: 'プロジェクトID', type: String })
  @ApiResponse({ 
    status: 200, 
    description: 'タスク一覧取得成功',
    type: [TaskResponseDto]
  })
  @Get('projects/:projectId/tasks')
  async getTasks(@Param('projectId') projectId: string, @Req() req: Request, @Res() res: Response) {
    try {
      const token = this.extractToken(req);
      const tasks = await this.webodmService.getTasks(parseInt(projectId), token);
      res.json(tasks);
    } catch (error) {
      console.error('タスク一覧取得エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // タスク作成
  @ApiOperation({ summary: 'タスク作成（画像アップロード）' })
  @ApiParam({ name: 'projectId', description: 'プロジェクトID', type: String })
  @ApiConsumes('multipart/form-data')
  @ApiBody({ 
    type: CreateTaskDto,
    description: 'タスク作成用データ'
  })
  @ApiResponse({ 
    status: 201, 
    description: 'タスク作成成功',
    type: TaskResponseDto
  })
  @Post('projects/:projectId/tasks/')
  @UseInterceptors(FilesInterceptor('images'))
  async createTask(
    @Param('projectId') projectId: string,
    @UploadedFiles() files: Express.Multer.File[],
    @Body() body: CreateTaskDto,
    @Req() req: Request,
    @Res() res: Response
  ) {
    try {
      const token = this.extractToken(req);
      
      // optionsパラメータの安全な処理
      let options: string[] = [];
      if (body.options) {
        try {
          // まずJSONとしてパースを試行
          options = JSON.parse(body.options);
        } catch (parseError) {
          // JSONパースに失敗した場合、カンマ区切りの文字列として処理
          if (typeof body.options === 'string') {
            options = body.options.split(',').map(option => option.trim()).filter(option => option.length > 0);
          }
        }
      }
      
      const task = await this.webodmService.createTask(parseInt(projectId), files, options, token);
      res.json(task);
    } catch (error) {
      console.error('タスク作成エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // タスク詳細の取得
  @ApiOperation({ summary: 'タスク詳細取得' })
  @ApiParam({ name: 'projectId', description: 'プロジェクトID', type: String })
  @ApiParam({ name: 'taskId', description: 'タスクID', type: String })
  @ApiResponse({ 
    status: 200, 
    description: 'タスク詳細取得成功',
    type: TaskResponseDto
  })
  @Get('projects/:projectId/tasks/:taskId/')
  async getTask(
    @Param('projectId') projectId: string,
    @Param('taskId') taskId: string,
    @Req() req: Request,
    @Res() res: Response
  ) {
    try {
      const token = this.extractToken(req);
      const task = await this.webodmService.getTask(parseInt(projectId), taskId, token);

      res.json(task);
    } catch (error) {
      console.error('タスク詳細取得エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // タスク削除
  @ApiOperation({ summary: 'タスク削除（管理者のみ）' })
  @ApiParam({ name: 'projectId', description: 'プロジェクトID', type: String })
  @ApiParam({ name: 'taskId', description: 'タスクID', type: String })
  @ApiResponse({ status: 200, description: 'タスク削除成功' })
  @ApiResponse({ status: 403, description: '管理者のみ操作可能' })
  @Delete('projects/:projectId/tasks/:taskId/')
  async deleteTask(
    @Param('projectId') projectId: string,
    @Param('taskId') taskId: string,
    @Req() req: Request,
    @Res() res: Response
  ) {
    try {
      const token = this.extractToken(req);
      const user = (req as any).user;
      if (!user?.isAdmin) {
        throw new ForbiddenException('管理者のみ操作可能');
      }
      await this.webodmService.deleteTask(parseInt(projectId), taskId, token);
      res.json({ message: 'タスクを削除しました' });
    } catch (error) {
      console.error('タスク削除エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // タスクの再実行
  @ApiOperation({ summary: 'タスク再実行' })
  @ApiParam({ name: 'projectId', description: 'プロジェクトID', type: String })
  @ApiParam({ name: 'taskId', description: 'タスクID', type: String })
  @ApiResponse({ 
    status: 200, 
    description: 'タスク再実行成功',
    type: TaskResponseDto
  })
  @Post('projects/:projectId/tasks/:taskId/restart/')
  async restartTask(
    @Param('projectId') projectId: string,
    @Param('taskId') taskId: string,
    @Req() req: Request,
    @Res() res: Response
  ) {
    try {
      const token = this.extractToken(req);
      const task = await this.webodmService.restartTask(parseInt(projectId), taskId, token);

      res.json(task);
    } catch (error) {
      console.error('タスク再実行エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // ファイルダウンロード
  @ApiOperation({ summary: 'ファイルダウンロード' })
  @ApiParam({ name: 'projectId', description: 'プロジェクトID', type: String })
  @ApiParam({ name: 'taskId', description: 'タスクID', type: String })
  @ApiParam({ name: 'filename', description: 'ファイル名', type: String })
  @ApiResponse({ status: 200, description: 'ファイルダウンロード成功' })
  @Get('projects/:projectId/tasks/:taskId/download/:filename')
  async downloadFile(
    @Param('projectId') projectId: string,
    @Param('taskId') taskId: string,
    @Param('filename') filename: string,
    @Req() req: Request,
    @Res() res: Response
  ) {
    try {
      const token = this.extractToken(req);
      const fileBuffer = await this.webodmService.downloadFile(parseInt(projectId), taskId, filename, token);
      
      res.setHeader('Content-Type', 'application/octet-stream');
      res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
      res.setHeader('Content-Length', fileBuffer.length.toString());
      res.send(fileBuffer);
    } catch (error) {
      console.error('ファイルダウンロードエラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // モデル取得（GLB変換付き）
  @ApiOperation({ summary: '3Dモデル取得（GLB変換）' })
  @ApiParam({ name: 'projectId', description: 'プロジェクトID' })
  @ApiParam({ name: 'taskId', description: 'タスクID' })
  @ApiResponse({ status: 200, description: 'GLBモデル取得成功' })
  @ApiResponse({ status: 404, description: 'モデルが見つかりません' })
  @Get('projects/:projectId/tasks/:taskId/model')
  async getModel(
    @Param('projectId') projectId: string,
    @Param('taskId') taskId: string,
    @Req() req: Request,
    @Res() res: Response
  ) {
    try {
      const token = this.extractToken(req);
      if (!token) throw new ForbiddenException('認証トークンが必要です');

      // タスクの状態を確認
      const task = await this.webodmService.getTask(parseInt(projectId), taskId, token);
      
      // タスクが完了していない場合はエラー
      if (task.status !== 40) {
        throw new Error(`タスクが完了していません。現在のステータス: ${task.statusLabel || task.status}`);
      }

      // GLBファイルのパスを生成
      const glbFileName = `${taskId}.glb`;
      const glbFilePath = path.join(process.cwd(), 'uploads', 'users', 'projects', 'model', 'glb', glbFileName);

      // GLBファイルが既に存在する場合は直接返す
      if (fs.existsSync(glbFilePath)) {
        console.log('既存のGLBファイルを使用:', glbFilePath);
        return res.sendFile(glbFilePath);
      }

      // ZIPファイルをダウンロードしてGLB変換
      console.log('ZIPファイルをダウンロードしてGLB変換を開始');
      const zipBuffer = await this.webodmService.downloadFile(parseInt(projectId), taskId, 'textured_model.zip', token);
      
      // 既存のGLB変換APIを使用
      const { convertZipToGlb } = require('../common/zip-to-gltf');
      const glbBuffer = await convertZipToGlb(zipBuffer);
      
      console.log(`GLB変換完了: ${glbBuffer.length} bytes`);

      // GLBディレクトリを作成
      const glbDir = path.join(process.cwd(), 'uploads', 'users', 'projects', 'model', 'glb');
      if (!fs.existsSync(glbDir)) {
        fs.mkdirSync(glbDir, { recursive: true });
      }

      // GLBファイルを保存
      fs.writeFileSync(glbFilePath, glbBuffer);
      console.log('GLBファイルを保存:', glbFilePath);

      // GLBファイルを返す
      res.setHeader('Content-Type', 'model/gltf-binary');
      res.setHeader('Content-Disposition', `attachment; filename="${glbFileName}"`);
      res.setHeader('Content-Length', glbBuffer.length.toString());
      res.send(glbBuffer);

    } catch (error) {
      console.error('モデル取得エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // 管理者: ユーザー一覧取得
  @ApiOperation({ summary: '管理者: ユーザー一覧取得（管理者のみ）' })
  @ApiResponse({ 
    status: 200, 
    description: 'ユーザー一覧取得成功',
    type: [UserResponseDto]
  })
  @ApiResponse({ status: 403, description: '管理者のみ操作可能' })
  @Get('admin/users')
  async getAdminUsers(@Req() req: Request, @Res() res: Response) {
    try {
      const token = this.extractToken(req);
      if (!token) throw new ForbiddenException('認証トークンが必要です');
      const user = (req as any).user;
      if (!user?.isAdmin) throw new ForbiddenException('管理者のみ操作可能');
      const users = await this.webodmService.getAdminUsers(token);
      res.json(users);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  // 管理者: ユーザー作成
  @ApiOperation({ summary: '管理者: ユーザー作成（管理者のみ）' })
  @ApiBody({ type: CreateAdminUserDto })
  @ApiResponse({ 
    status: 201, 
    description: 'ユーザー作成成功',
    type: UserResponseDto
  })
  @ApiResponse({ status: 403, description: '管理者のみ操作可能' })
  @Post('admin/users')
  async createAdminUser(@Body() body: CreateAdminUserDto, @Req() req: Request, @Res() res: Response) {
    try {
      const token = this.extractToken(req);
      if (!token) throw new ForbiddenException('認証トークンが必要です');
      const user = (req as any).user;
      if (!user?.isAdmin) throw new ForbiddenException('管理者のみ操作可能');
      const created = await this.webodmService.createAdminUser(body, token);
      res.json(created);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  // 管理者: ユーザー取得
  @ApiOperation({ summary: '管理者: ユーザー詳細取得（管理者のみ）' })
  @ApiParam({ name: 'id', description: 'ユーザーID', type: String })
  @ApiResponse({ 
    status: 200, 
    description: 'ユーザー詳細取得成功',
    type: UserResponseDto
  })
  @ApiResponse({ status: 403, description: '管理者のみ操作可能' })
  @Get('admin/users/:id')
  async getAdminUser(@Param('id') id: string, @Req() req: Request, @Res() res: Response) {
    try {
      const token = this.extractToken(req);
      if (!token) throw new ForbiddenException('認証トークンが必要です');
      const user = (req as any).user;
      if (!user?.isAdmin) throw new ForbiddenException('管理者のみ操作可能');
      const result = await this.webodmService.getAdminUser(Number(id), token);
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  // 管理者: ユーザー更新
  @ApiOperation({ summary: '管理者: ユーザー情報更新（管理者のみ）' })
  @ApiParam({ name: 'id', description: 'ユーザーID', type: String })
  @ApiBody({ type: UpdateAdminUserDto })
  @ApiResponse({ 
    status: 200, 
    description: 'ユーザー更新成功',
    type: UserResponseDto
  })
  @ApiResponse({ status: 403, description: '管理者のみ操作可能' })
  @Put('admin/users/:id')
  async updateAdminUser(@Param('id') id: string, @Body() body: UpdateAdminUserDto, @Req() req: Request, @Res() res: Response) {
    try {
      const token = this.extractToken(req);
      if (!token) throw new ForbiddenException('認証トークンが必要です');
      const user = (req as any).user;
      if (!user?.isAdmin) throw new ForbiddenException('管理者のみ操作可能');
      const updated = await this.webodmService.updateAdminUser(Number(id), body, token);
      res.json(updated);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  // 管理者: ユーザー削除
  @ApiOperation({ summary: '管理者: ユーザー削除（管理者のみ）' })
  @ApiParam({ name: 'id', description: 'ユーザーID', type: String })
  @ApiResponse({ status: 200, description: 'ユーザー削除成功' })
  @ApiResponse({ status: 403, description: '管理者のみ操作可能' })
  @Delete('admin/users/:id')
  async deleteAdminUser(@Param('id') id: string, @Req() req: Request, @Res() res: Response) {
    try {
      const token = this.extractToken(req);
      if (!token) throw new ForbiddenException('認証トークンが必要です');
      const user = (req as any).user;
      if (!user?.isAdmin) throw new ForbiddenException('管理者のみ操作可能');
      await this.webodmService.deleteAdminUser(Number(id), token);
      res.json({ message: '削除しました' });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  // サインアップ
  @ApiOperation({ summary: 'ユーザーサインアップ' })
  @ApiBody({ type: SignupDto })
  @ApiResponse({ 
    status: 201, 
    description: 'サインアップ成功',
    type: UserResponseDto
  })
  @Post('signup')
  async signup(@Body() body: SignupDto, @Req() req: Request, @Res() res: Response) {
    try {
      // 管理者トークンを環境変数から取得（または管理者アカウントでログインして取得）
      const adminToken = process.env.WEBODM_ADMIN_TOKEN;
      if (!adminToken) {
        throw new Error('管理者トークンが設定されていません');
      }

      // WebODMにユーザー作成
      const webodmUser = await this.webodmService.signupUser(body, adminToken);
      
      // アプリ側DBにもユーザー作成
      const appUser = await this.userService.create({
        username: body.username,
        password: body.password, // UserServiceでハッシュ化される
        email: body.email,
        first_name: body.first_name,
        last_name: body.last_name,
        isAdmin: false,
        webodm_user_id: webodmUser.id
      });
      
      // 成功レスポンス
      res.json({
        message: 'ユーザー登録が完了しました',
        user: {
          id: appUser.id,
          username: appUser.username,
          email: appUser.email,
          webodm_user_id: appUser.webodm_user_id
        }
      });
    } catch (error) {
      console.error('サインアップエラー:', error);
      res.status(400).json({ error: error.message });
    }
  }

  // 認証トークンからJWTトークンを抽出
  private extractToken(req: Request): string | null {
    const authHeader = req.headers.authorization;
    if (authHeader && authHeader.startsWith('JWT ')) {
      return authHeader.substring(4);
    }
    return null;
  }
} 