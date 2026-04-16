#!/bin/sh
# Claude Code SessionEnd 훅 래퍼
# - 세션 종료 시 append_vibe_log.py 를 실행한다
# - python3 / python 우선순위로 fallback
# - 스크립트가 없거나 python 이 없으면 조용히 패스 (세션 종료는 절대 막지 않음)

if [ -z "$CLAUDE_PROJECT_DIR" ]; then
    CLAUDE_PROJECT_DIR="$(pwd)"
fi

SCRIPT="$CLAUDE_PROJECT_DIR/scripts/append_vibe_log.py"
if [ ! -f "$SCRIPT" ]; then
    echo "[vibe-log] 스크립트 없음: $SCRIPT — 건너뜀"
    exit 0
fi

if command -v python3 >/dev/null 2>&1; then
    python3 "$SCRIPT"
elif command -v python >/dev/null 2>&1; then
    python "$SCRIPT"
else
    echo "[vibe-log] python 미설치 — 건너뜀"
fi

exit 0
