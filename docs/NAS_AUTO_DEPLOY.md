# NAS 자동 배포 (master → Docker)

`master` 브랜치에 머지/푸시되면 GitHub Actions **self-hosted runner**(NAS)가
`scripts/deploy_nas.sh` 를 실행해 Docker 스택을 재배포합니다.

## 구성 요약

| 구성요소 | 역할 |
|----------|------|
| `.github/workflows/deploy-nas.yml` | `push` to `master` / 수동 실행 트리거 |
| `scripts/deploy_nas.sh` | `git pull` → `docker compose build` → `up -d` |
| Self-hosted runner | NAS에서 Actions job 실행 (`labels: self-hosted, Linux, X64, nas`) |
| `/home/miny/github/kakao_game/.env` | 시크릿(토큰 등). git에 없음, 배포 시 유지 |

## 배포 동작

1. Actions runner가 job 수신
2. `deploy_nas.sh` 실행
3. `origin/master` 로 hard reset (로컬 코드 맞춤, **`.env` 유지**)
4. `gamebot` / `worker` 이미지 빌드
5. `postgres redis zookeeper kafka gamebot worker` 기동 (`--remove-orphans`)
6. 상태/로그 출력

데이터 볼륨(`postgres_data`, `redis_data` 등)은 삭제하지 않습니다.

## 수동 배포

```bash
cd /home/miny/github/kakao_game
./scripts/deploy_nas.sh
```

또는 GitHub → Actions → **Deploy to NAS** → **Run workflow**.

## Runner 관리

```bash
# 상태 (systemd 서비스 이름 예시)
sudo systemctl status actions.runner.*

# 로그
journalctl -u 'actions.runner.*' -f
```

Runner 재등록이 필요하면:

```bash
cd ~/actions-runners/kakao_game
./svc.sh stop
./config.sh remove --token <REMOVE_TOKEN>
# GitHub에서 registration token 발급 후
./config.sh --url https://github.com/MinYn/kakao_game --token <REG_TOKEN> \
  --name nas-kakao-game --labels nas --work _work --unattended
./svc.sh install
./svc.sh start
```

## 주의사항

- `.env` 의 `DISCORD_TOKEN` 등은 NAS에만 두고 저장소에 올리지 마세요.
- Runner는 저장소에 대한 write/배포 권한이 있으므로 NAS 계정 보안을 유지하세요.
- 동시 배포는 `concurrency` 로 직렬화됩니다.
