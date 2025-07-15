import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcrypt';

const prisma = new PrismaClient();

@Injectable()
export class UserService {
  async findAll() {
    return prisma.user.findMany({
      select: {
        id: true,
        username: true,
        email: true,
        first_name: true,
        last_name: true,
        isAdmin: true,
        webodm_user_id: true,
        created_at: true,
        updated_at: true
        // passwordは除外
      }
    });
  }

  async create(dto: {
    username: string;
    password: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    isAdmin?: boolean;
    webodm_user_id?: number;
  }) {
    // パスワードをハッシュ化
    const hashedPassword = await bcrypt.hash(dto.password, 10);
    
    return prisma.user.create({
      data: {
        ...dto,
        password: hashedPassword
      },
      select: {
        id: true,
        username: true,
        email: true,
        first_name: true,
        last_name: true,
        isAdmin: true,
        webodm_user_id: true,
        created_at: true,
        updated_at: true
        // passwordは除外
      }
    });
  }

  async findOne(id: number) {
    const user = await prisma.user.findUnique({
      where: { id },
      select: {
        id: true,
        username: true,
        email: true,
        first_name: true,
        last_name: true,
        isAdmin: true,
        webodm_user_id: true,
        created_at: true,
        updated_at: true
        // passwordは除外
      }
    });
    if (!user) throw new NotFoundException('ユーザーが見つかりません');
    return user;
  }

  async findByUsername(username: string) {
    return prisma.user.findUnique({
      where: { username }
    });
  }

  async update(id: number, dto: {
    username?: string;
    password?: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    isAdmin?: boolean;
    webodm_user_id?: number;
  }) {
    const updateData: any = { ...dto };
    
    // パスワードが含まれている場合はハッシュ化
    if (dto.password) {
      updateData.password = await bcrypt.hash(dto.password, 10);
    }
    
    return prisma.user.update({
      where: { id },
      data: updateData,
      select: {
        id: true,
        username: true,
        email: true,
        first_name: true,
        last_name: true,
        isAdmin: true,
        webodm_user_id: true,
        created_at: true,
        updated_at: true
        // passwordは除外
      }
    });
  }

  async remove(id: number) {
    return prisma.user.delete({ where: { id } });
  }

  // パスワード検証
  async validatePassword(userId: number, password: string): Promise<boolean> {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { password: true }
    });
    if (!user) return false;
    return bcrypt.compare(password, user.password);
  }
} 