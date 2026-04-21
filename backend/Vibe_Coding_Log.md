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

---

## 6️⃣ 멀티테넌트 조직 기반 권한 체계 구현 (2026-04-20)

> **착수 시각**: 2026-04-20 14:00  
> **작업자**: @youminsu0523  
> **목표**: 여러 회사/개인에게 배포될 플랫폼이므로, 조직(Organization) 기반 데이터 격리 + 사용자 권한 관리 체계 전면 구축.  
> **배경**: 기존에는 로그인만 되면 전체 데이터에 접근 가능했음. A회사 사용자가 B회사 데이터를 볼 수 없도록 격리 필요.

### ⏱ 14:00 | 소셜 로그인 에러 수정 (선행 작업)
- **문제 1**: `python-jose` 미설치 → 백엔드 기동 불가 → `ModuleNotFoundError: No module named 'jose'`
  - 해결: `pip install python-jose[cryptography]`
- **문제 2**: OAuth 이메일 중복 → `IntegrityError: duplicate key (email)=(youminsu0523@gmail.com)`
  - 원인: `_find_or_create_oauth_user()` 이메일 조회가 case-sensitive → 기존 계정 못 찾고 INSERT 시도
  - 해결: `func.lower()` 대소문자 무시 조회 + `IntegrityError` catch 후 재조회 (`app/api/oauth.py`)
- **문제 3**: React 18 Strict Mode 이중 실행 → OAuth 인가 코드 2회 전송 → `invalid_grant`
  - 해결: `OAuthCallback.jsx` 에 `useRef` guard 추가하여 1회만 실행

### ⏱ 14:30 | Phase 1 — 백엔드 스키마 + 핵심 의존성
- **모델 변경**:
  - `app/models/site.py` — `organization_id` FK 추가 (멀티테넌트 격리 기준)
  - `app/models/conversation.py` — `organization_id` FK 추가
  - `app/models/organization.py`:
    - `Organization` 모델에 `invite_code` (8자리 영숫자, unique) 추가
    - `OrganizationMember` 모델에 `started_at` (입사일), `ended_at` (퇴사/계약 만료일, nullable) 추가
- **Alembic 마이그레이션**: `alembic.ini` 한글 인코딩 오류 수정 (cp949→UTF-8) + `env.py` 전체 모델 import + 마이그레이션 생성·적용 완료
- **핵심 의존성** (`app/dependencies.py`):
  - `get_current_org_member()` — 현재 사용자의 활성 조직 멤버십 조회. `X-Organization-Id` 헤더로 다중 조직 선택 지원. `ended_at` 만료 체크
  - `get_current_user_with_org()` — 미소속 사용자도 허용 (soft 버전)
  - `require_role("owner", "admin")` — 역할 기반 접근 제어 팩토리

### ⏱ 15:00 | Phase 2 — 백엔드 API 조직 스코핑 (데이터 격리)
- **Sites API** (`app/api/sites.py`): 모든 CRUD에 `Depends(get_current_org_member)` 적용. `list`: `WHERE organization_id = org.id`, `create`: 자동 `organization_id` 설정
- **Defects API** (`app/api/defects.py`): `DefectLog → Site JOIN → Site.organization_id` 경유 필터링. summary/list/get 모두 적용
- **Reports API** (`app/api/report.py`): `Report → Site JOIN → Site.organization_id` 경유 필터링. save/list/get/download/delete 모두 적용
- **Chat API** (`app/api/chat.py`): 대화 생성 시 `organization_id` 자동 설정 + 참여자 같은 조직 검증. 목록 조회 시 `Conversation.organization_id == org.id` 필터

### ⏱ 15:30 | Phase 2 — 인증 응답 확장 + 조직 관리 API
- **인증 응답에 조직 정보 포함**:
  - `app/schemas/user.py` — `OrgBriefResponse` (id, name, role, department, position) 스키마 추가, `UserResponse.organizations` 필드 추가
  - `app/api/auth.py` — `/me`, `login` 응답에 사용자 조직 목록 포함
  - `app/api/oauth.py` — Google/Kakao/Naver 3종 OAuth 응답에도 조직 목록 포함
  - `PATCH /auth/me` — 사용자 이름/전화번호 수정 엔드포인트 추가
- **조직 관리 API 확장** (`app/api/organization.py`):
  - `GET /organizations/unaffiliated-users` — 미소속 사용자 목록 (admin/owner 전용)
  - `POST /organizations/members/assign` — 미소속 사용자 조직 배정 (admin/owner 전용)
  - `POST /organizations/join` — 초대 코드로 조직 가입
  - `PATCH /organizations/members/{user_id}` — 입사일/퇴사일 설정 지원, 퇴사일 경과 시 자동 비활성 처리

