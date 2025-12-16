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
import uvicorn


class WebhookServer:
    """카카오 챗봇 관리자센터 스킬 서버 클래스"""
    
    def __init__(self, adapter: KakaoAdapter, engine: GameEngine):
        self.app = FastAPI(title="카카오 게임봇 웹훅 서버")
        self.adapter = adapter
        self.engine = engine
        self._setup_routes()
    
    def _parse_user_request(self, data: Dict[str, Any]) -> tuple[str, str]:
        """
        카카오 챗봇 관리자센터 스킬 서버 요청 파싱
        
        요청 형식:
        {
            "userRequest": {
                "user": {
                    "id": "user_id"
                },
                "utterance": "사용자 메시지"
            }
        }
        """
        user_request = data.get('userRequest', {})
        user = user_request.get('user', {})
        user_id = user.get('id', '')
        utterance = user_request.get('utterance', '')
        
        return str(user_id), utterance
    
    def _create_response(self, text: str) -> Dict[str, Any]:
        """
        카카오 챗봇 관리자센터 스킬 서버 응답 생성
        
        응답 형식:
        {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "응답 메시지"
                        }
                    }
                ]
            }
        }
        """
        return {
            'version': '2.0',
            'template': {
                'outputs': [
                    {
                        'simpleText': {
                            'text': text
                        }
                    }
                ]
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
                user_id, message = self._parse_user_request(data)
                
                if not user_id or not message:
                    # userRequest 형식이 아닌 경우 다른 형식 시도
                    user_id = data.get('user', {}).get('id') or data.get('user_id', '')
                    message = data.get('content', {}).get('text') or data.get('message', '') or data.get('utterance', '')
                
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
                                            'text': '❌ 잘못된 요청 형식입니다.'
                                        }
                                    }
                                ]
                            }
                        }
                    )
                
                # 메시지 처리
                response_text = self.engine.process_message(user_id, message)
                
                # 카카오 챗봇 관리자센터 스킬 서버 응답 형식으로 반환
                response = self._create_response(response_text)
                
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
                                        'text': f'❌ 오류가 발생했습니다: {str(e)}'
                                    }
                                }
                            ]
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

