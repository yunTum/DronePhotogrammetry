import { Controller, Get, Post, Put, Delete, Body, Param, Query, Res, Req, UseInterceptors, UploadedFiles, ForbiddenException } from '@nestjs/common';
import { FilesInterceptor } from '@nestjs/platform-express';
import { Response, Request } from 'express';
import { WebodmService } from './webodm.service';
import { UserService } from '../user.service';

@Controller('api')
export class WebodmController {
  constructor(
    private readonly webodmService: WebodmService,
    private readonly userService: UserService
  ) {}

  // プロジェクト一覧の取得
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
  @Post('projects/')
  async createProject(@Body() body: { name: string }, @Req() req: Request, @Res() res: Response) {
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
  @Post('projects/:projectId/tasks/')
  @UseInterceptors(FilesInterceptor('images'))
  async createTask(
    @Param('projectId') projectId: string,
    @UploadedFiles() files: Express.Multer.File[],
    @Body() body: any,
    @Req() req: Request,
    @Res() res: Response
  ) {
    try {
      const token = this.extractToken(req);
      const options = body.options ? JSON.parse(body.options) : [];
      const task = await this.webodmService.createTask(parseInt(projectId), files, options, token);
      res.json(task);
    } catch (error) {
      console.error('タスク作成エラー:', error);
      const status = (error as any).status || 500;
      res.status(status).json({ error: error.message });
    }
  }

  // タスク詳細の取得
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

  // 管理者: ユーザー一覧取得
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

  // 管理者: ユーザー新規作成
  @Post('admin/users')
  async createAdminUser(@Body() body: any, @Req() req: Request, @Res() res: Response) {
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

  // 管理者: ユーザー詳細取得
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
  @Put('admin/users/:id')
  async updateAdminUser(@Param('id') id: string, @Body() body: any, @Req() req: Request, @Res() res: Response) {
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
  @Post('signup')
  async signup(@Body() body: {
    username: string;
    password: string;
    email?: string;
    first_name?: string;
    last_name?: string;
  }, @Req() req: Request, @Res() res: Response) {
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