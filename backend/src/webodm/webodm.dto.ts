import { ApiProperty } from '@nestjs/swagger';

export class CreateProjectDto {
  @ApiProperty({ 
    description: 'プロジェクト名',
    example: 'My Drone Project'
  })
  name: string;
}

export class CreateTaskDto {
  @ApiProperty({ 
    description: 'WebODM処理オプション（JSON配列またはカンマ区切り文字列）',
    required: false,
    example: '["fast-orthophoto", "dtm"] または "fast-orthophoto,dtm"'
  })
  options?: string;

  @ApiProperty({ 
    type: 'array',
    items: {
      type: 'string',
      format: 'binary',
    },
    description: 'ドローン写真ファイル（最低2枚必要）',
    required: true
  })
  images?: any[];
}

export class CreateAdminUserDto {
  @ApiProperty({ 
    description: 'ユーザー名',
    example: 'newuser'
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
    example: 'user@example.com'
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
}

export class UpdateAdminUserDto {
  @ApiProperty({ 
    description: 'ユーザー名',
    required: false,
    example: 'updateduser'
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
    example: 'user@example.com'
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
}

export class SignupDto {
  @ApiProperty({ 
    description: 'ユーザー名',
    example: 'newuser'
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
    example: 'user@example.com'
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
}

export class ProjectResponseDto {
  @ApiProperty({ example: 1 })
  id: number;

  @ApiProperty({ example: 'My Drone Project' })
  name: string;

  @ApiProperty({ example: 1 })
  user_id: number;

  @ApiProperty()
  created_at: string;

  @ApiProperty()
  updated_at: string;
}

export class TaskResponseDto {
  @ApiProperty({ example: 'task-uuid-123' })
  id: string;

  @ApiProperty({ example: 'My Task' })
  name: string;

  @ApiProperty({ example: 20 })
  status: number;

  @ApiProperty()
  created_at: string;

  @ApiProperty()
  updated_at: string;
}

export class UserResponseDto {
  @ApiProperty({ example: 1 })
  id: number;

  @ApiProperty({ example: 'username' })
  username: string;

  @ApiProperty({ example: 'user@example.com' })
  email: string;

  @ApiProperty({ example: 'John' })
  first_name: string;

  @ApiProperty({ example: 'Doe' })
  last_name: string;
} 