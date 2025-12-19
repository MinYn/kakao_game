from typing import Callable, Optional
import asyncio
import os
import time
import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from platforms.base_platform import ChatPlatform
from config import Config
from image_generator import ImageGenerator
from space_badges import SpaceBadgeService, generate_svg
from events.platform_queue import PlatformMessage, PlatformMessageQueue


class HuntMenuView(View):
    """사냥 메뉴 뷰 (일반몹/특수몹/보스몹 선택)"""
    
    def __init__(self, message_handler, user_id: str, engine=None, adapter=None, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.message_handler = message_handler
        self.user_id = user_id
        self.engine = engine
        self.adapter = adapter
        
        # Select Menu 생성
        select = Select(
            placeholder="사냥할 몬스터를 선택하세요",
            options=[
                discord.SelectOption(label="일반몹", value="일반몹", emoji="🟢", description="기본 보상: 20~50G"),
                discord.SelectOption(label="특수몹", value="특수몹", emoji="🟡", description="보상: 80~150G, 입장권 드랍 가능"),
                discord.SelectOption(label="보스몹", value="보스몹", emoji="🔴", description="보상: 200~350G, 입장권 필요"),
            ]
        )
        select.callback = self._on_select
        self.add_item(select)
    
    async def on_timeout(self):
        """타임아웃 시 정리"""
        try:
            # View 정리
            for item in self.children:
                item.disabled = True
        except:
            pass
    
    async def _on_select(self, interaction: discord.Interaction):
        """Select Menu 선택 콜백"""
        try:
            # 즉시 응답 (타임아웃 방지)
            await interaction.response.defer(ephemeral=False)

            selected = interaction.data['values'][0]  # 선택된 값
            if self.adapter:
                queued, duplicate = self.adapter._enqueue_incoming(self.user_id, selected)
                if queued:
                    await self.adapter._acknowledge_interaction(interaction, duplicate=duplicate)
                    return
            if self.message_handler:
                response = self.message_handler(self.user_id, selected)
                if response:
                    # 이미지 생성 (사냥 결과인 경우)
                    image_path = None
                    if hasattr(self, 'adapter') and self.adapter:
                        image_path = self.adapter._generate_image_if_needed(self.user_id, selected, response)

                    await self.adapter._send_interaction_message(
                        interaction=interaction,
                        response=response,
                        view=self._create_view_for_response(selected, response),
                        image_path=image_path,
                        user_id=self.user_id,
                    )
                else:
                    await interaction.followup.send("처리되었습니다.", ephemeral=True)
            else:
                await interaction.followup.send("처리 중 오류가 발생했습니다.", ephemeral=True)
        except Exception as e:
            print(f"[디스코드] Select Menu 오류: {e}")
            import traceback
            traceback.print_exc()
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("처리 중 오류가 발생했습니다.", ephemeral=True)
                else:
                    await interaction.followup.send("처리 중 오류가 발생했습니다.", ephemeral=True)
            except:
                pass
    
    def _create_view_for_response(self, command: Optional[str], response: str):
        """응답에 따라 적절한 버튼 뷰 생성"""
        if not self.message_handler:
            return None

        if self.adapter:
            buttons = self.adapter._get_button_definitions(self.user_id, command, response)
        elif self.engine:
            buttons = self.engine.get_ui_buttons(self.user_id, command, response)
        else:
            # 기본 버튼 (engine이 없는 경우)
            buttons = [
                {'label': '💰 골드', 'messageText': '골드'},
                {'label': '🏆 랭킹', 'messageText': '리더보드'},
                {'label': '❓ 도움말', 'messageText': '도움말'},
            ]

        return CommandButtonView(
            buttons,
            self.message_handler,
            self.user_id,
            self.engine,
            self.adapter,
            last_command=command,
        )


class CommandButtonView(View):
    """명령어 버튼 뷰"""

    def __init__(
        self,
        buttons: list,
        message_handler,
        user_id: str,
        engine=None,
        adapter=None,
        last_command: Optional[str] = None,
        timeout: float = 300.0,
    ):
        super().__init__(timeout=timeout)
        self.message_handler = message_handler
        self.user_id = user_id
        self.engine = engine
        self.adapter = adapter
        self.last_command = last_command
        
        # 버튼 생성 (최대 5개)
        for btn_data in buttons[:5]:
            label = btn_data.get('label', btn_data.get('messageText', '버튼'))
            message_text = btn_data.get('messageText', label)
            
            # "사냥" 버튼은 특별 처리
            if message_text == '사냥':
                button = Button(
                    label="사냥",
                    style=discord.ButtonStyle.primary,
                    emoji="🗡️"
                )
                button.callback = self._create_hunt_callback()
            else:
                # 이모지와 텍스트 분리
                parts = label.split(' ', 1)
                if len(parts) == 2 and len(parts[0]) <= 2:  # 이모지가 있는 경우
                    emoji_str = parts[0]
                    text_label = parts[1]
                    button = Button(
                        label=text_label[:80],
                        style=discord.ButtonStyle.primary,
                        emoji=emoji_str
                    )
                else:
                    # 이모지가 없거나 인식 불가능한 경우
                    clean_label = label.split(' ', 1)[-1] if ' ' in label else label
                    button = Button(
                        label=clean_label[:80],
                        style=discord.ButtonStyle.primary
                    )
                button.callback = self._create_callback(message_text)
            
            self.add_item(button)
    
    async def on_timeout(self):
        """타임아웃 시 정리"""
        try:
            # View 정리
            for item in self.children:
                item.disabled = True
        except:
            pass
    
    def _create_hunt_callback(self):
        """사냥 버튼 클릭 콜백 (서브 메뉴 표시)"""
        async def callback(interaction: discord.Interaction):
            # 사냥 메뉴 뷰 생성
            adapter = None
            if hasattr(self, 'adapter'):
                adapter = self.adapter
            hunt_view = HuntMenuView(self.message_handler, self.user_id, self.engine, adapter)
            await interaction.response.send_message(
                "🗡️ 사냥할 몬스터를 선택하세요:",
                view=hunt_view,
                ephemeral=False
            )
        
        return callback
    
    def _create_callback(self, command: str):
        """버튼 클릭 콜백 생성"""
        async def callback(interaction: discord.Interaction):
            try:
                # 즉시 응답 (타임아웃 방지)
                await interaction.response.defer(ephemeral=False)

                if hasattr(self, 'adapter') and self.adapter:
                    queued, duplicate = self.adapter._enqueue_incoming(self.user_id, command)
                    if queued:
                        await self.adapter._acknowledge_interaction(interaction, duplicate=duplicate)
                        return

                if self.message_handler:
                    response = self.message_handler(self.user_id, command)
                    if response:
                        # 응답에 따라 새로운 버튼 생성
                        view = self._create_view_for_response(command, response)
                        image_path = None
                        if self.adapter:
                            image_path = self.adapter._generate_image_if_needed(self.user_id, command, response)

                        await self.adapter._send_interaction_message(
                            interaction=interaction,
                            response=response,
                            view=view,
                            image_path=image_path,
                            user_id=self.user_id,
                        )
                    else:
                        await interaction.followup.send("처리되었습니다.", ephemeral=True)
                else:
                    await interaction.followup.send("처리 중 오류가 발생했습니다.", ephemeral=True)
            except Exception as e:
                print(f"[디스코드] 버튼 클릭 오류: {e}")
                import traceback
                traceback.print_exc()
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message("처리 중 오류가 발생했습니다.", ephemeral=True)
                    else:
                        await interaction.followup.send("처리 중 오류가 발생했습니다.", ephemeral=True)
                except:
                    pass
        
        return callback
    
    def _create_view_for_response(self, command: Optional[str], response: str):
        """응답에 따라 적절한 버튼 뷰 생성"""
        if self.adapter:
            buttons = self.adapter._get_button_definitions(self.user_id, command, response)
        elif self.engine:
            buttons = self.engine.get_ui_buttons(self.user_id, command, response)
        else:
            # 기본 버튼 (engine이 없는 경우)
            buttons = [
                {'label': '💰 골드', 'messageText': '골드'},
                {'label': '🏆 랭킹', 'messageText': '리더보드'},
                {'label': '❓ 도움말', 'messageText': '도움말'},
            ]

        return CommandButtonView(
            buttons,
            self.message_handler,
            self.user_id,
            self.engine,
            self.adapter,
            last_command=command,
        )


class DiscordAdapter(ChatPlatform):
    """디스코드 봇 어댑터"""
    
    def __init__(self, token: Optional[str] = None, engine=None, message_queue: Optional[PlatformMessageQueue] = None):
        super().__init__()
        self.token = token or Config.DISCORD_TOKEN
        self.command_prefix = Config.DISCORD_COMMAND_PREFIX
        self.is_running = False
        self.client = None
        self.loop = None
        self.bot_thread = None
        self.engine = engine  # GameEngine 참조
        self.image_generator = ImageGenerator()  # 이미지 생성기
        self.message_queue = message_queue
        self._queue_listener_started = False
        self._pending_actions: dict[str, float] = {}

        self.message_handler: Optional[Callable[[str, str], str]] = None

        # 메시지 전송을 위한 채널/유저 매핑
        self.user_channels = {}  # user_id -> (channel, last_channel) 매핑

    def set_message_queue(self, queue: PlatformMessageQueue) -> None:
        self.message_queue = queue

    def _enqueue_incoming(self, user_id: str, content: str) -> tuple[bool, bool]:
        """Kafka/큐에 수신 메시지를 적재하며 중복 액션을 표시"""
        now = time.monotonic()
        duplicate = False
        last_ts = self._pending_actions.get(user_id)
        if last_ts and now - last_ts < 2.0:
            duplicate = True

        # 중복 요청은 큐 적재 없이 처리 차단
        if duplicate:
            self._pending_actions[user_id] = now
            return True, True

        self._pending_actions[user_id] = now

        if self.message_queue:
            self.message_queue.publish_incoming(
                PlatformMessage(platform="discord", user_id=user_id, content=content)
            )
            return True, False
        return False, False

    def _clear_pending_action(self, user_id: str) -> None:
        self._pending_actions.pop(user_id, None)

    def _handle_outgoing_message(self, message: PlatformMessage) -> None:
        if message.platform and message.platform != "discord":
            return
        self.send_message(message.user_id, message.content)

    async def _acknowledge_interaction(self, interaction: discord.Interaction, duplicate: bool = False) -> None:
        if not duplicate:
            return
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "요청을 접수했어요. 처리 후 답변을 보내드릴게요.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "요청을 접수했어요. 처리 후 답변을 보내드릴게요.",
                    ephemeral=True,
                )
        except Exception:
            pass

    async def _acknowledge_channel(self, channel: discord.abc.Messageable, duplicate: bool = False) -> None:
        if not duplicate:
            return
        try:
            await channel.send("요청을 접수했어요. 처리 후 답변을 보내드릴게요.")
        except Exception:
            pass
    
    def send_message(self, user_id: str, message: str) -> bool:
        """디스코드 메시지 전송"""
        if not self.is_running or not self.client:
            print(f"[디스코드] 메시지 전송 실패: 플랫폼이 실행 중이 아닙니다.")
            return False
        
        # 비동기 함수를 동기적으로 실행
        try:
            if self.loop and self.loop.is_running():
                # 이미 실행 중인 루프가 있으면 태스크로 추가
                asyncio.run_coroutine_threadsafe(
                    self._send_message_async(user_id, message),
                    self.loop
                )
            else:
                # 루프가 없으면 새로 생성해서 실행
                asyncio.run(self._send_message_async(user_id, message))
            return True
        except Exception as e:
            print(f"[디스코드] 메시지 전송 오류: {e}")
            return False
    
    async def _send_message_async(
        self,
        user_id: str,
        message: str,
        image_path: Optional[str] = None,
        last_command: Optional[str] = None,
    ) -> None:
        """비동기 메시지 전송"""
        try:
            # 버튼 뷰는 실행 중인 이벤트 루프 내에서 생성해야 함
            view = self._create_button_view(user_id, message, last_command)
            files = self._build_files(image_path)
            
            # 마지막으로 메시지를 보낸 채널이 있으면 그 채널에 전송
            if user_id in self.user_channels:
                channel, _ = self.user_channels[user_id]
                if channel:
                    await channel.send(message, view=view, files=files or None)
                    self._cleanup_temp_image(image_path)
                    return
            
            # 채널이 없으면 DM으로 전송 시도
            user = self.client.get_user(int(user_id))
            if user:
                await user.send(message, view=view, files=files or None)
                self._cleanup_temp_image(image_path)
        except discord.Forbidden:
            print(f"[디스코드] 메시지 전송 권한 없음: {user_id}")
        except Exception as e:
            print(f"[디스코드] 메시지 전송 오류: {e}")
            self._cleanup_temp_image(image_path)
        finally:
            self._clear_pending_action(user_id)
            self._cleanup_temp_image(image_path)
    
    def _create_button_view(
        self, user_id: str, response: str, last_command: Optional[str] = None
    ) -> Optional[View]:
        """응답에 따라 버튼 뷰 생성"""
        if not self.message_handler:
            return None

        buttons = self._get_button_definitions(user_id, last_command, response)
        return CommandButtonView(
            buttons,
            self.message_handler,
            user_id,
            self.engine,
            self,
            last_command=last_command,
        )

    def _get_button_definitions(
        self, user_id: str, command: Optional[str], response: Optional[str]
    ) -> list:
        if self.engine:
            return self.engine.get_ui_buttons(user_id, command, response)
        return [
            {'label': '🔨 강화', 'messageText': '강화'},
            {'label': '📊 상태', 'messageText': '상태'},
            {'label': '🛰️ 정찰', 'messageText': '정찰'},
            {'label': '🧭 탐사', 'messageText': '탐사'},
            {'label': '🚨 구조', 'messageText': '구조'},
        ]
    
    def _generate_image_if_needed(self, user_id: str, command: str, response: str) -> Optional[str]:
        """강화/사냥 결과인 경우 이미지 생성"""
        if not self.engine:
            return None
        
        try:
            if "우주 탐험 로그를 시작합니다!" in response:
                return self._generate_space_badge_image(user_id)

            if self._should_attach_badge(command, response):
                return self._generate_space_badge_image(user_id)

            # 이미지 생성 필요 여부 확인
            if not self.engine.should_generate_image(user_id, command, response):
                return None
            
            # 강화 결과 이미지 생성
            if '강화 성공' in response or '강화 실패' in response:
                image_data = self.engine.get_enhancement_image_data(user_id, response)
                if image_data:
                    return self.image_generator.generate_enhancement_image(
                        level=image_data['level'],
                        max_level=image_data['max_level'],
                        is_success=image_data['is_success'],
                        previous_level=image_data['previous_level'],
                        gold=image_data['gold'],
                        next_cost=image_data.get('next_cost', 0),
                        next_success_rate=image_data.get('next_success_rate', 0),
                        attempts=image_data.get('attempts', 0),
                        successes=image_data.get('successes', 0),
                        failures=image_data.get('failures', 0)
                    )
            
            # 사냥 결과 이미지 생성
            if '사냥 성공' in response or '사냥 실패' in response:
                image_data = self.engine.get_hunt_image_data(user_id, command, response)
                if image_data:
                    return self.image_generator.generate_hunt_image(
                        monster_name=image_data['monster_name'],
                        monster_type=image_data['monster_type'],
                        reward=image_data['reward'],
                        is_success=image_data['is_success'],
                        level=image_data['level'],
                        gold=image_data['gold']
                    )
        except Exception as e:
            print(f"[디스코드] 이미지 생성 오류: {e}")
            import traceback
            traceback.print_exc()

        return None

    def _should_attach_badge(self, command: str, response: str) -> bool:
        normalized = (command or "").strip().lower()
        if normalized in {"강화", "성장", "train", "업그레이드", "상태", "status", "info"}:
            return True

        if "현재 우주선 강화 레벨" in response or "콜사인" in response:
            return True

        return False

    def _generate_space_badge_image(self, user_id: str) -> Optional[str]:
        try:
            service = SpaceBadgeService()
            variant = service.get_variant_for_user(user_id)
            variant_index = service.find_variant_index(variant)
            svg_code = generate_svg(variant, variant_index, star_seed=service.stable_seed(user_id))
            return self.image_generator.generate_svg_image(svg_code, filename_prefix="space_badge")
        except Exception as e:
            print(f"[디스코드] 배지 이미지 생성 오류: {e}")
            return None

    async def _send_interaction_message(
        self,
        interaction: discord.Interaction,
        response: str,
        view: Optional[View] = None,
        image_path: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        files = self._build_files(image_path)
        await interaction.followup.send(response, view=view, files=files or None, ephemeral=False)
        if user_id:
            self._clear_pending_action(user_id)
        self._cleanup_temp_image(image_path)

    def _build_files(self, image_path: Optional[str]):
        files = []
        if image_path and os.path.exists(image_path):
            files.append(discord.File(image_path, filename=os.path.basename(image_path)))
        return files

    def _cleanup_temp_image(self, image_path: Optional[str]) -> None:
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass
    
    def start(self, start_webhook: bool = False) -> None:
        """디스코드 봇 시작"""
        if self.is_running:
            print("[디스코드] 이미 실행 중입니다.")
            return
        
        if not self.token:
            print("⚠️ DISCORD_TOKEN이 설정되지 않았습니다.")
            print("💡 .env 파일에 DISCORD_TOKEN을 설정하세요.")
            return
        
        # 비동기 봇 실행을 별도 스레드에서 처리
        import threading
        
        def run_bot():
            asyncio.set_event_loop(asyncio.new_event_loop())
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self._start_bot())
        
        self.bot_thread = threading.Thread(target=run_bot, daemon=True)
        self.bot_thread.start()
    
    async def _start_bot(self):
        """비동기 봇 시작"""
        intents = discord.Intents.default()
        intents.message_content = True
        # intents.members는 privileged intent이므로 필요시 Developer Portal에서 활성화 필요
        # 이 봇은 멤버 정보가 필요 없으므로 제거
        
        self.client = commands.Bot(
            command_prefix=self.command_prefix,
            intents=intents
        )
        
        @self.client.event
        async def on_ready():
            self.is_running = True
            print(f"[디스코드] 봇이 로그인했습니다: {self.client.user}")
            print(f"[디스코드] 서버 수: {len(self.client.guilds)}")
            print(f"[디스코드] 명령어 접두사: {self.command_prefix}")
            if self.message_queue and not self._queue_listener_started:
                self.message_queue.start_outgoing_consumer(
                    self._handle_outgoing_message,
                    group_id=f"{Config.KAFKA_PLATFORM_GROUP}-discord",
                )
                self._queue_listener_started = True
        
        @self.client.event
        async def on_message(message):
            # 봇 자신의 메시지는 무시
            if message.author == self.client.user:
                return
            
            # DM인 경우
            if isinstance(message.channel, discord.DMChannel):
                user_id = str(message.author.id)
                if self.message_handler:
                    # 플랫폼 어댑터 설정 (멘션 기능용)
                    if self.engine:
                        self.engine.set_platform_adapter(self)
                    queued, duplicate = self._enqueue_incoming(user_id, message.content)
                    if queued:
                        self.user_channels[user_id] = (message.channel, message.channel)
                        await self._acknowledge_channel(message.channel, duplicate=duplicate)
                        return
                    response = self.message_handler(user_id, message.content)
                    if response:
                        # DM 채널 저장
                        self.user_channels[user_id] = (message.channel, message.channel)
                        # 버튼 뷰 생성
                        view = self._create_button_view(user_id, response, message.content)
                        # 이미지 생성 (강화/사냥 결과인 경우)
                        image_path = self._generate_image_if_needed(user_id, message.content, response)
                        await message.channel.send(response, view=view, files=[discord.File(image_path)] if image_path and os.path.exists(image_path) else None)
                        # 이미지 파일 정리
                        if image_path and os.path.exists(image_path):
                            try:
                                os.remove(image_path)
                            except:
                                pass
            # 서버 채널인 경우
            else:
                user_id = str(message.author.id)
                # 명령어 접두사로 시작하는 경우만 처리
                if message.content.startswith(self.command_prefix):
                    if self.message_handler:
                        # 접두사 제거
                        content = message.content[len(self.command_prefix):].strip()
                        # 플랫폼 어댑터 설정 (멘션 기능용)
                        if self.engine:
                            self.engine.set_platform_adapter(self)
                        queued, duplicate = self._enqueue_incoming(user_id, content)
                        if queued:
                            self.user_channels[user_id] = (message.channel, message.channel)
                            await self._acknowledge_channel(message.channel, duplicate=duplicate)
                            return
                        response = self.message_handler(user_id, content)
                        if response:
                            # 채널 저장
                            self.user_channels[user_id] = (message.channel, message.channel)
                            # 버튼 뷰 생성
                            view = self._create_button_view(user_id, response, content)
                            # 이미지 생성 (강화/사냥 결과인 경우)
                            image_path = self._generate_image_if_needed(user_id, content, response)
                            await message.channel.send(response, view=view, files=[discord.File(image_path)] if image_path and os.path.exists(image_path) else None)
                            # 이미지 파일 정리
                            if image_path and os.path.exists(image_path):
                                try:
                                    os.remove(image_path)
                                except:
                                    pass
                # 접두사 없이도 처리하려면 주석 해제
                # else:
                #     if self.message_handler:
                #         response = self.message_handler(user_id, message.content)
                #         if response:
                #             self.user_channels[user_id] = (message.channel, message.channel)
                #             await message.channel.send(response)
            
            # 명령어 처리 (commands.Bot이므로 필요)
            await self.client.process_commands(message)
        
        try:
            await self.client.start(self.token)
        except discord.LoginFailure:
            print("⚠️ 디스코드 토큰이 유효하지 않습니다.")
            print("💡 Discord Developer Portal에서 올바른 토큰을 확인하세요.")
        except Exception as e:
            print(f"⚠️ 디스코드 봇 실행 오류: {e}")
    
    async def _cleanup_views(self):
        """모든 활성 View 정리"""
        try:
            # discord.py는 View를 자동으로 관리하므로 명시적 정리 불필요
            # _views 속성은 내부 구현이므로 접근하지 않음
            pass
        except Exception as e:
            print(f"[디스코드] View 정리 오류: {e}")
    
    def stop(self) -> None:
        """디스코드 봇 종료"""
        if not self.is_running:
            return
        
        self.is_running = False
        print("[디스코드] 봇을 종료합니다...")
        
        # 데이터베이스 저장 (GameEngine을 통해)
        if self.engine:
            try:
                print("[디스코드] 게임 데이터 저장 중...")
                # 모든 활성 게임 종료 및 데이터 저장
                if hasattr(self.engine, 'point_system') and self.engine.point_system:
                    # 데이터베이스 연결은 자동으로 커밋되므로 명시적 저장 불필요
                    pass
            except Exception as e:
                print(f"[디스코드] 데이터 저장 오류: {e}")
        
        if self.client and self.loop:
            try:
                # 봇 종료
                if self.loop.is_running():
                    # 비동기 종료 (타임아웃 설정)
                    future = asyncio.run_coroutine_threadsafe(
                        self._safe_close(),
                        self.loop
                    )
                    # 최대 5초 대기
                    try:
                        future.result(timeout=5.0)
                    except asyncio.TimeoutError:
                        print("[디스코드] 종료 타임아웃, 강제 종료합니다...")
                    except Exception as e:
                        print(f"[디스코드] 종료 중 예외: {e}")
                else:
                    self.loop.run_until_complete(self._safe_close())
                
                # 루프 정리 (안전하게)
                if self.loop and not self.loop.is_closed():
                    try:
                        # 남은 태스크 취소 (현재 태스크 제외)
                        pending = [t for t in asyncio.all_tasks(self.loop) if not t.done()]
                        for task in pending:
                            if not task.cancelled():
                                task.cancel()
                        # 취소된 태스크 완료 대기 (짧은 타임아웃)
                        if pending:
                            try:
                                self.loop.run_until_complete(
                                    asyncio.wait_for(
                                        asyncio.gather(*pending, return_exceptions=True),
                                        timeout=1.0
                                    )
                                )
                            except (asyncio.TimeoutError, RuntimeError):
                                pass
                    except RuntimeError:
                        # 루프가 이미 닫혔거나 다른 스레드에서 실행 중
                        pass
            except Exception as e:
                print(f"[디스코드] 종료 오류: {e}")
        
        print("[디스코드] 봇이 종료되었습니다.")
    
    async def _safe_close(self):
        """안전한 봇 종료"""
        try:
            if self.client:
                # 모든 View 정리
                await self._cleanup_views()
                # 봇 종료
                await self.client.close()
                # HTTP 세션 명시적으로 닫기
                if hasattr(self.client, 'http') and self.client.http:
                    await self.client.http.close()
        except Exception as e:
            print(f"[디스코드] 안전 종료 오류: {e}")
    
    def simulate_message(self, user_id: str, message: str) -> None:
        """테스트용 메시지 시뮬레이션"""
        if self.message_handler:
            response = self.message_handler(user_id, message)
            if response:
                self.send_message(user_id, response)
    
    def mention_user(self, user_id: str, user_name: Optional[str] = None) -> str:
        """디스코드 사용자 멘션 문자열 생성
        
        Discord에서는 <@user_id> 형태로 멘션
        """
        return f"<@{user_id}>"