### 🔗 신규/변경 API 엔드포인트
| 메서드 | 경로 | 역할 |
|--------|------|------|
| PATCH | `/api/v1/auth/me` | 내 정보 수정 (이름/전화번호) |
| GET | `/api/v1/organizations/unaffiliated-users` | 미소속 사용자 목록 |
| POST | `/api/v1/organizations/members/assign` | 미소속 사용자 배정 |
| POST | `/api/v1/organizations/join` | 초대코드 가입 |

### 📐 설계 결정 사항
- **데이터 격리 방식**: Site에 `organization_id` FK 직접 부여. Defect/Report는 Site FK 경유 간접 필터링 (스키마 최소 변경)
- **다중 조직 허용**: 한 사용자가 여러 조직에 소속 가능 (프리랜서/컨설턴트 시나리오)
- **계약 관리**: `started_at`/`ended_at`으로 입사·퇴사 관리, 퇴사일 경과 시 자동 비활성
- **온보딩 플로우**: Slack/Notion/Jira 패턴 → "조직 생성 / 초대코드 가입 / 관리자 배정 대기" 3가지 선택지

---

## 7️⃣ 프로필 이미지 업로드 기능 구현 (2026-04-20)

> **착수 시각**: 2026-04-20 16:00  
> **작업자**: @youminsu0523  
> **목표**: 사용자 프로필 이미지 업로드/삭제 기능. 회사 특성상 팀원 얼굴 인식이 필요하므로 이니셜 아바타 → 실제 사진 전환 지원. 채팅에서도 프로필 이미지 표시.

### ⏱ 16:00 | User 모델 + 스키마 확장

- **피드백**: "내 정보 수정에서 프로필 이미지를 변경할 수 있게 해줘. 현재는 이름의 앞 두글자를 띄우지만, 회사 특성상 얼굴을 알아야 하는 경우가 있기 때문에 프로필 사진을 넣을 수 있게 해줘. 프로필 사진은 채팅에서도 표현되어야 해."
- **수정 파일**:
  - `app/models/user.py` — `profile_image_url` 컬럼 추가 (String 500, nullable). 업로드된 이미지의 서버 내 경로 저장
  - `app/schemas/user.py` — `UserResponse`에 `profile_image_url: Optional[str] = None` 필드 추가

### ⏱ 16:10 | 프로필 이미지 업로드/삭제 API

- **수정 파일**: `app/api/auth.py`
  - `PUT /auth/me/profile-image` — 프로필 이미지 업로드. `UploadFile` 수신 → content-type 검증(JPEG/PNG/WebP/GIF) → 5MB 크기 제한 → UUID 파일명으로 `./uploads/profiles/` 저장 → 기존 파일 삭제 → DB `profile_image_url` 갱신
  - `DELETE /auth/me/profile-image` — 프로필 이미지 삭제. 파일시스템 파일 제거 + DB null 처리
  - 기존 `signup`, `login`, `get_me`, `update_me` 응답에 `profile_image_url` 포함하도록 갱신
- **파일 업로드 패턴**: 기존 `floorplan.py` 패턴 참고 — `aiofiles` 비동기 파일 쓰기, `uuid` 파일명, 확장자 화이트리스트

### ⏱ 16:20 | 정적 파일 서빙 + DB 마이그레이션

- **수정 파일**: `app/main.py` — `FastAPI.mount("/uploads", StaticFiles(...))` 추가. 업로드된 프로필 이미지를 `/uploads/profiles/{filename}` 경로로 HTTP 제공
- **신규 파일**: `alembic/versions/b3f1a2c4e5d6_add_profile_image_url_to_users.py` — `users.profile_image_url` 컬럼 추가 마이그레이션

### ⏱ 16:30 | 마이그레이션 적용 및 오류 해결

- **문제**: User 모델에 `profile_image_url` 컬럼 추가 후 서버 재시작 시, SQLAlchemy가 `SELECT users.profile_image_url`을 시도하지만 DB에 해당 컬럼 미존재 → 모든 인증 관련 쿼리 실패 (멤버 관리 페이지 "데이터를 불러오지 못했습니다" 에러)
- **원인**: `Base.metadata.create_all()`은 새 테이블만 생성하고 기존 테이블에 컬럼을 추가하지 않음
- **해결**: `PYTHONPATH=. alembic upgrade head` 실행 → `a957fb9970a3 → b3f1a2c4e5d6` 마이그레이션 성공 적용

