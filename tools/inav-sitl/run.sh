#!/usr/bin/env bash
# =============================================
# tools/inav-sitl/run.sh
# INAV SITL + socat 가상 시리얼 라이프사이클 헬퍼.
#
# 흐름:
#   1) bash run.sh up      → SITL + socat 기동 → /tmp/aeroinspect-fc-uart 가상 PTY 생성
#   2) AEROINSPECT_FC_UART=/tmp/aeroinspect-fc-uart python3 pi/fc_bridge.py 별도 터미널
#   3) bash run.sh logs    → SITL 로그 모니터
#   4) bash run.sh down
# =============================================
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="$HERE/docker-compose.yml"

cmd="${1:-help}"
case "$cmd" in
  build)  docker compose -f "$COMPOSE" build ;;
  up)
    docker compose -f "$COMPOSE" up -d
    echo "[sitl] up. virtual UART: /tmp/aeroinspect-fc-uart"
    echo "[sitl] start fc_bridge:  AEROINSPECT_FC_UART=/tmp/aeroinspect-fc-uart python3 pi/fc_bridge.py"
    ;;
  down|stop) docker compose -f "$COMPOSE" down ;;
  logs)      docker compose -f "$COMPOSE" logs -f ;;
  restart)   docker compose -f "$COMPOSE" restart ;;
  *)
    cat <<EOF
Usage: $0 {build|up|down|logs|restart}
  build    INAV SITL + socat 컨테이너 빌드
  up       기동 → /tmp/aeroinspect-fc-uart 가상 PTY 생성
  down     정지 + 제거
  logs     SITL stdout/stderr 모니터
EOF
    ;;
esac
