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

---

## 4️⃣ 추가 피드백 & 반영 — 회원가입 DB 설계 라운드
> **착수 시각**: 2026-04-16 14:30
> **목표**: 프론트엔드 회원가입 폼(`Signup.jsx`)을 백엔드 DB에 연결하기 위한 모델 설계.
> **전제(사용자 요청)**: AWS 프리티어 만료 임박 → DB 실제 기동은 최종 단계에서 한 번만. 그 전에는 모델·스키마·해싱·엔드포인트 코드만 먼저 완성.

### ⏱ 14:30 | "지금 회원가입을 위한 DB를 연결하고자 해"
→ 현재 상태 점검(PostgreSQL+asyncpg+SQLAlchemy 기반 이미 구성, User 모델 부재) 후 스키마 범위·DB 선택지·해싱 방식 확정 질의.

### ⏱ 14:35 | "테이블 먼저 구성하자"
→ 단일 `users` 테이블 초안 제안 (개인/사업자 account_type 컬럼으로 통합, 사업자 필드 nullable).

### ⏱ 14:38 | "DB 연결은 … 다 구현하고 마지막에 연결할게. 아마존 무료 기간이 얼마 남지 않아서"
→ 프로젝트 메모리 `project_aws_free_tier.md` 등록. 작업 순서 확정: 테이블 → 스키마 → 해싱 → 엔드포인트 → (최후) DB 연결.

### ⏱ 14:42 | "테이블 분리에 대해서는 제1정규화 ~ 제3정규화 고려해서 작성해줘"
→ 단일 테이블 초안 폐기. 3NF 기준으로 4 테이블 재설계:
- `users` — 공통 회원 정보 (account_type, email, username, password_hash, name, phone)
- `business_profiles` — 사업자 1:1 분리 (user_id PK=FK, biz_number UNIQUE, ceo_name, verified_at) → `account_type → biz_*` 이행 종속 제거
- `terms` — 약관 마스터 (code, is_required, version) → 약관 추가 시 스키마 불변
- `user_term_agreements` — 동의 이력 M:N 연결 (user_id + term_id 복합 PK, version 스냅샷, agreed_at) → 1NF 반복그룹 제거

### ⏱ 14:46 | "응 구현해줘"
→ 4개 ORM 모델 파일 신규 작성:
- `app/models/user.py` (UUID PK, account_type ENUM, unique email/username, relationships)
- `app/models/business_profile.py` (user_id PK/FK CASCADE, biz_number UNIQUE)
- `app/models/term.py` (SERIAL PK, code UNIQUE, is_required/version)
- `app/models/user_term_agreement.py` (복합 PK, version 스냅샷)
- `app/models/__init__.py` — 신규 4개 모델 포함시켜 `Base.metadata` 자동 등록
- `app/db/init_db.py` — 신규 모델 임포트 추가

### ⏱ 14:50 | "DB 연결을 python으로 해야돼? Node.js로 하면 되지 않아?"
→ Python 유지 권장 (판단 근거):
- 기존 FastAPI 백엔드가 DefectLog/WebSocket/MJPEG/LiDAR 전부 Python SQLAlchemy 세션 공유 중
- AI 파이프라인(YOLOv8/anomalib/OpenCV/pyserial) Python 전용 → Node 이식 불가
- 서버 2개 운영 시 AWS 프리티어 시간 2배 소진 (이번 라운드 제약 직접 위반)

### ⏱ 14:52 | "너 말대로 진행해줘"
→ Python 확정. 다음 라운드: Pydantic 스키마(`app/schemas/user.py`) → 비밀번호 해싱 유틸(`app/core/security.py` + `passlib[bcrypt]`) → 회원가입/중복확인 엔드포인트 → 최종 DB 연결.

