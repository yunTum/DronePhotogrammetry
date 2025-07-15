import { Controller, Post, Body, Res, HttpStatus } from '@nestjs/common';
import { Response } from 'express';
import { AuthService } from './auth.service';

interface LoginRequest {
  username: string;
  password: string;
}

interface LogoutRequest {
  token: string;
}

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('login')
  async login(@Body() loginRequest: LoginRequest, @Res() res: Response) {
    try {
      const result = await this.authService.login(loginRequest.username, loginRequest.password);
      res.status(HttpStatus.OK).json(result);
      console.log('ログイン成功:', result);
    } catch (error) {
      console.error('ログインエラー:', error);
      res.status(HttpStatus.UNAUTHORIZED).json({ 
        error: 'ログインに失敗しました。ユーザー名とパスワードを確認してください。' 
      });
    }
  }

  @Post('logout')
  async logout(@Body() logoutRequest: LogoutRequest, @Res() res: Response) {
    try {
      await this.authService.logout(logoutRequest.token);
      res.status(HttpStatus.OK).json({ message: 'ログアウトしました' });
    } catch (error) {
      console.error('ログアウトエラー:', error);
      res.status(HttpStatus.INTERNAL_SERVER_ERROR).json({ 
        error: 'ログアウトに失敗しました' 
      });
    }
  }
} 