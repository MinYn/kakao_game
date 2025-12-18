#!/bin/bash
# Nginx 접근 문제 진단 스크립트

echo "=== Nginx 접근 문제 진단 ==="
echo ""

# 1. 컨테이너 상태 확인
echo "1. 컨테이너 상태 확인:"
docker-compose ps
echo ""

# 2. Nginx 컨테이너 로그 확인
echo "2. Nginx 컨테이너 로그 (최근 20줄):"
docker-compose logs --tail=20 nginx
echo ""

# 3. Gamebot 컨테이너 상태 확인
echo "3. Gamebot 컨테이너 상태:"
docker-compose ps gamebot
echo ""

# 4. 포트 확인
echo "4. 포트 확인:"
EXTERNAL_PORT=${EXTERNAL_PORT:-8080}
echo "외부 포트: $EXTERNAL_PORT"
netstat -an | grep ":$EXTERNAL_PORT" || lsof -i :$EXTERNAL_PORT || echo "포트 $EXTERNAL_PORT 사용 가능"
echo ""

# 5. Nginx 설정 검증
echo "5. Nginx 설정 검증:"
docker-compose exec nginx nginx -t 2>&1 || echo "Nginx 컨테이너가 실행 중이지 않습니다"
echo ""

# 6. 네트워크 확인
echo "6. 네트워크 확인:"
docker network inspect kakao_game_gamebot-network 2>/dev/null | grep -A 5 "Containers" || echo "네트워크를 찾을 수 없습니다"
echo ""

# 7. 직접 연결 테스트
echo "7. Gamebot 직접 연결 테스트:"
docker-compose exec nginx wget -O- http://gamebot:5000/health 2>&1 | head -5 || echo "Gamebot에 연결할 수 없습니다"
echo ""

# 8. 외부 접근 테스트
echo "8. 외부 접근 테스트:"
curl -v http://localhost:$EXTERNAL_PORT/health 2>&1 | head -10 || echo "외부 접근 실패"
echo ""

echo "=== 진단 완료 ==="
