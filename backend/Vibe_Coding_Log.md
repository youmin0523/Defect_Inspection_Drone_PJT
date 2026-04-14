# 🤖 바이브코딩(Vibe Coding) 프롬프트 & 결과 추적 로그

> **💡 설명**: 백엔드(Backend) 전용 바이브코딩 로그입니다. AI에게 언제, 어떤 프롬프트를 입력하여 어떤 코드를 도출했는지 기록합니다.

---

## 📝 기본 정보 (Meta)

- 작성자 (Who): @youminsu0523
- 작성 일자 (When): 2026-04-14
- 목표 기능 (Objective): AeroInspect 드론 하자점검 플랫폼 백엔드 전체 스캐폴드 구축 (FastAPI + SQLAlchemy async + MJPEG 스트리밍 + YOLOv8 + LLM 보고서)
- 작업 브랜치/환경: `MS`

---

## 💬 바이브코딩 대화 흐름 (Vibe Coding Log)

### 1️⃣ 초기 질문 / 프롬프트 (Initial Prompt)
> *계획서(v1.3) PDF를 첨부하여 AI에게 전달한 지시*
- **프롬프트 내용**:
  ```text
  "위 계획서 참고해서 backend/ frontend 에 맞춰서 기초 파일 작업해줘"
  ```

### 2️⃣ 계획(Plan) 단계 피드백 (Plan Mode Feedback)
> *AI가 플랜을 제안한 후 팀원이 추가 요구사항 3가지를 제시*
- **피드백 1** (카메라 전환):
  > "IRC-256CA 열화상 카메라와 일반 카메라의 전환이 필요해"
  → 해결: `/stream/rgb`, `/stream/thermal`, `/stream/blend` 3개 엔드포인트 + `POST /stream/mode` API 추가, WS `camera.mode_changed` 이벤트 브로드캐스트 설계
- **피드백 2** (환경 파일):
  > "backend와 frontend에 .env와 .gitignore, venv 등 필요한 폴더들을 함께 구축해줘"
  → 해결: `.env`, `.env.example`, `.gitignore`, `Dockerfile`, `alembic.ini` 포함
- **피드백 3** (파일 주석):
  > "각 파일 내부에 주석으로 이 파일은 어떠한 역할을 하는 파일들인지에 대한 설명도 제일 위에 적어줘"
  → 해결: 모든 Python 파일 최상단 `# ===== 파일명 =====\n# 역할: ...` 블록 주석 추가

### 3️⃣ 구현된 백엔드 핵심 아키텍처

#### 비동기 처리 원칙
- OpenCV `cap.read()`, PyTorch 추론, pyserial 모두 블로킹 → `asyncio.to_thread()` 래핑
- DB: `asyncpg` 드라이버 + SQLAlchemy async 네이티브 비동기
- Claude API: `AsyncAnthropic` 클라이언트

#### MJPEG 멀티클라이언트 팬아웃 패턴
```python
# app/services/camera.py 핵심 패턴
class CameraService:
    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=2)  # 최신 2프레임만 버퍼
        self._subscribers.append(q)
        return q

    async def _capture_loop(self):
        while self._running:
            frame = await asyncio.to_thread(self._cap.read)
            for q in self._subscribers:
                if q.full():
                    q.get_nowait()  # 오래된 프레임 드롭
                await q.put(frame)
```

#### WebSocket 싱글톤 매니저
```python
# app/core/ws_manager.py
class ConnectionManager:
    channels: dict[str, list[WebSocket]]  # defects/telemetry/thermal/camera

ws_manager = ConnectionManager()  # 모듈 레벨 싱글톤
# Dockerfile에서 --workers 1 강제 (다중 프로세스 시 인스턴스 분리 방지)
```

#### 열화상 블렌드 합성
```python
# app/core/streaming.py
def _blend_frames(rgb: np.ndarray, thermal: np.ndarray, alpha: float) -> np.ndarray:
    thermal_resized = cv2.resize(thermal, (rgb.shape[1], rgb.shape[0]))
    return cv2.addWeighted(rgb, 1 - alpha, thermal_resized, alpha, 0)
```

---

## ✅ 최종 결과 (Final Outcome)

### 📁 생성된 백엔드 파일 목록 (48개)
- `requirements.txt` — FastAPI, SQLAlchemy[asyncio], asyncpg, opencv-python, ultralytics, anomalib, pyserial, anthropic, google-generativeai 등
- `app/main.py` — lifespan: init_db → rgb/thermal camera open → yolo model load
- `app/config.py` — pydantic-settings 기반 환경변수 (DATABASE_URL, ANTHROPIC_API_KEY, THERMAL_BLEND_ALPHA 등)
- `app/core/ws_manager.py` — 채널별 WebSocket 연결 관리 싱글톤
- `app/core/streaming.py` — MJPEG 제너레이터 + blend_frames() 합성
- `app/models/defect.py` — DefectLog ORM (UUID PK, area A-E, severity HIGH/MED/LOW, lidar_x/y/z, raw_payload JSONB)
- `app/api/stream.py` — `/stream/rgb`, `/stream/thermal`, `/stream/blend`, `POST /stream/mode`
- `app/api/report.py` — LLM 스트리밍 보고서 생성 (Claude/Gemini)
- `app/services/camera.py` — RGB 카메라 서비스 + 구독자 큐 팬아웃
- `app/services/thermal.py` — IRC-256CA 16bit ADC→섭씨 변환 + COLORMAP_INFERNO
- `app/services/yolo_inference.py` — YOLOv8 싱글톤 (가중치 없으면 더미 모드)
- `app/services/lidar.py` — TF-Luna UART 9바이트 프레임 파싱
- `app/utils/severity_mapper.py` — 20종 하자 카탈로그 (A-01 ~ E-02)
- `alembic/env.py` — async_engine_from_config 패턴 비동기 마이그레이션
- `tests/test_defects_api.py`, `test_ws_manager.py`, `test_yolo_inference.py` — pytest 스텁

### 📊 아키텍처 영향도
- **DB 스키마**: 복합 인덱스 `(severity, timestamp DESC)`, `(area, timestamp DESC)` 적용
- **카메라 전환**: 단일 `POST /stream/mode` API → WS 브로드캐스트 → 모든 클라이언트 동기화
- **AI 파이프라인**: YOLOv8(탐지) + Anomalib PatchCore(이상탐지) 병렬 추론

---

## 💡 배운 점 및 인사이트 (Lessons Learned)

- **블로킹 I/O 격리**: OpenCV, PyTorch, pyserial은 모두 동기 블로킹 → FastAPI async 이벤트 루프 차단 방지를 위해 반드시 `asyncio.to_thread()` 사용
- **MJPEG 팬아웃**: 구독자별 `asyncio.Queue(maxsize=2)` 유지로 슬로우 클라이언트가 빠른 클라이언트를 차단하지 않도록 설계
- **단일 워커 제약**: WS 매니저 싱글톤은 `--workers 1` 강제 필요, 수평 확장 시 Redis pub/sub 백엔드 교체 필요
- **열화상 좌표 매핑**: IRC-256CA 16bit ADC 값 → 섭씨 변환: `temp = (raw_value / 100.0) - 273.15`
