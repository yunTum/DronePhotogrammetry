import { Module } from '@nestjs/common';
import { WebodmController } from './webodm.controller';
import { WebodmService } from './webodm.service';
import { UserService } from '../user.service';

@Module({
  controllers: [WebodmController],
  providers: [WebodmService, UserService],
  exports: [WebodmService]
})
export class WebodmModule {} 