### 🔗 신규 API 엔드포인트
| 메서드 | 경로 | 역할 |
|--------|------|------|
| PUT | `/api/v1/auth/me/profile-image` | 프로필 이미지 업로드 (교체) |
| DELETE | `/api/v1/auth/me/profile-image` | 프로필 이미지 삭제 |

### 📐 설계 결정 사항
- **저장 방식**: 로컬 파일시스템 (`./uploads/profiles/`) + StaticFiles 서빙. 운영 배포 시 Cloudflare R2 presigned URL로 전환 예정 (기존 `project_file_storage_r2.md` 메모리 참조)
- **파일명 전략**: UUID v4 + 원본 확장자. 중복/충돌 방지 + URL 추측 불가
- **기존 파일 정리**: 새 이미지 업로드 시 이전 파일 자동 삭제 (디스크 낭비 방지)
- **크기 제한**: 5MB. 프로필 사진 용도로 충분, 서버 부담 최소화

---

## 📝 세션 추가 정보 (2026-04-20 @Hijin)

- 작성자 (Who): @Hijin554
- 작성 일자 (When): 2026-04-20
- 목표 기능 (Objective): 2차 프로젝트 Phase 2 — 학습 완료된 AI 3개 모델을 실제 서빙하는 파이프라인 + `/api/v1/detect` REST + `/api/v1/ws/stream` WebSocket (드롭 큐) 구축
- 작업 브랜치/환경: `Hijin`

### 1️⃣ 초기 프롬프트 (Initial Prompt)
> AeroInspect 2차 프로젝트 — FastAPI 백엔드 구축 요청(v3). 학습 완료된 YOLOv8s × 2 + ResNet50 × 1 가중치를 실제로 로드·추론하는 파이프라인을 기존 `backend/` 구조에 통합.

### 2️⃣ 계획(Plan) 단계 피드백

- **피드백 1** (통합 vs 신규):
  > "aeroinspect_backend/ 새로 만들지 말고 기존 backend/ 에 통합해줘. 먼저 기존 구조 꼼꼼히 읽고 delta 계획부터 보여줘."
  → 해결: 기존 [app/services/yolo_inference.py](app/services/yolo_inference.py), [core/ws_manager.py](app/core/ws_manager.py), [models/defect.py](app/models/defect.py) 등 15개 파일 분석 → 수정/신규/제외 파일 delta 계획서 작성 → 승인 후 구현 진입

- **피드백 2** (bbox 좌표 정책):
  > "API 응답은 bbox_xyxy(픽셀) 유지. DB 저장 시에만 xywhn 변환. 이미지 W/H가 필요하니 프레임 shape을 결과에 같이 실어서 내려줘."
  → 해결: `DetectionResult.image_shape: {width, height}` 필드 추가, `xyxy_to_xywhn(xyxy, w, h)` 헬퍼 별도 함수로 분리 → [tests/test_inference_pipeline.py](tests/test_inference_pipeline.py) 회귀 테스트 5건

- **피드백 3** (shim 패턴):
  > "모델 로드는 절대 중복 금지 — inference_pipeline.service가 유일한 싱글톤. yolo_inference.yolo_service는 내부적으로 참조만 해."
  → 해결: [yolo_inference.py](app/services/yolo_inference.py) 를 40줄 shim으로 재작성. 기존 호출자([defect_processor.py](app/services/defect_processor.py), [dependencies.py](app/dependencies.py)) 무수정으로 호환

- **피드백 4** (WS 이중 브로드캐스트):
  > "신규 /ws/stream 탐지 결과는 기존 ws_manager.broadcast('defects', ...)로도 Push해줘. 두 WS 채널 분리돼 있지만 결과는 양쪽 다 흐르게."
  → 해결: [core/stream_inference.py](app/core/stream_inference.py) 에서 `stream` 채널(신규 포맷) + `defects` 채널(레거시 `defect.new` 이벤트) 동시 브로드캐스트

- **피드백 5** (Alembic 베이스라인):
  > "0001_baseline.py 수동 작성은 기존 스키마와 drift 날 위험. 0002만 새로 작성하고 첫 배포 때 alembic stamp head 돌리는 절차로."
  → 해결: [alembic/versions/0002_defect_class_display.py](alembic/versions/0002_defect_class_display.py) 하나만 생성 (`down_revision=None`). README에 `alembic stamp 0002_defect_class_display` 절차 명시

### 3️⃣ 구현 핵심 아키텍처

