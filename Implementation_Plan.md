# Implementation Plan

## 프로젝트 개요
- **프로젝트명**: AeroInspect AI — 드론 기반 아파트 사전 점검 자동화 플랫폼
- **팀원**: @youminsu0523 (MS), @Hijin554 (Hijin), @unknownName-15 (SH), @Antigravity (인프라)

---

## 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│  Client Browser (React SPA)                                         │
│  ├── Landing (/)          — 마케팅 페이지 (Hero/Features/Cases/CTA) │
│  ├── Auth (/login, /signup, /find-account, /oauth/:provider/callback)│
│  ├── Employee Hub (/employee/*) — 사무실 허브 (KPI/채팅/현장/리포트) │
│  ├── Session (/session/*) — 점검 워크플로우 (Setup→Level→Modeling)   │
│  ├── Dashboard (/dashboard) — 실시간 드론 관제 (HUD/3D/영상/AI)     │
│  ├── React Three Fiber    — 3D 건물·드론·마커·비행경로 시각화        │
│  ├── Zustand (9 stores)   — auth/chat/defect/drone/notification/     │
│  │                          preModel/reports/session/sites            │
│  └── REST API (axios) + WebSocket 연동                               │
├─────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend (Python 비동기)                                     │
│  ├── api/ (17 라우터)     — REST 엔드포인트                          │
│  │   auth, oauth, chat, defects, detect, sites, report, telemetry,  │
│  │   stream, organization, notifications, ai_webhook, coverage,     │
│  │   floorplan, slam, websocket, ws_stream                          │
│  ├── core/                — JWT, Security(bcrypt), Middleware(CORS/  │
│  │                          RequestID), Metrics(Prometheus),         │
│  │                          WebSocket Manager, Streaming,            │
│  │                          StreamInferenceWorker                    │
│  ├── services/ (25 모듈)  — 비즈니스 로직                           │
│  │   inference_pipeline (3-model), inference_pipeline_20 (20종 ONNX),│
│  │   onnx_inference(YOLO/ResNet/UNet/PatchCore), wallpaper_classifier│
│  │   yolo_inference, alignment_detector(KCS기준), insulation_detector│
│  │   ensemble, temporal_filter, defect_processor, defect_taxonomy,  │
│  │   lidar, thermal, camera, recording, test_stream(1,053줄),       │
│  │   floorplan_processor(OpenCV), llm_report, image_storage,        │
│  │   email_service, notification_service, push_notifications,       │
│  │   telemetry_cache, anomaly_detection                             │
│  ├── models/ (18 ORM)    — SQLAlchemy                               │
│  │   User, Organization, OrganizationMember, Site, Defect, Report,  │
│  │   Conversation, ConversationMember, Message, Notification,       │
│  │   DeviceToken, Floorplan, SlamMap, Telemetry, BusinessProfile,   │
│  │   Department, Term, UserTermAgreement                            │
│  ├── schemas/ (14 세트)   — Pydantic 요청/응답                      │
│  └── db/                  — 데이터베이스 연결 + Alembic 마이그레이션 │
├─────────────────────────────────────────────────────────────────────┤
│  PostgreSQL        │  Redis Pub/Sub     │  ONNX Runtime              │
│  (전체 영속 저장소)│  (WS 브로커/캐시)  │  (20종 결함 분류 추론)     │
└─────────────────────────────────────────────────────────────────────┘
```

### 데이터 흐름 (Data Journey)
```
1. 사용자 로그인 → JWT(HS256) + Refresh Token 발급 (+ OAuth Google/Kakao/Naver)
   → 조직 biz_number 매칭 → 멀티테넌트 접근 제어
2. 현장 CRUD → Site 모델(20+ 컬럼, JSONB assigned_members/recordings) → PostgreSQL
3. 세션 워크플로우 → SessionSetup(현장/운용자/날짜) → SessionLevel(L1 CAD/L2 평면도/L3 자율비행)
   → SessionModeling(mockModeling 6~12초) → Dashboard
4. 드론 비행 → 텔레메트리 POST → telemetry_cache O(1) 메모리 갱신
   → WS "telemetry" 브로드캐스트 → 3D DroneMarker(비행경로 500점 폴리라인)
5. 비디오 스트리밍 → WS /ws/stream 바이너리 JPEG → StreamInferenceWorker(드롭큐+프레임스킵)
   → 3-Model / 20종 ONNX 추론 → WS "stream"+"defects" 동시 브로드캐스트
6. 20종 결함 분류 → M1(균열 2-Stage) + M2(표면 2-Stage) + M3(바닥/창호 2-Stage)
   + M4(열화상 U-Net) + M5(세그멘테이션+기하학 RANSAC) + M6(PatchCore 앙상블)
   → cross_model_nms + temporal_filter → Defect DB 저장
7. 벽지 분류 → 이중 게이트(conf≥0.35 AND margin≥0.15) → 오탐 차단
8. LiDAR → telemetry_cache fresh pose + lidar_service → 3D 월드 좌표 주입
9. 점검 커버리지 → 텔레메트리 convex hull(Andrew's monotone chain) → Shoelace 면적
   → covered_area / supplied_area ratio + 미점검 구역 hull 폴리곤
10. 리포트 → LLM 기반 요약 → PDF(react-pdf, Noto Sans KR) / Excel(SheetJS/ExcelJS 양식 주입)
11. 채팅 → REST + WS 브로드캐스트 → DM 중복 방지(aliased 자기조인)
12. 알림 → 10종 카테고리 → NotificationDropdown + FCM/APNs 푸시(noop/fcm/apns)
```

### API 엔드포인트 전체 맵 (17 라우터, 60+ 엔드포인트)
| 라우터 | prefix | 담당자 | 주요 엔드포인트 |
|--------|--------|--------|----------------|
| auth | `/api/v1/auth` | @youminsu0523, @Hijin554 | signup, login, me, refresh, check-email, check-username |
| oauth | `/api/v1/oauth` | @youminsu0523 | google, kakao, naver (code→token→userinfo→JWT) |
| sites | `/api/v1/sites` | @youminsu0523 | CRUD + 필터(status/building_type/client_type) + 페이지네이션 |
| defects | `/api/v1/defects` | @youminsu0523, @Hijin554 | CRUD + image_storage 연동 + DELETE 파일 클린업 |
| detect | `/api/v1/detect` | @Hijin554 | POST 단건/batch(10장) multipart 3-모델 추론 |
| stream | `/api/v1/stream` | @youminsu0523 | RGB/Thermal/Blend MJPEG + 녹화 + 테스트 모드 14개 |
| report | `/api/v1/report` | @youminsu0523, @Hijin554 | LLM 생성 + 저장/조회/다운로드(마크다운)/삭제 |
| chat | `/api/v1/chat` | @youminsu0523 | conversations CRUD + messages + read/unread + leave |
| organization | `/api/v1/organizations` | @youminsu0523 | my/members/create/invite/modify/remove + 슈퍼어드민 all-orgs/departments |
| telemetry | `/api/v1/telemetry` | @Hijin554 | POST(ROS2/MAVLink→WS Push) + GET 목록/최신 |
| ai_webhook | `/api/v1/ai` | @Hijin554 | detection/thermal/batch → DB + WS 브로드캐스트 |
| notifications | `/api/v1/notifications` | @Hijin554 | CRUD + tokens 등록/삭제 + push test |
| coverage | `/api/v1/coverage` | @Hijin554 | site별 convex hull 커버리지 산출 |
| floorplan | `/api/v1/floorplan` | @Hijin554 | 업로드/처리/분석/목록/상세/삭제/calibrate |
| slam | `/api/v1/slam` | @Hijin554 | CRUD + 실시간 갱신(WS Push) |
| websocket | WS | @Hijin554 | 실시간 이벤트 (telemetry/defects/stream/thermal/camera) |
| ws_stream | WS `/ws/stream` | @Hijin554 | 바이너리 JPEG 프레임 수신 → 추론 워커 |

---

## 구현 계획 (단계별 상세)

### Phase 1. 프로젝트 초기화 & 인프라 (260413~260414) ✅
- **담당**: @youminsu0523, @Antigravity
- **파일**: `team_project_rules.md` (454줄), `.clauderules`, `.geminirules`, `Task.md`, `Implementation_Plan.md`
- **상세**:
  - 팀 협업 가이드라인 15개 섹션 (멘토 모드, Better Comment, Scope Containment, 리팩토링, 검수 체크리스트 등)
  - 백엔드/프론트엔드 개별 문서 구조 분화
  - Notion 자동 동기화 파이프라인 (스크린샷 캡쳐 Pillow/PowerShell 폴백)

### Phase 2. FastAPI + React 기초 (260414) ✅
- **담당**: @youminsu0523
- **상세**: FastAPI main.py(lifespan, CORS, health), requirements.txt, React Header(텔레메트리+하자카운트), DefectPanel(필터+리스트)

### Phase 3. 랜딩 페이지 (260415) ✅
- **담당**: @youminsu0523
- **상세**: 95개 파일, 이미지 에셋 80개, 7개 랜딩 섹션 컴포넌트, ContactModal(국세청 시뮬), IntersectionObserver Reveal, 스크롤 부드러운 이동

### Phase 4. 프론트엔드 인증 + 국세청 API (260416) ✅
- **담당**: @youminsu0523
- **상세**: Signup(784줄 개인/사업자 탭, 국세청 실API 연동), Login(254줄 소셜3종), FindAccount(320줄 탭+쿼리파라미터), businessVerifyApi(odcloud.kr Vite 프록시)

### Phase 5. 풀스택 인증 + 대시보드 HUD (260416) ✅
- **담당**: @youminsu0523
- **상세**: 백엔드(auth API 3개, User/BusinessProfile/Term/UserTermAgreement 4모델, bcrypt), 프론트엔드(DashboardTopBar HUD, DronesPanel 2드론, Dashboard 풀스크린 관제, DRONE_CAMERA_MAP)

### Phase 6. 세션 워크플로우 + 3D 시각화 (260416) ✅
- **담당**: @youminsu0523
- **상세**: 23개 파일. SessionSetup→SessionLevel→SessionModeling 3단계, sessionStore(Zustand+persist 30+필드), mockModeling(L1~L3 시뮬레이터), 세션 컴포넌트 5개, DroneMarker(cone+프로펠러+Billboard+yaw+색상), MissionControl

### Phase 7. 직원 전용 사무실 허브 (260416) ✅
- **담당**: @youminsu0523
- **상세**: EmployeeLanding 749줄(KPI/일정/알림/팀원/최근활동/세션카드, MOCK_* 목업+실데이터 혼용)

### Phase 8. 드론 리포트 관리 시스템 (260416) ✅
- **담당**: @youminsu0523
- **상세**: 36개 파일. ReportEditor(AI 공종 제안), AddDefectDialog, ExcelExport(SheetJS), PdfExport(react-pdf Noto Sans KR), LocationMapEditor, TradeSelect, reportsStore, preModelStore, trades.js(12종 공종), PreWork(사전작업), CI Vibe Log 검증

### Phase 9. 백엔드 텔레메트리 + AI 웹훅 + SLAM + 평면도 (260416) ✅
- **담당**: @Hijin554
- **상세**: 17개 파일 +1,191줄. ai_webhook(단건/열화상/배치+WS), telemetry(POST WS Push+GET), slam(CRUD 5개+WS), floorplan(업로드 aiofiles+OpenCV+CRUD), report(저장/조회/다운로드), DB 모델 4개+스키마 4세트, router 등록

### Phase 10. 드론 미션 제어 + 녹화 + 평면도 OpenCV + 리포트 내보내기 (260417) ✅
- **담당**: @youminsu0523
- **상세**: 50개 파일. recording.py(RGB+Thermal mp4, _CameraRecorder), floorplan_processor.py(OpenCV 벽체추출 파이프라인), stream.py(MJPEG+녹화 CRUD), ExcelPreviewModal, PdfPreviewModal, templateExport.js(ExcelJS 양식 주입)

### Phase 11. DroneMarker 비행 경로 + 풀스택 인증 완성 (260417) ✅
- **담당**: @youminsu0523
- **상세**: DroneMarker 비행경로 폴리라인(500점, dashed, 2D 투영 그림자). auth login/me + oauth Google/Kakao/Naver 3종 + jwt create/decode + authStore + OAuthCallback

### Phase 12. 프론트엔드 인증 UI & 모바일 반응형 (260417~260420) ✅
- **담당**: @unknownName-15
- **상세**: Remix Icon CDN, LandingHeader 모바일 햄버거 메뉴(외부클릭/aria/드롭다운), 뒤로가기 navigate(-1)+아이콘 통일, 포커스 링 전역 제거

### Phase 13. 현장 관리 시스템 (260418) ✅
- **담당**: @youminsu0523
- **상세**: 22개 파일 +2,822줄. Site 모델(20+ 컬럼, JSONB, Enum), API 5개(필터+페이지네이션), sitesApi(시드 5건), SiteManagement(히어로+KPI+검색+필터+테이블), SiteDetail(미니KPI+2컬럼+3탭), Analytics, TrendReport, WeeklyReport

### Phase 14. 3-모델 추론 + 스트림 워커 + REST/WS 추론 (260420) ✅
- **담당**: @Hijin554
- **상세**: 23개 파일 +2,139줄. InferencePipeline(460줄, YOLO crack_moisture+delamination+ResNet50 wallpaper), WallpaperClassifier(188줄, 19클래스), defect_taxonomy(188줄, 19클래스 매핑), StreamInferenceWorker(239줄, 드롭큐+to_thread+이중 WS 브로드캐스트), detect REST(단건/batch), ws_stream(바이너리 JPEG), 테스트 193줄

### Phase 15. 풀스택 채팅 + 알림 + 조직 관리 (260420) ✅
- **담당**: @youminsu0523
- **상세**: 48개 파일 +4,313줄. DB 모델 5개, API 4라우터(chat/notifications/organization/auth), 채팅 UI 9컴포넌트, 알림 드롭다운+10종 카테고리, email/notification 서비스, store/api 6세트

### Phase 16. LiDAR 3D + 이미지 저장소 + 로깅 + 이중 게이트 (260421) ✅
- **담당**: @Hijin554
- **상세**: 24개 파일. telemetry_cache(DronePose O(1)), image_storage(Base64→파일), structlog JSON, RequestIDMiddleware, LiDAR 3D 좌표 주입, 이중 게이트(conf≥0.35 AND margin≥0.15), 테스트 3개

### Phase 17. 결함 로깅 + 커버리지 + 모니터링 스키마 (260422) ✅
- **담당**: @Hijin554
- **상세**: coverage.py(convex hull+Shoelace), sweep_wallpaper_thresholds.py(격자탐색), monitoring.py(StreamStats/CoverageResponse), 하자 삭제 파일 클린업, site_id FK 마이그레이션, 테스트 6개

### Phase 18. Refresh Token + Prometheus + Redis WS + Push (260422) ✅
- **담당**: @Hijin554
- **상세**: 26개 파일 +1,532줄. JWT refresh(type 분리), PrometheusMiddleware(HTTP+커스텀 6메트릭), RedisConnectionManager(pub/sub 팩토리), push_notifications(FCM/APNs 스켈레톤), device_tokens 모델, 인증 가드 11+엔드포인트, calibrate, 테스트 6개

### Phase 19. 20종 결함 분류 ONNX 파이프라인 (260422) ✅
- **담당**: @youminsu0523
- **상세**: 41개 파일 +6,392줄. ONNX 4클래스(YoloDetector/ResNetClassifier/UNetSegmenter/PatchCoreDetector), 20종 파이프라인(M1~M6 Tier 실행), ensemble(cross_model_nms+PatchCore 승격), alignment_detector(647줄 KCS기준), insulation_detector(237줄 4종), temporal_filter(120줄), 학습 스크립트 15+개

### Phase 20. 테스트 스트림 + 대시보드 인프라 (260424) ✅
- **담당**: @youminsu0523
- **상세**: 33개 파일 +2,787줄. TestStreamService(1,053줄), 테스트 모드 14엔드포인트, TestModeBar(319줄), floorplan_quality(7항목), API localStorage→axios 전환

### Phase 21. 조직/멤버 + 채팅 고도화 (260424) ✅
- **담당**: @youminsu0523
- **상세**: 15개 파일. DM 중복방지, 대화방 나가기, 슈퍼어드민 전체조직/부서, AdminMembers 4단계 워크플로우

---

## 향후 계획 (미완료)

### Phase 22. DB 실가동 & 배포 준비
- [ ] PostgreSQL 실DB 연결 (AWS 프리티어 → 최종 단계)
- [ ] Alembic 마이그레이션 실행
- [ ] Redis 서버 세팅
- [ ] .env 환경 변수 정비, CORS 최종 점검

### Phase 23. 파일 스토리지 연동
- [ ] Cloudflare R2 Presigned URL (도면/드론 영상)

### Phase 24. 점검 면적 자동 산출
- [ ] 드론 비행 후 가용면적 자동 계산 + 커버리지율 + 미점검 구역 리포트

### Phase 25. MOCK_* → 실API 교체
- [x] **(2026-05-03)** EmployeeLanding `MOCK_TODAY_SCHEDULE` / `MOCK_TEAM_MEMBERS` / `MOCK_MONTHLY_KPI` / `MOCK_RECENT_ACTIVITIES` 4개 const 삭제 + 백엔드 `/api/v1/employee/{schedule/today, kpi/monthly, activities}` + `/organizations/members` 병렬 fetch로 완전 교체
- [x] **(2026-05-03)** mockup 팀원명(가짜 5명) → 실제 팀(백승희/오희진/유민수)로 통일 (mockTrendData / chatConstants / SiteFormModal / EmployeeLanding)
- [ ] ProtectedEmployeeLayout 인증 가드

### Phase 26. 통합 테스트 & QA
- [ ] 풀스택 E2E, 반응형 검증, 보안 점검, 접근성(a11y) 감사

### Phase 27. 배포 직전 안정화 (2026-05-03 ~ 2026-05-06)
- [x] **Swagger Phase 1~3** — HTTPBearer/AIWebhookSecret 보안 스키마, 17 tags_metadata, persistAuthorization, 공통 401/403 responses, schema example 4종
- [x] **운영 보안 가드** — `APP_ENV=production` 기준으로 config.py(placeholder secret 차단) / init_db.py(create_all 자동 스킵, alembic 책임 분리) / seed_demo_data.py(시드 abort) 3중 가드
- [x] **InspectionSchedule 모델 + alembic migration `i2c3d4e5f6a7`** — DB 19테이블/12리비전
- [x] **`/api/v1/employee` 라우터 신규** — schedule/today + kpi/monthly + activities (조직 단위 격리)
- [x] **`scripts/seed_demo_data.py` 신설** — 조직/부서/사용자(백승희·오희진)/현장 8/하자 25~60건/보고서 3~5건/오늘 일정 3건/알림. idempotent + APP_ENV 가드 + `--reset` / `--force-prod`
- [x] **문서 동기화 (1차)** — API 명세서 v1.1 → v1.2, ERD v1.0 → v1.1, Vibe_Coding_Log backend R19~R25 / frontend R10~R12 append
- [x] **문서 양식 정정 (R26 후속)** — tasks 문서 부록을 본문 인라인으로 재배치 + 파일명 rename + 팀명 `다마코더 → AeroInspect` 일괄 + 가이드 3종 문서이력 위치 정정 + `CHANGES_2026-05-03.md` 신설
- [x] **alembic upgrade head + seed_demo_data 실 적용** — 분기 head 병합(`89b53c16de85`) + 누락 컬럼 10건 `ADD COLUMN IF NOT EXISTS` 보정 + 시드 결과: sites=8 / defects=315 / reports=12 / schedules=3 (잠실 리센츠 14:00 KST 백승희 검증)
- [x] **(2026-05-06)** 브라우저 탭 favicon 일원화 — 누락된 `/drone-icon.svg` 참조 제거, `frontend/public/`에 favicon.ico(16/32/48 다중 entry) + favicon-{16,32,192,512}.png + apple-touch-icon.png(180×180) 신규 + `index.html` link 5줄 명시 등록. 로고 알파 row 스캔으로 graphic/text 자동 분리 → 텍스트 제외 그래픽만 favicon 화
- [x] **(2026-05-06, R19 후속)** favicon 흰 원 배경 추가 + 로고 확대 — 다크 탭/작은 사이즈 시인성 보강. 512×512 master `FillEllipse` 흰 원 + inscribed 사각형 92% 기준(333×312) 로고 fit + 모든 ico/PNG 갱신

---

## Revision History

### v5.2_260506 (작성자: @youminsu0523 / branch: main)
- Phase 27 추가 완료 항목: 브라우저 탭 favicon 자체 로고 적용 (frontend R19) — ico/PNG 다중 등록 + 알파 row 스캔으로 graphic/text 자동 분리 + 정사각 캔버스 가운데 배치. 배포 사이트 globe 기본 favicon 이슈 해소.
- Phase 27 추가 완료 항목: favicon 흰 원 배경 + 로고 확대 (frontend R23, R19 후속) — 다크 탭/작은 사이즈에서 어두운 푸른빛이 묻히는 이슈 해결. 512×512 master 흰 원 fillEllipse + inscribed 사각형 92% 기준 로고 재배치.

### v5.1_260503 (작성자: @youminsu0523 / branch: MS)
- Phase 27 추가 완료 항목: alembic 분기 head 병합(`89b53c16de85`) + `defect_logs` 누락 컬럼 ALTER 보정 + `seed_demo_data --reset` 실행 (sites=8/defects=315/reports=12/schedules=3). tasks 문서 양식 정정 (API v1.2/ERD v1.1 인라인 + 파일 rename + 팀명 일괄). CHANGES_2026-05-03.md 신설.

### v5.0_260503 (작성자: @youminsu0523 / branch: MS)
- Phase 25 부분 완료 (mockup → DB API 전환), Phase 27 신설(배포 직전 안정화 — Swagger / 운영 가드 / InspectionSchedule / Employee 라우터 / 시드 / 문서 동기화)

### v4.0_260427 (작성자: @youminsu0523 / branch: MS)
- 전면 재작성: git log 기반 21개 Phase 상세 기록 (파일 수, 구체적 구현 내용, 담당자, 함수명/API/모델 상세)

### v1.0_260413 (작성자: @Antigravity / branch: main)
- Implementation_Plan.md 초기 생성