### 📐 3NF 설계 근거 요약
- **1NF**: 약관 동의를 M:N 연결 테이블로 원자화, 컬럼 기반 반복그룹 제거
- **2NF**: 단일 PK 테이블은 자동 충족. 연결 테이블의 version/agreed_at 도 복합 PK 전체에 종속
- **3NF**: 사업자 속성(`biz_number → ceo_name` 등) 분리, `account_type`에 대한 이행 종속 제거

---

## 5️⃣ 백엔드 대규모 확장 — 인증·현장·평면도·SLAM·텔레메트리·AI웹훅 (2026-04-20)

> **착수 시각**: 2026-04-20 09:37  
> **작업자**: @unknownname-15  
> **목표**: 프론트엔드 기능 확장(현장 관리 / 분석 / 세션 워크플로우)에 대응하는 백엔드 API·모델·서비스 전면 구축. 총 36개 파일 신규/수정.

### ⏱ 2026-04-20 09:37 | 인증 시스템 완성 (JWT + OAuth + 의존성 주입)
- **신규 파일**:
  - `app/core/jwt.py` — `python-jose` 기반 HS256 JWT. `create_access_token(user_id, expires_minutes)` / `decode_access_token(token)`. `settings.JWT_SECRET` + `JWT_ACCESS_EXPIRE_MINUTES` 파라미터화
  - `app/api/auth.py` — 5개 엔드포인트: `POST /auth/signup`(개인/사업자 공용, 사업자 시 `business_profiles` 행 함께 생성) · `POST /auth/login`(아이디+비밀번호 → JWT) · `GET /auth/me`(현재 사용자 조회) · `GET /auth/check-email` · `GET /auth/check-username`(중복 확인)
  - `app/api/oauth.py` — SNS 소셜 로그인 3종. `POST /oauth/google` · `POST /oauth/kakao` · `POST /oauth/naver`. 공통 플로우: 프론트 인가 코드 → provider access_token 교환 → 프로필 조회 → DB 조회/자동 회원가입 → JWT 반환. `httpx.AsyncClient` 비동기 provider 호출
  - `app/dependencies.py` — FastAPI `Depends` 팩토리 모음. `get_db()`(비동기 DB 세션 생성기), `get_current_user()`(Bearer 토큰 검증 후 User ORM 반환), `get_ws_manager()`, `get_rgb_camera()`, `get_thermal_camera()`. 모든 라우터에서 재사용

### ⏱ 2026-04-20 09:37 | 현장(Site) 관리 API + ORM + 스키마
- **신규 파일**:
  - `app/models/site.py` — `sites` 테이블. UUID PK, 현장명/건물유형/주소/점검구분/의뢰유형(B2B/B2C)/의뢰사/연락처/계약기간/세대수/면적/배정팀원 JSONB/메모. `DefectLog` · `Report` 에서 FK 참조 예정. 인덱스: `(status, created_at DESC)` · `(client_type, created_at DESC)`
  - `app/schemas/site.py` — `SiteCreate / SiteUpdate / SiteResponse / SiteListResponse`. `SiteUpdate` 전 필드 Optional(PATCH 부분 업데이트). `SiteListResponse` 에 `total / page / per_page` 페이지네이션 메타 포함
  - `app/api/sites.py` — 5개 엔드포인트: `GET /sites`(필터+검색+페이지네이션) · `GET /sites/{id}` · `POST /sites` · `PATCH /sites/{id}` · `DELETE /sites/{id}`. `get_current_user` 의존성으로 인증 필수