#### 3-모델 추론 파이프라인 (싱글톤)
```
InferencePipeline.load_models()
  ├── YOLO(yolov8s_crack_moisture_best.pt)   — Crack, Moisture (nc=2)
  ├── YOLO(yolov8s_delamination_best.pt)     — delamination (nc=1)
  └── ResNet50(resnet50_wallpaper_best.pt)   — 19 classes (good=Burst 포함)
```
- 체크포인트 `class_names` 리스트를 하드코딩 `WALLPAPER_CLASSES`와 `assert` 검증 — 학습·서빙 클래스 순서 미스매치 사전 차단
- 입력 타입 4종 지원: `bytes / numpy.ndarray / PIL.Image / str(경로)`
- 블로킹 추론은 전부 `asyncio.to_thread()` 로 스레드 풀 위임

#### ⚠️ `good` 클래스 특수 처리
데이터셋 폴더명이 `good`으로 지어졌으나 실제 내용은 "터짐(Burst)" 하자 이미지. 가중치에 baked-in 되어 있어 내부명은 유지하되:
```python
CLASS_DISPLAY_MAP = {
    ...
    "good": ("Burst", "터짐"),  # ⚠️ 실제 의미는 '터짐'
}
WALLPAPER_SEVERE_CLASSES = {"Mold", "Damage", "Exploded", "Defective_Joint", "good"}
# → severity MED로 격상 (LOW 아님)
```
"정상=하자없음"으로 필터링하는 로직은 코드 어디에도 넣지 않음.

#### severity 자동 계산 규칙 ([inference_pipeline.py](app/services/inference_pipeline.py))
```
yolo_thermal/delam 탐지 있음               → HIGH
벽지 is_confident & top1 ∈ SEVERE classes  → MED
벽지 is_confident & 그 외                   → LOW
그 외 (신뢰도 부족)                         → null (판단 보류)
```

#### WebSocket 드롭 큐 + 프레임 스킵 ([core/stream_inference.py](app/core/stream_inference.py))
드론 IRC-256CA 스트림(15~30 fps) vs CPU/GPU 추론(80~150 ms/frame) 불일치 → 모든 프레임 처리 불가. 다음 패턴으로 해결:
```python
self._queue: asyncio.Queue = asyncio.Queue(maxsize=1)

def submit(frame):
    if self._submitted_count % FRAME_SKIP != 0: return  # 3프레임 중 1개만
    try: self._queue.put_nowait(QueuedFrame(frame, ...))
    except asyncio.QueueFull: self._dropped_count += 1   # 바쁘면 그냥 버림
```
워커 태스크는 별도 `asyncio.create_task`로 영구 실행, main.py lifespan에서 `start()/stop()`.

#### DB 스키마 확장 ([models/defect.py](app/models/defect.py), [alembic/versions/0002_defect_class_display.py](alembic/versions/0002_defect_class_display.py))
기존 `defect_logs` 스키마 유지하면서 4컬럼 추가 + 레거시 A-E 컬럼 NULLABLE 완화:
```
+ defect_source ENUM('yolo_thermal','yolo_delam','wallpaper')
+ defect_class VARCHAR(50)                 -- 모델 내부명 (예: 'good', 'Crack')
+ defect_class_display_en VARCHAR(80)      -- 프론트용 (예: 'Burst')
+ defect_class_display_ko VARCHAR(80)      -- 프론트용 (예: '터짐')
~ area/category_code/defect_type: NOT NULL → NULLABLE  (신규 클래스 중 A-E 매핑 없는 케이스 대비)
```

### 4️⃣ 신규/수정 파일 목록

**신규 (11개)**:
- [app/schemas/detection.py](app/schemas/detection.py) — `DetectionResult`, `YoloDetection`, `WallpaperPrediction`, `HealthResponse` Pydantic 스키마
- [app/services/defect_taxonomy.py](app/services/defect_taxonomy.py) — `WALLPAPER_CLASSES`(19), `CLASS_DISPLAY_MAP`, `YOLO_DISPLAY_MAP`, `LEGACY_MAP_THERMAL/WALLPAPER`, `map_to_legacy()`, `xyxy_to_xywhn()`
- [app/services/wallpaper_classifier.py](app/services/wallpaper_classifier.py) — ResNet50 19-class. 체크포인트 `class_names` assert 검증. top1+top3 softmax
- [app/services/inference_pipeline.py](app/services/inference_pipeline.py) — 싱글톤 오케스트레이터. `detect_defects()`, `detect_defects_async()`, `detect_defects_legacy()` shim용
- [app/core/stream_inference.py](app/core/stream_inference.py) — 드롭 큐 워커 + `stream`/`defects` 양방향 브로드캐스트
- [app/api/detect.py](app/api/detect.py) — `POST /api/v1/detect` multipart 단건, `POST /api/v1/detect/batch` 최대 10장
- [app/api/ws_stream.py](app/api/ws_stream.py) — `WS /api/v1/ws/stream` 바이너리 JPEG 수신 + `asyncio.to_thread(cv2.imdecode)`
- [alembic/versions/0002_defect_class_display.py](alembic/versions/0002_defect_class_display.py) — 4컬럼 추가 + NULLABLE 완화 마이그레이션
- [tests/test_inference_pipeline.py](tests/test_inference_pipeline.py) — 18개 테스트 (xyxy→xywhn 5, taxonomy 8, /health & /detect 5)
- [pytest.ini](pytest.ini) — `asyncio_mode=auto`
- [README.md](README.md) — 3-모델 표, WebSocket 프로토콜, React 예제, 마이그레이션 절차, **동작 확인 체크리스트**

