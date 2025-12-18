#!/usr/bin/env python3
"""
서버 실행 스크립트
Gunicorn 또는 Uvicorn으로 실행
"""
import os
import sys
from config import Config

def run_with_gunicorn():
    """Gunicorn으로 실행"""
    import gunicorn.app.wsgiapp as wsgi
    
    # Gunicorn 명령줄 인자 설정
    sys.argv = [
        'gunicorn',
        'webhook_server:create_app()',
        '-c', 'gunicorn_config.py',
    ]
    
    wsgi.run()


def run_with_uvicorn():
    """Uvicorn으로 실행 (개발용)"""
    from webhook_server import create_app
    import uvicorn
    
    app = create_app()
    uvicorn.run(
        app,
        host=Config.SERVER_HOST,
        port=Config.SERVER_PORT,
        log_level=Config.LOG_LEVEL.lower()
    )


if __name__ == '__main__':
    # 환경변수로 실행 방식 결정
    use_gunicorn = os.getenv('USE_GUNICORN', 'true').lower() == 'true'
    
    if use_gunicorn:
        run_with_gunicorn()
    else:
        run_with_uvicorn()
