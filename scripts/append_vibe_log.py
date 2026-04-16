"""Claude Code SessionEnd 훅 — 세션 transcript(.jsonl) 를 파싱해
수정된 파일 스코프(backend/ or frontend/)에 맞춰
Vibe_Coding_Log.md 에 요약 블록을 자동 append.

입력: stdin JSON (SessionEnd hook 규격)
  { "session_id", "transcript_path", "cwd", "hook_event_name", "reason" }

동작:
  1) transcript 파싱 → 사용자 프롬프트 목록 + Edit/Write 대상 파일 + 마지막 assistant text
  2) 파일 경로로 backend / frontend 스코프 분류
  3) 각 스코프별 Vibe_Coding_Log.md 에 블록 append (세션 ID 마커로 중복 방지)

실패해도 exit 0 — 절대 세션 종료를 막지 않는다.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime

# Windows(cp949 등) 콘솔에서 이모지/em-dash print 시 터지지 않도록 강제 UTF-8.
for _stream in ("stdout", "stderr"):
    try:
        getattr(sys, _stream).reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


LOG_ROUTE = {
    "frontend": "frontend/Vibe_Coding_Log.md",
    "backend": "backend/Vibe_Coding_Log.md",
}

PROMPT_MAX_SHOW = 6
PROMPT_CHARS = 160
RESULT_CHARS = 420
FILES_MAX_SHOW = 12

# transcript 에서 '사용자 프롬프트' 로 치지 않을 메타 텍스트
IGNORE_PATTERNS = (
    "<command-name>",
    "<command-message>",
    "<local-command-stdout>",
    "<system-reminder>",
    "<ide_opened_file>",
    "<ide_selection>",
    "<user-prompt-submit-hook>",
    "[Request interrupted by user",  # 도구 사용 중단 메타 메시지
)

# 사용자 의도를 담지 않는 자동 resume/이어가기 명령
IGNORE_EXACT = (
    "Continue from where you left off.",
    "continue",
    "Continue",
)

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def load_session_input():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def _extract_user_text(content):
    """user message content(string or list) → 프롬프트 문자열 (없으면 None)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if not isinstance(p, dict):
                continue
            if p.get("type") == "text":
                parts.append(p.get("text", ""))
            # tool_result 는 프롬프트 아님 → 무시
        text = "".join(parts)
        return text or None
    return None


def parse_transcript(path):
    user_prompts = []
    files_edited = set()
    last_assistant_text = ""

    if not os.path.exists(path):
        return user_prompts, files_edited, last_assistant_text

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                m = json.loads(line)
            except Exception:
                continue

            t = m.get("type")
            if t not in ("user", "assistant"):
                continue  # queue-operation / attachment / summary 등 무시

            msg = m.get("message") or {}

            if t == "user":
                text = _extract_user_text(msg.get("content"))
                if not text:
                    continue
                if any(pat in text for pat in IGNORE_PATTERNS):
                    continue
                stripped = text.strip()
                if stripped and stripped not in IGNORE_EXACT:
                    user_prompts.append(stripped)

            else:  # assistant
                content = msg.get("content") or []
                if not isinstance(content, list):
                    continue
                text_fragment = ""
                for p in content:
                    if not isinstance(p, dict):
                        continue
                    ptype = p.get("type")
                    if ptype == "tool_use":
                        tool = p.get("name", "")
                        inp = p.get("input") or {}
                        fp = inp.get("file_path")
                        if fp and tool in EDIT_TOOLS:
                            files_edited.add(fp)
                    elif ptype == "text":
                        text_fragment += p.get("text", "")
                if text_fragment.strip():
                    last_assistant_text = text_fragment.strip()

    return user_prompts, files_edited, last_assistant_text


def classify_scope(files, cwd):
    """수정 파일들을 backend / frontend 스코프로 분류. 매칭 없는 파일은 드롭."""
    cwd_norm = os.path.normpath(cwd).replace("\\", "/").rstrip("/")
    areas = {"frontend": [], "backend": []}
    for f in files:
        norm = os.path.normpath(f).replace("\\", "/")
        rel = norm
        if cwd_norm and norm.lower().startswith(cwd_norm.lower() + "/"):
            rel = norm[len(cwd_norm) + 1:]
        for area in areas:
            if rel.startswith(area + "/") or f"/{area}/" in rel:
                areas[area].append(rel)
                break
    return {k: v for k, v in areas.items() if v}


