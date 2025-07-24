import { Controller, Get, Post, Patch, Delete, Param, Body, Req, ForbiddenException } from '@nestjs/common';
import { ApiTags, ApiSecurity, ApiOperation, ApiParam, ApiBody, ApiResponse } from '@nestjs/swagger';
import { UserService } from './user.service';
import { CreateUserDto, UpdateUserDto, UserResponseDto } from './user.dto';

@ApiTags('users')
@ApiSecurity('JWT-auth')
@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  // 管理者のみユーザー一覧取得
  @ApiOperation({ summary: 'ユーザー一覧取得（管理者のみ）' })
  @ApiResponse({ 
    status: 200, 
    description: 'ユーザー一覧取得成功',
    type: [UserResponseDto]
  })
  @ApiResponse({ status: 403, description: '管理者権限が必要です' })
  @Get()
  async findAll(@Req() req) {
    if (!req.user?.isAdmin) throw new ForbiddenException('管理者権限が必要です');
    return this.userService.findAll();
  }

  // 管理者のみユーザー新規作成
  @ApiOperation({ summary: 'ユーザー新規作成（管理者のみ）' })
  @ApiBody({ type: CreateUserDto })
  @ApiResponse({ 
    status: 201, 
    description: 'ユーザー作成成功',
    type: UserResponseDto
  })
  @ApiResponse({ status: 403, description: '管理者権限が必要です' })
  @Post()
  async create(@Body() dto: CreateUserDto, @Req() req) {
    if (!req.user?.isAdmin) throw new ForbiddenException('管理者権限が必要です');
    return this.userService.create(dto);
  }

  // 管理者または本人のみ詳細取得
  @ApiOperation({ summary: 'ユーザー詳細取得（管理者または本人のみ）' })
  @ApiParam({ name: 'id', description: 'ユーザーID', type: String })
  @ApiResponse({ 
    status: 200, 
    description: 'ユーザー詳細取得成功',
    type: UserResponseDto
  })
  @ApiResponse({ status: 403, description: '権限がありません' })
  @ApiResponse({ status: 404, description: 'ユーザーが見つかりません' })
  @Get(':id')
  async findOne(@Param('id') id: string, @Req() req) {
    if (!req.user?.isAdmin && req.user?.id !== Number(id)) throw new ForbiddenException('権限がありません');
    return this.userService.findOne(Number(id));
  }

  // 管理者または本人のみ更新
  @ApiOperation({ summary: 'ユーザー情報更新（管理者または本人のみ）' })
  @ApiParam({ name: 'id', description: 'ユーザーID', type: String })
  @ApiBody({ type: UpdateUserDto })
  @ApiResponse({ 
    status: 200, 
    description: 'ユーザー更新成功',
    type: UserResponseDto
  })
  @ApiResponse({ status: 403, description: '権限がありません' })
  @ApiResponse({ status: 404, description: 'ユーザーが見つかりません' })
  @Patch(':id')
  async update(@Param('id') id: string, @Body() dto: UpdateUserDto, @Req() req) {
    if (!req.user?.isAdmin && req.user?.id !== Number(id)) throw new ForbiddenException('権限がありません');
    return this.userService.update(Number(id), dto);
  }

  // 管理者のみ削除
  @ApiOperation({ summary: 'ユーザー削除（管理者のみ）' })
  @ApiParam({ name: 'id', description: 'ユーザーID', type: String })
  @ApiResponse({ status: 200, description: 'ユーザー削除成功' })
  @ApiResponse({ status: 403, description: '管理者権限が必要です' })
  @ApiResponse({ status: 404, description: 'ユーザーが見つかりません' })
  @Delete(':id')
  async remove(@Param('id') id: string, @Req() req) {
    if (!req.user?.isAdmin) throw new ForbiddenException('管理者権限が必要です');
    return this.userService.remove(Number(id));
  }
} 