import { Controller, Post, Body, Res, HttpStatus } from '@nestjs/common';
import { Response } from 'express';
import { ApiTags, ApiOperation, ApiBody, ApiResponse } from '@nestjs/swagger';
import { AuthService } from './auth.service';
import { LoginDto, LogoutDto, LoginResponseDto, LogoutResponseDto } from './auth.dto';

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @ApiOperation({ summary: 'ユーザーログイン' })
  @ApiBody({ type: LoginDto })
  @ApiResponse({ 
    status: 200, 
    description: 'ログイン成功',
    type: LoginResponseDto
  })
  @ApiResponse({ status: 401, description: 'ログインに失敗しました' })
  @Post('login')
  async login(@Body() loginRequest: LoginDto, @Res() res: Response) {
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

  @ApiOperation({ summary: 'ユーザーログアウト' })
  @ApiBody({ type: LogoutDto })
  @ApiResponse({ 
    status: 200, 
    description: 'ログアウト成功',
    type: LogoutResponseDto
  })
  @ApiResponse({ status: 500, description: 'ログアウトに失敗しました' })
  @Post('logout')
  async logout(@Body() logoutRequest: LogoutDto, @Res() res: Response) {
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