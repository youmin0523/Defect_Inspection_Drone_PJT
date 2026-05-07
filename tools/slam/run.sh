#!/usr/bin/env bash
# =============================================
# tools/slam/run.sh
# Visual SLAM 컨테이너 라이프사이클 헬퍼.
# =============================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="$HERE/docker-compose.yml"
BACKEND="${AEROINSPECT_SLAM_BACKEND:-orbslam3}"

cmd="${1:-help}"
case "$cmd" in
  build)
    docker compose -f "$COMPOSE" --profile "$BACKEND" build
    ;;
  up)
    docker compose -f "$COMPOSE" --profile "$BACKEND" up -d
    echo "[slam] $BACKEND started. logs: bash $0 logs"
    ;;
  down|stop)
    docker compose -f "$COMPOSE" --profile "$BACKEND" down
    ;;
  logs)
    docker compose -f "$COMPOSE" --profile "$BACKEND" logs -f
    ;;
  restart)
    docker compose -f "$COMPOSE" --profile "$BACKEND" restart
    ;;
  *)
    cat <<EOF
Usage: AEROINSPECT_SLAM_BACKEND={orbslam3|rtabmap} $0 {build|up|down|logs|restart}
  build     SLAM 컨테이너 빌드 (orbslam3 의 경우 30~60분)
  up        컨테이너 기동
  down      정지 + 제거
  logs      stdout JSONL 모니터
  restart   재기동
EOF
    ;;
esac
