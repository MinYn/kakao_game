FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 폰트 파일 복사 (Galmuri, Font Awesome)
COPY fonts/ /usr/share/fonts/truetype/custom/
RUN fc-cache -fv

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 5000

# 애플리케이션 실행
# 환경변수 USE_GUNICORN으로 Gunicorn 또는 직접 실행 선택
# Gunicorn 사용 시: gunicorn webhook_server:create_app -c gunicorn_config.py
# 직접 실행 시: python main.py kakao
CMD ["sh", "-c", "if [ \"$USE_GUNICORN\" = \"true\" ]; then gunicorn webhook_server:create_app -c gunicorn_config.py; else python main.py kakao; fi"]

