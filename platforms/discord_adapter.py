from typing import Optional
from platforms.base_platform import ChatPlatform
from config import Config


class DiscordAdapter(ChatPlatform):
    """디스코드 봇 어댑터"""
    
    def __init__(self, token: Optional[str] = None):
        super().__init__()
        self.token = token or Config.DISCORD_TOKEN
        self.command_prefix = Config.DISCORD_COMMAND_PREFIX
        self.is_running = False
        self.client = None
    
    def send_message(self, user_id: str, message: str) -> bool:
        """디스코드 메시지 전송"""
        if not self.is_running:
            print(f"[디스코드] 메시지 전송 실패: 플랫폼이 실행 중이 아닙니다.")
            return False
        
        # 실제 디스코드 API 호출 로직
        # 여기서는 시뮬레이션으로 출력만 함
        print(f"[디스코드 → {user_id}] {message}")
        
        # 실제 구현 예시 (discord.py 사용):
        # if self.client:
        #     user = self.client.get_user(int(user_id))
        #     if user:
        #         await user.send(message)
        #         return True
        
        return True
    
    def start(self) -> None:
        """디스코드 봇 시작"""
        if self.is_running:
            print("[디스코드] 이미 실행 중입니다.")
            return
        
        self.is_running = True
        print("[디스코드] 봇이 시작되었습니다.")
        
        # 실제 구현 예시:
        # import discord
        # from discord.ext import commands
        # 
        # intents = discord.Intents.default()
        # intents.message_content = True
        # self.client = commands.Bot(command_prefix='!', intents=intents)
        # 
        # @self.client.event
        # async def on_message(message):
        #     if message.author == self.client.user:
        #         return
        #     if self.message_handler:
        #         response = self.message_handler(str(message.author.id), message.content)
        #         if response:
        #             await message.channel.send(response)
        # 
        # self.client.run(self.token)
    
    def stop(self) -> None:
        """디스코드 봇 종료"""
        if not self.is_running:
            return
        
        self.is_running = False
        print("[디스코드] 봇이 종료되었습니다.")
        
        # if self.client:
        #     await self.client.close()
    
    def simulate_message(self, user_id: str, message: str) -> None:
        """테스트용 메시지 시뮬레이션"""
        if self.message_handler:
            response = self.message_handler(user_id, message)
            if response:
                self.send_message(user_id, response)

