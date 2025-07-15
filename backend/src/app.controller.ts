import { Controller, Get, Post, UploadedFile, UseInterceptors, Res, Param } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { Response } from 'express';
import { AppService } from './app.service';
import { WebodmService } from './webodm/webodm.service';
import { convertZipToGlb } from './common/zip-to-gltf';

@Controller()
export class AppController {
  constructor(
    private readonly appService: AppService,
    private readonly webodmService: WebodmService
  ) {}

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }

  @Post('convert')
  @UseInterceptors(FileInterceptor('file'))
  async convertZipToGltfApi(
    @UploadedFile() file: Express.Multer.File,
    @Res() res: Response,
  ) {
    try {
      console.log(`変換開始: ファイルサイズ=${file.size} bytes`);
      
      // ファイルサイズチェック（500MB制限）
      const maxSize = 500 * 1024 * 1024; // 500MB
      if (file.size > maxSize) {
        return res.status(400).json({ 
          error: `ファイルサイズが大きすぎます。最大${maxSize / (1024 * 1024)}MBまで対応しています。` 
        });
      }
      
      // タイムアウトを無効化（長時間処理のため）
      res.setTimeout(0);
      
      // zip→GLB変換
      const glbBuffer = await convertZipToGlb(file.buffer);
      
      console.log(`変換完了: GLBサイズ=${glbBuffer.length} bytes`);
      
      // GLBファイルを送信
      res.setHeader('Content-Type', 'application/octet-stream');
      res.setHeader('Content-Disposition', 'attachment; filename="result.glb"');
      res.setHeader('Content-Length', glbBuffer.length.toString());
      res.send(glbBuffer);
    } catch (error) {
      console.error('変換エラー:', error);
      res.status(400).json({ error: error.message });
    }
  }

  @Get('convert-zip/:projectId/:taskId')
  async convertZipToGlbFromWebodm(
    @Param('projectId') projectId: string,
    @Param('taskId') taskId: string,
    @Res() res: Response,
  ) {
    try {
      console.log(`WebODMからZIP変換開始: projectId=${projectId}, taskId=${taskId}`);
      
      // 認証トークンを取得（ヘッダーから）
      const authHeader = res.req.headers.authorization;
      if (!authHeader) {
        return res.status(401).json({ error: '認証トークンが必要です' });
      }

      // JWTトークンを抽出
      const token = authHeader.startsWith('JWT ') ? authHeader.substring(4) : null;

      // WebODMからZIPファイルを取得
      const zipBuffer = await this.webodmService.downloadFile(
        parseInt(projectId), 
        taskId, 
        'textured_model.zip', 
        token
      );
      
      console.log(`ZIPファイル取得完了: ${zipBuffer.length} bytes`);
      
      // zip→GLB変換
      const glbBuffer = await convertZipToGlb(zipBuffer);
      
      console.log(`GLB変換完了: ${glbBuffer.length} bytes`);
      
      // GLBファイルを送信
      res.setHeader('Content-Type', 'application/octet-stream');
      res.setHeader('Content-Disposition', 'attachment; filename="model.glb"');
      res.setHeader('Content-Length', glbBuffer.length.toString());
      res.send(glbBuffer);
    } catch (error) {
      console.error('WebODM変換エラー:', error);
      res.status(500).json({ error: error.message });
    }
  }
}
