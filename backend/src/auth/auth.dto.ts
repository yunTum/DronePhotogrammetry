import { ApiProperty } from '@nestjs/swagger';

export class LoginDto {
  @ApiProperty({ 
    description: 'ユーザー名',
    example: 'admin'
  })
  username: string;

  @ApiProperty({ 
    description: 'パスワード',
    example: 'adminpassword'
  })
  password: string;
}

export class LogoutDto {
  @ApiProperty({ 
    description: 'JWTトークン',
    example: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  })
  token: string;
}

export class LoginResponseDto {
  @ApiProperty({ 
    description: 'JWTトークン',
    example: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  })
  token: string;

  @ApiProperty({ 
    description: 'ユーザー情報',
    example: {
      id: 1,
      username: 'admin',
      isAdmin: true
    }
  })
  user: {
    id: number;
    username: string;
    isAdmin: boolean;
  };
}

export class LogoutResponseDto {
  @ApiProperty({ 
    description: 'メッセージ',
    example: 'ログアウトしました'
  })
  message: string;
} 