def git_user_name(cwd):
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "config", "user.name"],
            capture_output=True, text=True, timeout=3
        )
        name = r.stdout.strip()
        if name:
            return name
    except Exception:
        pass
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"


def _condense(s):
    return re.sub(r"\s+", " ", s).strip()


def truncate(s, n):
    s = _condense(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def format_block(session_id, author, user_prompts, files_in_area, last_text):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = truncate(user_prompts[0], 60) if user_prompts else "(프롬프트 없음)"
    sid_short = (session_id.split("-")[0] if session_id else "unknown")[:8]

    lines = []
    lines.append(f"#### ⏱ {now} | [auto|{author}] {title}")
    lines.append(f"- **세션 ID**: `{sid_short}` <!-- session:{session_id} -->")
    lines.append(f"- **주요 프롬프트** ({len(user_prompts)}회):")
    shown = user_prompts[:PROMPT_MAX_SHOW]
    for i, p in enumerate(shown, 1):
        lines.append(f"  {i}. \"{truncate(p, PROMPT_CHARS)}\"")
    remaining = len(user_prompts) - len(shown)
    if remaining > 0:
        lines.append(f"  - … 외 {remaining}건 생략")

    lines.append(f"- **수정 파일** ({len(files_in_area)}개):")
    for f in sorted(files_in_area)[:FILES_MAX_SHOW]:
        lines.append(f"  - `{f}`")
    if len(files_in_area) > FILES_MAX_SHOW:
        lines.append(f"  - … 외 {len(files_in_area) - FILES_MAX_SHOW}개 생략")

    if last_text:
        lines.append(f"- **결과 요약(assistant 마지막 발화)**: {truncate(last_text, RESULT_CHARS)}")

    lines.append("- **상태**: 🤖 자동 생성 초안 — 팀원 보강 권장")
    return "\n".join(lines) + "\n"


def already_logged(log_path, session_id):
    if not os.path.exists(log_path):
        return False
    marker = f"session:{session_id}"
    size = os.path.getsize(log_path)
    start = max(0, size - 200_000)  # 꼬리 200KB 만 스캔
    with open(log_path, "rb") as f:
        f.seek(start)
        tail = f.read().decode("utf-8", errors="ignore")
    return marker in tail


def append_to_log(log_path, block):
    parent = os.path.dirname(log_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    need_separator = os.path.exists(log_path) and os.path.getsize(log_path) > 0
    with open(log_path, "a", encoding="utf-8") as f:
        if need_separator:
            f.write("\n")
        f.write(block)


def main():
    data = load_session_input()
    session_id = (data.get("session_id") or "").strip()
    transcript = (data.get("transcript_path") or "").strip()
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    if not session_id or not transcript:
        print("[vibe-log] session_id / transcript_path 누락 — 건너뜀")
        return 0

    user_prompts, files_edited, last_text = parse_transcript(transcript)
    if not files_edited:
        print("[vibe-log] 수정된 파일 없음 — 건너뜀 (대화만 한 세션)")
        return 0
    if not user_prompts:
        print("[vibe-log] 사용자 프롬프트 없음 — 건너뜀")
        return 0

    areas = classify_scope(files_edited, cwd)
    if not areas:
        print("[vibe-log] backend/ · frontend/ 외 스코프 — 건너뜀")
        return 0

    author = git_user_name(cwd)
    cwd_abs = os.path.abspath(cwd)

    appended = []
    skipped = []
    for area, files_in_area in areas.items():
        log_path = os.path.join(cwd_abs, *LOG_ROUTE[area].split("/"))
        if already_logged(log_path, session_id):
            skipped.append(LOG_ROUTE[area])
            continue
        block = format_block(session_id, author, user_prompts, files_in_area, last_text)
        append_to_log(log_path, block)
        appended.append(LOG_ROUTE[area])

    parts = []
    if appended:
        parts.append("append: " + ", ".join(appended))
    if skipped:
        parts.append("이미 기록됨: " + ", ".join(skipped))
    print("[vibe-log] " + (" / ".join(parts) if parts else "변경 없음"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[vibe-log] 예외 — 건너뜀: {e}", file=sys.stderr)
        sys.exit(0)
