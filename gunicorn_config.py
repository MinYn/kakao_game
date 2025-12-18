"""
Gunicorn 설정 파일
FastAPI (ASGI) 애플리케이션용
"""
import multiprocessing
import os

# 서버 소켓
bind = f"0.0.0.0:{os.getenv('SERVER_PORT', '5000')}"
backlog = 2048

# 워커 프로세스 (ASGI용 Uvicorn 워커 사용)
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 60
keepalive = 5

# 로깅
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# 프로세스 이름
proc_name = "gamebot"

# 서버 메커니즘
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_redirect = False

# 성능 튜닝
max_requests = 1000
max_requests_jitter = 50
preload_app = False

# SSL (필요시)
# keyfile = None
# certfile = None