### ⏱ 2026-04-20 09:37 | 평면도 업로드·처리 API + 서비스
- **신규 파일**:
  - `app/models/floorplan.py` — `floorplans` 테이블. 파일명/경로/크기/상태(`uploaded/processing/done/error`) + 추출 결과 JSONB(`walls_json` / `outline_json`)
  - `app/schemas/floorplan.py` — `FloorplanUploadResponse / FloorplanDetail / FloorplanListResponse`
  - `app/api/floorplan.py` — 5개 엔드포인트: `POST /floorplan/upload`(JPG/PDF/DXF, `aiofiles` 비동기 저장, 확장자 화이트리스트 검증) · `POST /floorplan/{id}/process`(OpenCV 벽체 추출 트리거, 백그라운드 태스크) · `GET /floorplan` · `GET /floorplan/{id}` · `DELETE /floorplan/{id}`
  - `app/services/floorplan_processor.py` — OpenCV 순수 이미지 처리. `extract_walls_from_bytes(image_bytes)` 함수. 파이프라인: 그레이스케일 → 이진화 → 방향성 모폴로지(수평/수직 구조 벽 추출) → 컨투어 감지 → 건물 외곽 다각형 추출. DB 독립 순수 함수, 결과를 `{"walls": [...], "outline": [...]}` dict 반환

### ⏱ 2026-04-20 09:37 | SLAM 맵 데이터 API
- **신규 파일**:
  - `app/models/slam_map.py` — `slam_maps` 테이블. 점유 격자(occupancy grid) 메타(해상도/크기/원점) + 이미지 base64 + 드론 위치 JSON
  - `app/schemas/slam_map.py` — `SlamMapCreate / SlamMapUpdate / SlamMapResponse`
  - `app/api/slam.py` — 5개 엔드포인트: `POST /slam`(새 맵 세션) · `GET /slam`(목록, 이미지 제외 메타만) · `GET /slam/{id}`(이미지 포함 상세) · `PATCH /slam/{id}`(실시간 매핑 중 점진 갱신) · `DELETE /slam/{id}`. WS `slam.map_updated` 이벤트 브로드캐스트로 프론트 3D 미니맵 실시간 반영

### ⏱ 2026-04-20 09:37 | 드론 텔레메트리 로그 API
- **신규 파일**:
  - `app/models/telemetry.py` — `telemetry_logs` 테이블. 위치(pos_x/y/z) + 자세(roll/pitch/yaw) + 배터리 + 비행 모드 + 센서 상태. 인덱스: `(created_at DESC)` 타임시리즈 조회 최적화
  - `app/schemas/telemetry.py` — `TelemetryCreate / TelemetryResponse`
  - `app/api/telemetry.py` — 3개 엔드포인트: `POST /telemetry`(저장 + WS `telemetry.update` push) · `GET /telemetry`(목록, 기간 필터) · `GET /telemetry/latest`(최신 1건)

### ⏱ 2026-04-20 09:37 | Python AI 서버 → FastAPI 웹훅 연동
- **신규 파일**:
  - `app/api/ai_webhook.py` — 3개 엔드포인트: `POST /ai/detection`(YOLO/PatchCore 탐지 이벤트 수신 → `DefectLog` DB 저장 + WS `defect.new` 브로드캐스트) · `POST /ai/thermal`(열화상 분석 결과 WS push) · `POST /ai/batch`(다건 탐지 결과 일괄 저장, 단건 `/detection` N회 호출과 동일 효과이나 트랜잭션 단위화)
  - Python AI 프로세스(YOLO/PatchCore/RANSAC)와 FastAPI 백엔드를 분리된 서비스로 유지하면서 이 웹훅으로 연결하는 아키텍처 — AI 서버 재시작이 메인 백엔드에 영향 없음

### ⏱ 2026-04-20 09:37 | 보고서 ORM + 녹화 서비스 + 라우터 통합
- **신규 파일**:
  - `app/models/report.py` — `reports` 테이블. 세션 ID / 현장 FK / LLM 제공자(claude/gemini) / 제목 / 본문 Text / 상태(draft/published) / 생성자 FK
  - `app/schemas/report.py` — `ReportCreate / ReportResponse`
  - `app/services/recording.py` — RGB + Thermal 동시 별도 파일 녹화. `recording_service` 싱글톤. `start_recording()` → `asyncio.Queue` 구독 + `cv2.VideoWriter` mp4 인코딩. `stop_recording()` → writer close + 파일 경로 반환. 저장 경로: `./recordings/YYYYMMDD_HHMMSS_rgb.mp4` / `_thermal.mp4`
  - `app/api/router.py` — 모든 서브 라우터를 `api_router` 로 통합. `main.py` 에서 `app.include_router(api_router, prefix="/api/v1")` 로 마운트. 신규 라우터 포함: `auth / oauth / defects / stream / websocket / report / telemetry / slam / floorplan / ai_webhook / sites`
