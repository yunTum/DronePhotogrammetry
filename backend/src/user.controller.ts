import { Controller, Get, Post, Patch, Delete, Param, Body, Req, ForbiddenException } from '@nestjs/common';
import { UserService } from './user.service';

@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  // 管理者のみユーザー一覧取得
  @Get()
  async findAll(@Req() req) {
    if (!req.user?.isAdmin) throw new ForbiddenException('管理者権限が必要です');
    return this.userService.findAll();
  }

  // 管理者のみユーザー新規作成
  @Post()
  async create(@Body() dto: {
    username: string;
    password: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    isAdmin?: boolean;
    webodm_user_id?: number;
  }, @Req() req) {
    if (!req.user?.isAdmin) throw new ForbiddenException('管理者権限が必要です');
    return this.userService.create(dto);
  }

  // 管理者または本人のみ詳細取得
  @Get(':id')
  async findOne(@Param('id') id: string, @Req() req) {
    if (!req.user?.isAdmin && req.user?.id !== Number(id)) throw new ForbiddenException('権限がありません');
    return this.userService.findOne(Number(id));
  }

  // 管理者または本人のみ更新
  @Patch(':id')
  async update(@Param('id') id: string, @Body() dto: {
    username?: string;
    password?: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    isAdmin?: boolean;
    webodm_user_id?: number;
  }, @Req() req) {
    if (!req.user?.isAdmin && req.user?.id !== Number(id)) throw new ForbiddenException('権限がありません');
    return this.userService.update(Number(id), dto);
  }

  // 管理者のみ削除
  @Delete(':id')
  async remove(@Param('id') id: string, @Req() req) {
    if (!req.user?.isAdmin) throw new ForbiddenException('管理者権限が必要です');
    return this.userService.remove(Number(id));
  }
} 