**수정 (10개)**:
- [app/services/yolo_inference.py](app/services/yolo_inference.py) — **전체 재작성**: 40줄 shim (`pipeline.load_models()` 위임, `detect_defects_legacy()` 반환)
- [app/config.py](app/config.py) — `AEROINSPECT_WEIGHTS_DIR`, `YOLO_THERMAL_WEIGHTS`, `YOLO_DELAM_WEIGHTS`, `WALLPAPER_WEIGHTS`, `YOLO_CONF_THRESHOLD=0.25`, `WALLPAPER_CONF_THRESHOLD=0.4`, `FRAME_SKIP=3`, `DEVICE=auto` 추가
- [.env.example](.env.example), [.env](.env) — 위 키 전부 반영
- [app/models/defect.py](app/models/defect.py) — 4 컬럼 추가, 레거시 컬럼 NULLABLE
- [app/schemas/defect.py](app/schemas/defect.py) — `DefectLogCreate/Response`에 4 필드 + 레거시 A-E Optional화
- [app/api/defects.py](app/api/defects.py) — `GET /api/v1/defects/recent` 추가, `POST /defects`에 4 필드 DB 저장
- [app/api/ai_webhook.py](app/api/ai_webhook.py) — 웹훅도 4 필드 저장
- [app/api/router.py](app/api/router.py) — `detect`, `ws_stream` 라우터 등록
- [app/main.py](app/main.py) — lifespan에 `stream_inference_worker.start()/stop()` + `/health` 확장 (`device/models_loaded/wallpaper_classes_count/stream_worker_running/frame_skip`)
- [requirements.txt](requirements.txt) — `torch>=2.1`, `ultralytics>=8.3.0` 핀 + `pytest`, `pytest-asyncio`
- [alembic.ini](alembic.ini), [alembic/env.py](alembic/env.py) — Python 3.14 cp949 로케일 이슈 대응: 한글 주석 제거 + `sys.path` 수동 삽입

### 5️⃣ 실제 검증 결과

- **pytest**: 18/18 통과 (`good=Burst` 매핑, xyxy→xywhn 회귀 등 전부)
- **서버 기동 로그**:
  ```
  [Pipeline] YOLO thermal 로드: yolov8s_crack_moisture_best.pt
  [Pipeline] YOLO delam 로드:   yolov8s_delamination_best.pt
  [Wallpaper] ResNet50 로드 완료: device=cpu, val_acc=0.5434, classes=19
  [Pipeline] 3-모델 로드 완료
  [StreamInfer] 워커 시작 (frame_skip=3)
  ```
- **`/health`** 응답: `models_loaded` 3개 전부 `true`, `wallpaper_classes_count=19`, `stream_worker_running=true`
- **`/api/v1/detect`** 실제 이미지 업로드 테스트 (Roboflow 샘플):
  ```
  top1: Damage (훼손) / conf 97.97% / severity=MED / has_defect=true
  ```
  → 클래스 표시명 매핑, severity 격상 규칙, image_shape 기록 모두 정상

### 📋 잔여 한계 / 향후 작업 (추가분)
- **GPU 추론**: 현재 T4 없이 CPU로 돌려 한 장당 5~15초. 프로덕션 배포 시 GPU 인스턴스 + `DEVICE=cuda` 로 전환 필요
- **싱글 워커 제한**: `stream_inference_worker`는 프로세스 내 싱글톤이라 gunicorn multi-worker 구동 불가. 다중 워커 필요 시 Redis pub/sub 기반 리팩터
- **드론 좌표**: MAVLink/LiDAR 연동 전이라 `lidar_x/y/z`는 당분간 NULL. TF 연동 완료 후 기존 컬럼에 채울 예정
- **벽지 분류 정확도 0.54**: `WALLPAPER_CONF_THRESHOLD=0.4`로 보수 필터링. 데이터 추가 수집 후 fine-tuning 필요
