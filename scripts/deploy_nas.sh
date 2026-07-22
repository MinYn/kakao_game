#!/usr/bin/env bash
# NAS 배포 스크립트
# - master 최신 코드 pull
# - .env / Docker 볼륨 유지
# - gamebot + worker 이미지 재빌드 후 재기동
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/home/miny/github/kakao_game}"
BRANCH="${DEPLOY_BRANCH:-master}"
# Discord 봇 스택 (nginx 제외: HTTP 서버 없음)
COMPOSE_SERVICES="${COMPOSE_SERVICES:-postgres redis zookeeper kafka gamebot worker}"

log() { printf '[deploy] %s\n' "$*"; }
die() { printf '[deploy] ERROR: %s\n' "$*" >&2; exit 1; }

cd "$DEPLOY_DIR" || die "배포 디렉터리 없음: $DEPLOY_DIR"

command -v docker >/dev/null || die "docker 가 설치되어 있지 않습니다"

# user systemd / 일부 세션에서는 docker 그룹이 적용되지 않을 수 있음 → sg docker 폴백
docker_sh() {
  local cmd=$1
  if docker info >/dev/null 2>&1; then
    bash -lc "cd $(printf '%q' "$DEPLOY_DIR") && $cmd"
  elif command -v sg >/dev/null 2>&1; then
    sg docker -c "cd $(printf '%q' "$DEPLOY_DIR") && $cmd"
  else
    die "docker 권한 없음 (docker 그룹 또는 root 필요)"
  fi
}

docker_sh "docker compose version >/dev/null" || die "docker compose 를 사용할 수 없습니다"

[[ -f .env ]] || die ".env 파일이 없습니다. 먼저 NAS에 .env 를 구성하세요."
[[ -d .git ]] || die "git 저장소가 아닙니다: $DEPLOY_DIR"

log "배포 시작: dir=$DEPLOY_DIR branch=$BRANCH"

# .env 는 git 추적 대상이 아니므로 reset 후에도 유지됨
log "코드 동기화 (origin/${BRANCH})"
git fetch --prune origin
git checkout "$BRANCH"
git reset --hard "origin/${BRANCH}"

SHORT_SHA="$(git rev-parse --short HEAD)"
log "HEAD=${SHORT_SHA} $(git log -1 --pretty=format:'%s')"

log "이미지 빌드 (gamebot, worker)"
docker_sh "docker compose build gamebot worker"

log "서비스 기동: ${COMPOSE_SERVICES}"
docker_sh "docker compose up -d --remove-orphans ${COMPOSE_SERVICES}"

log "상태 확인"
docker_sh "docker compose ps"

sleep 5
log "gamebot 최근 로그"
docker_sh "docker compose logs --tail=30 gamebot" || true

log "배포 완료 (${SHORT_SHA})"
