"""
카카오톡 챗봇 스킬 서버
카카오 챗봇 관리자센터 스킬 서버 형식에 맞춰 구현
참고: https://kakaobusiness.gitbook.io/main/tool/chatbot
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from platforms.kakao_adapter import KakaoAdapter
from game_engine import GameEngine
from config import Config
from models.database import init_db
from api import gold, boss_tickets, enhancement, stats
import uvicorn


class WebhookServer:
    """카카오 챗봇 관리자센터 스킬 서버 클래스"""
    
    def __init__(self, adapter: KakaoAdapter, engine: GameEngine):
        self.app = FastAPI(
            title="카카오 게임봇 웹훅 서버",
            description="게임봇 API 및 웹훅 서버",
            version="1.0.0"
        )
        self.adapter = adapter
        self.engine = engine
        
        # 데이터베이스 초기화
        init_db()
        
        # API 라우터 등록
        self.app.include_router(gold.router)
        self.app.include_router(boss_tickets.router)
        self.app.include_router(enhancement.router)
        self.app.include_router(stats.router)
        
        self._setup_routes()
    
    def _parse_user_request(self, data: Dict[str, Any]) -> tuple[str, str, Optional[str]]:
        """
        카카오 챗봇 관리자센터 스킬 서버 요청 파싱
        
        요청 형식:
        {
            "userRequest": {
                "user": {
                    "id": "user_id",
                    "properties": {
                        "nickname": "사용자명"
                    }
                },
                "utterance": "사용자 메시지"
            }
        }
        """
        user_request = data.get('userRequest', {})
        user = user_request.get('user', {})
        user_id = user.get('id', '')
        utterance = user_request.get('utterance', '')
        # 사용자 이름 추출 (카카오톡에서 제공하는 경우)
        user_properties = user.get('properties', {})
        user_name = user_properties.get('nickname') or user.get('nickname')
        
        return str(user_id), utterance, user_name
    
    def _get_default_quick_replies(self) -> list:
        """
        기본 Quick Replies 버튼 목록 생성
        
        카카오톡에서 봇 멘션(@봇이름) 시 표시될 커맨드 버튼들
        """
        return [
            {
                'action': 'message',
                'label': '💰 골드',
                'messageText': '골드'
            },
            {
                'action': 'message',
                'label': '🎮 게임시작',
                'messageText': '게임시작 모험'
            },
            {
                'action': 'message',
                'label': '🏆 랭킹',
                'messageText': '리더보드'
            },
            {
                'action': 'message',
                'label': '📋 게임목록',
                'messageText': '게임목록'
            },
            {
                'action': 'message',
                'label': '❓ 도움말',
                'messageText': '도움말'
            }
        ]
    
    def _get_adventure_quick_replies(self) -> list:
        """
        모험 게임 중 Quick Replies 버튼 목록 생성
        """
        return [
            {
                'action': 'message',
                'label': '🔨 강화',
                'messageText': '강화'
            },
            {
                'action': 'message',
                'label': '🗡️ 사냥',
                'messageText': '사냥'
            },
            {
                'action': 'message',
                'label': '💰 판매',
                'messageText': '판매'
            },
            {
                'action': 'message',
                'label': '📊 상태',
                'messageText': '상태'
            },
            {
                'action': 'message',
                'label': '🏆 랭킹',
                'messageText': '리더보드'
            },
            {
                'action': 'message',
                'label': '❌ 종료',
                'messageText': '게임종료'
            }
        ]
    
    def _create_response(
        self,
        text: str,
        quick_replies: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        카카오 챗봇 관리자센터 스킬 서버 응답 생성
        
        응답 형식:
        {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "응답 메시지",
                            "extra": {}
                        }
                    }
                ],
                "quickReplies": [
                    {
                        "action": "message",
                        "label": "버튼 텍스트",
                        "messageText": "전송될 메시지"
                    }
                ]
            }
        }
        
        Args:
            text: 응답 메시지 텍스트
            quick_replies: Quick Replies 버튼 목록 (None이면 기본 버튼 사용)
        """
        if quick_replies is None:
            quick_replies = self._get_default_quick_replies()
        
        return {
            'version': '2.0',
            'template': {
                'outputs': [
                    {
                        'simpleText': {
                            'text': text,
                            'extra': {}
                        }
                    }
                ],
                'quickReplies': quick_replies
            }
        }
    
    def _setup_routes(self):
        """라우트 설정"""
        
        @self.app.post('/webhook')
        async def webhook(request: Request):
            """카카오 챗봇 관리자센터 스킬 서버 엔드포인트"""
            try:
                data = await request.json()
                
                # 요청 로그 (디버깅용)
                print(f"[웹훅 요청] {data}")
                
                # 카카오 챗봇 관리자센터 스킬 서버 형식 파싱
                user_id, message, user_name = self._parse_user_request(data)
                
                if not user_id or not message:
                    # userRequest 형식이 아닌 경우 다른 형식 시도
                    user_id = data.get('user', {}).get('id') or data.get('user_id', '')
                    message = data.get('content', {}).get('text') or data.get('message', '') or data.get('utterance', '')
                    user_name = data.get('user', {}).get('nickname') or data.get('user_name')
                
                if not user_id or not message:
                    print(f"[웹훅 오류] 잘못된 요청 형식: {data}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            'version': '2.0',
                            'template': {
                                'outputs': [
                                    {
                                        'simpleText': {
                                            'text': '❌ 잘못된 요청 형식입니다.',
                                            'extra': {}
                                        }
                                    }
                                ],
                                'quickReplies': self._get_default_quick_replies()
                            }
                        }
                    )
                
                # 플랫폼 어댑터 설정 (멘션 기능용)
                self.engine.set_platform_adapter(self.adapter)
                
                # 메시지 처리 (사용자 이름 전달)
                response_text = self.engine.process_message(user_id, message, user_name=user_name, platform_adapter=self.adapter)
                
                # Quick Replies 버튼 결정
                # 모험 게임 중이면 모험 게임 버튼, 아니면 기본 버튼
                quick_replies = None
                if self.engine.has_active_game(user_id):
                    # 게임 타입 확인을 위해 게임 이름으로 판단
                    # 응답 텍스트에 "모험" 또는 "강화" 키워드가 있으면 모험 게임
                    if ('강화' in response_text or
                            '사냥' in response_text or
                            '모험' in response_text):
                        quick_replies = self._get_adventure_quick_replies()
                
                # 카카오 챗봇 관리자센터 스킬 서버 응답 형식으로 반환
                response = self._create_response(response_text, quick_replies)
                
                print(f"[웹훅 응답] 사용자: {user_id}, 메시지: {message}, 응답: {response_text[:50]}...")
                
                return JSONResponse(content=response)
                
            except Exception as e:
                print(f"[웹훅 오류] {e}")
                import traceback
                traceback.print_exc()
                
                # 오류 응답도 올바른 형식으로 반환
                return JSONResponse(
                    status_code=500,
                    content={
                        'version': '2.0',
                        'template': {
                            'outputs': [
                                {
                                    'simpleText': {
                                        'text': f'❌ 오류가 발생했습니다: {str(e)}',
                                        'extra': {}
                                    }
                                }
                            ],
                            'quickReplies': []
                        }
                    }
                )
        
        @self.app.get('/health')
        async def health():
            """헬스 체크"""
            return {'status': 'ok'}
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """서버 실행"""
        host = host or Config.SERVER_HOST
        port = port or Config.SERVER_PORT
        print(f"웹훅 서버 시작: http://{host}:{port}/webhook")
        uvicorn.run(self.app, host=host, port=port, log_level="info")


def create_webhook_server(adapter: KakaoAdapter, engine: GameEngine) -> WebhookServer:
    """웹훅 서버 생성"""
    return WebhookServer(adapter, engine)


def create_app():
    """FastAPI 앱 생성 (Gunicorn용)"""
    from platforms.kakao_adapter import KakaoAdapter
    from game_engine import GameEngine
    
    adapter = KakaoAdapter()
    engine = GameEngine()
    server = WebhookServer(adapter, engine)
    return server.app

