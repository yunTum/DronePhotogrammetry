import { ApiProperty } from '@nestjs/swagger';

export class CreateUserDto {
  @ApiProperty({ 
    description: 'ユーザー名',
    example: 'john_doe'
  })
  username: string;

  @ApiProperty({ 
    description: 'パスワード',
    example: 'password123'
  })
  password: string;

  @ApiProperty({ 
    description: 'メールアドレス',
    required: false,
    example: 'john@example.com'
  })
  email?: string;

  @ApiProperty({ 
    description: '名',
    required: false,
    example: 'John'
  })
  first_name?: string;

  @ApiProperty({ 
    description: '姓',
    required: false,
    example: 'Doe'
  })
  last_name?: string;

  @ApiProperty({ 
    description: '管理者フラグ',
    required: false,
    default: false,
    example: false
  })
  isAdmin?: boolean;

  @ApiProperty({ 
    description: 'WebODMユーザーID',
    required: false,
    example: 123
  })
  webodm_user_id?: number;
}

export class UpdateUserDto {
  @ApiProperty({ 
    description: 'ユーザー名',
    required: false,
    example: 'john_doe'
  })
  username?: string;

  @ApiProperty({ 
    description: 'パスワード',
    required: false,
    example: 'newpassword123'
  })
  password?: string;

  @ApiProperty({ 
    description: 'メールアドレス',
    required: false,
    example: 'john@example.com'
  })
  email?: string;

  @ApiProperty({ 
    description: '名',
    required: false,
    example: 'John'
  })
  first_name?: string;

  @ApiProperty({ 
    description: '姓',
    required: false,
    example: 'Doe'
  })
  last_name?: string;

  @ApiProperty({ 
    description: '管理者フラグ',
    required: false,
    example: false
  })
  isAdmin?: boolean;

  @ApiProperty({ 
    description: 'WebODMユーザーID',
    required: false,
    example: 123
  })
  webodm_user_id?: number;
}

export class UserResponseDto {
  @ApiProperty({ example: 1 })
  id: number;

  @ApiProperty({ example: 'john_doe' })
  username: string;

  @ApiProperty({ example: 'john@example.com' })
  email: string;

  @ApiProperty({ example: 'John' })
  first_name: string;

  @ApiProperty({ example: 'Doe' })
  last_name: string;

  @ApiProperty({ example: false })
  isAdmin: boolean;

  @ApiProperty({ example: 123 })
  webodm_user_id: number;

  @ApiProperty()
  created_at: Date;

  @ApiProperty()
  updated_at: Date;
} 