- **수정 파일**:
  - `app/models/__init__.py` — 신규 5개 모델(`Site / Floorplan / SlamMap / Telemetry / Report`) import 추가 → `Base.metadata` 자동 등록, Alembic 마이그레이션에 반영
  - `app/db/init_db.py` — 신규 모델 임포트 추가
  - `app/main.py` — `api_router` 마운트, lifespan 에 recording_service 포함
  - `app/config.py` — `JWT_SECRET / JWT_ACCESS_EXPIRE_MINUTES / UPLOAD_DIR / RECORDINGS_DIR` 신규 환경변수 추가
  - `app/api/report.py` — 기존 LLM 스트리밍에 Report ORM 저장 로직 추가
  - `app/api/stream.py` · `app/services/camera.py` — 녹화 서비스 연동 주석 추가

### 📐 확장 후 전체 DB 스키마 현황
```
users (기존)          ←─── business_profiles (1:1, 기존)
  │                   ←─── user_term_agreements (M:N, 기존)
  ├── sites           ← 신규. B2B/B2C 현장 관리
  │     └── reports   ← 신규. 현장별 보고서 (FK: site_id optional)
  ├── defect_logs     ← 기존. (FK: site_id 추가 예정)
  ├── floorplans      ← 신규. 평면도 업로드·처리 결과
  ├── slam_maps       ← 신규. SLAM 맵 스냅샷
  └── telemetry_logs  ← 신규. 드론 위치/센서 타임시리즈
```

### 🔗 API 엔드포인트 전체 목록 (신규 추가분)
| 도메인 | 메서드 | 경로 | 역할 |
|--------|--------|------|------|
| Auth | POST | `/api/v1/auth/signup` | 회원가입 |
| Auth | POST | `/api/v1/auth/login` | JWT 로그인 |
| Auth | GET | `/api/v1/auth/me` | 내 정보 |
| OAuth | POST | `/api/v1/oauth/google` | Google OAuth |
| OAuth | POST | `/api/v1/oauth/kakao` | Kakao OAuth |
| OAuth | POST | `/api/v1/oauth/naver` | Naver OAuth |
| Sites | GET/POST | `/api/v1/sites` | 현장 목록/등록 |
| Sites | GET/PATCH/DELETE | `/api/v1/sites/{id}` | 현장 상세/수정/삭제 |
| Floorplan | POST | `/api/v1/floorplan/upload` | 평면도 업로드 |
| Floorplan | POST | `/api/v1/floorplan/{id}/process` | 벽체 추출 트리거 |
| SLAM | CRUD | `/api/v1/slam` | SLAM 맵 관리 |
| Telemetry | CRUD | `/api/v1/telemetry` | 텔레메트리 로그 |
| AI Webhook | POST | `/api/v1/ai/detection` | AI 탐지 이벤트 |
| AI Webhook | POST | `/api/v1/ai/batch` | 다건 탐지 일괄 |

### 📋 잔여 한계 / 향후 작업
- **DB 미연결**: 현재 모든 모델·엔드포인트 코드 완성 상태. Alembic `upgrade head` + AWS RDS 연결이 최종 단계
- **인증 가드**: 현재 일부 엔드포인트(`sites` 등)만 `get_current_user` 의존성. 운영 배포 전 전체 적용 필요
- **파일 저장**: `floorplan/upload` 는 로컬 파일시스템. 운영 시 S3 pre-signed URL 또는 `boto3` 업로드로 전환
- **AI 서버 분리**: `ai_webhook.py` 는 Python AI 프로세스가 HTTP 호출하는 구조 — AI 서버 URL/인증 정책은 별건으로 결정 필요
