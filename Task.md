# Task.md

## 프로젝트 개요
- **프로젝트명**: AeroInspect AI — 드론 기반 아파트 사전 점검 자동화 플랫폼
- **목적**: 드론(RGB+열화상+LiDAR)으로 아파트 외벽/내벽 결함을 자동 탐지하고, 20종 AI 분류 → 3D 시각화 → PDF/Excel 리포트를 생성하는 풀스택 서비스
- **주요 스택**: React + React Three Fiber (R3F) + Tailwind CSS, FastAPI (Python), PostgreSQL, WebSocket + Redis Pub/Sub, ONNX Runtime + YOLOv8 + ResNet50
- **팀원**: @youminsu0523 (MS), @Hijin554 (Hijin), @unknownName-15 (SH), @Antigravity (자동화/인프라)

---

## 작업 목록 — @youminsu0523 (branch: MS)

### Phase 1. 프로젝트 초기화 & 인프라 (260413~260414)
- [x] v1.0_260413 — 팀 프로젝트 협업 가이드 적용 및 프로젝트 초기화
- [x] v1.1_260413 — 백엔드/프론트엔드 개별 문서 구조 분화 (`backend/Task.md`, `frontend/Task.md` 등)
- [x] v1.2_260413 — 팀 가이드라인 Gemini 대응 업데이트 (`team_project_rules.md` AI 공통화)
- [x] v1.3_260413 — `.clauderules`, `.geminirules` 생성 (git pull 시 AI 자동 규칙 참조)
- [x] v1.4_260413 — 별전 레포지토리 이전 대비 가이드라인 복제
- [x] v1.5_260413 — 독립 레포지토리 가이드라인 무결성 강화
- [x] v1.6_260413 — 프로젝트 전체 아키텍처 및 데이터 플로우 전수 조사

### Phase 2. FastAPI 백엔드 초기 구조 + 프론트엔드 기초 (260414)
- [x] v2.0_260414 — **8개 파일** 변경
  - `backend/app/main.py`: FastAPI 앱 진입점 — `lifespan` 핸들러(DB 초기화, RGB/Thermal 카메라, YOLOv8 모델 로드), CORS, `/api/v1` 라우터, `/health` 헬스체크
  - `backend/requirements.txt`: FastAPI, SQLAlchemy(asyncio), OpenCV, PyTorch, Ultralytics, anomalib, pymavlink, anthropic 등 의존성
  - `frontend/src/components/layout/Header.jsx`: `useDroneStore` 텔레메트리(고도/속도/배터리/모드) + `useDefectStore` 하자 심각도 카운트 + WebSocket 상태 뱃지
  - `frontend/src/components/defects/DefectPanel.jsx`: `DefectFilter`(심각도/영역/카테고리) + `DefectCard` 리스트 + `useDefects` REST 초기 로드

### Phase 3. 랜딩 페이지 & 라우팅 분리 (260415)
- [x] v2.1_260415 — **95개 파일** (이미지 ~80개 포함)
  - `App.jsx` 라우팅: `/` = Landing, `/dashboard` = DashboardLayout
  - `Landing.jsx`: LandingHeader + HeroSection + ServiceIntroSection + FeaturesSection + CasesSection + DualCTASection 조립
  - `HeroSection.jsx`: `import.meta.glob` 이미지 자동 스캔, 5초 주기 3장 크로스페이드(더블 버퍼링), 그라데이션 오버레이, CTA 2개
  - `LandingHeader.jsx`: 스크롤 위치 기반 투명↔흰색 전환, 로고 스왑, `ContactModal` 연동
  - `ContactModal.jsx`: 개인/사업자 탭, 사업자등록번호 10자리 진위 시뮬레이션, 담당자/연락처/문의 수집
  - `ServiceIntroSection.jsx`: 접근성/정밀성/효율성 3가치 카드 + Reveal 애니메이션
  - `FeaturesSection.jsx`: 하이브리드 3D 복원/AI 하자 식별/정밀 공간 매핑 3기술 카드
  - `CasesSection.jsx`: B2B 건설사/정밀 안전진단/B2C 입주민 3레퍼런스 + `CaseSlideshow`
  - `DualCTASection.jsx`: B2B(다크)/B2C(옐로) 좌우 분할 CTA
  - `Reveal.jsx`: IntersectionObserver 스크롤 진입 1회 애니메이션
  - `smoothScroll.js`: 앵커 링크 부드러운 스크롤 유틸
  - 이미지 에셋 ~80개 (hero, cases, cta, features, logo)

### Phase 4. 프론트엔드 초기 구조 + 인증 페이지 + 국세청 API (260416)
- [x] v2.2_260416 — **11개 파일**
  - `Signup.jsx` (784줄): 개인/사업자 탭, 사업자번호 국세청 진위확인(`checkBusinessStatus` API), 이메일 도메인 드롭다운+중복확인, 아이디 중복확인, 비밀번호 자동생성, 약관 3종 아코디언
  - `Login.jsx` (254줄): 개인/사업자 탭, 소셜 로그인(Google/Naver/Kakao 원형 아이콘), 아이디/비밀번호 찾기 링크
  - `FindAccount.jsx` (320줄): 아이디찾기/비밀번호찾기 탭, `?tab=id|pw` 쿼리 파라미터 연동
  - `businessVerifyApi.js`: 국세청 odcloud.kr POST 호출(Vite 프록시), 상태코드 매핑(01계속/02휴업/03폐업)
  - `vite.config.js`: `/odcloud` 프록시 설정 (CORS 우회)

### Phase 5. 풀스택 드론 관리 초기화 + 백엔드 인증 (260416)
- [x] v2.3_260416 — **31개 파일**
  - **백엔드 인증**: `api/auth.py` (signup/check-email/check-username), `models/user.py` (UUID PK, account_type, bcrypt), `models/business_profile.py` (사업자 프로필), `models/term.py` (약관 마스터 3종), `models/user_term_agreement.py`, `schemas/user.py`, `core/security.py` (bcrypt 해싱)
  - **프론트엔드 대시보드 UI**: `DashboardTopBar.jsx` (풀스크린 HUD 상단 바, 검색/Satellite/Flightpaths/알림/프로필), `DronesPanel.jsx` (DRONE 01 RGB + DRONE 02 THERMAL 카드), `Dashboard.jsx` (메인 LIVE 카메라, Thermal PIP, 3D Mini Map, AI Defect 패널), `DroneStatusCard.jsx`
  - `droneStore.js`: `DRONE_CAMERA_MAP` 드론별 카메라 자동 매핑

### Phase 6. 세션 워크플로우 + 3D 시각화 + 미션 제어 (260416)
- [x] v2.4_260416 — **23개 파일**
  - `SessionSetup.jsx`: 현장명/운용자/점검일자 입력, 유효성 검증 → `/session/level`
  - `SessionLevel.jsx`: L1(CAD)/L2(평면도)/L3(드론 자율비행) 선택 카드, L3 "추천" 뱃지
  - `SessionModeling.jsx`: Level별 업로드/시뮬레이션, Mock 프로그레스 6~12초, 완료 후 `/dashboard`
  - `sessionStore.js` (Zustand+persist): siteName/operatorName/level/uploadedFile/modelStatus/modelProgress + `startModeling()`/`cancelModeling()`
  - `mockModeling.js`: Level별 시뮬레이터 (L1: CAD 파싱→메시 6~8초, L2: 윤곽→역설계 6~8초, L3: SLAM→포인트클라우드 10~12초)
  - 세션 컴포넌트 5개: FileDropzone, LevelCard, ModelingProgress, SessionLayout, ProtectedSessionLayout
  - `DroneMarker.jsx`: cone+4프로펠러+고도라인, Billboard ID 라벨, yaw 회전, 미션 상태별 색상
  - `MissionControl.jsx`: 미션 시작/중지/착륙 버튼

### Phase 7. 직원 전용 랜딩 + 랜딩 컴포넌트 분리 (260416)
- [x] v2.5_260416 — **6개 파일**
  - `EmployeeLanding.jsx` (749줄): 사무실 허브 레이아웃 — KPI 카드 3개, 오늘 일정 테이블, 알림/공지, 팀원 현황(이름/직급/팀/담당현장/상태), 최근 활동 로그, 현재 세션 카드(sessionStore 실데이터), MOCK_* 목업 데이터
  - `App.jsx`: `/employee` 라우트 추가
  - `LandingHeader.jsx`: 직원 전용 진입 링크 추가

### Phase 8. 드론 리포트 관리 시스템 (260416)
- [x] v2.6_260416 — **36개 파일**
  - `ReportsList.jsx`: 보고서 목록 (현장명/일자/공종/하자 요약/상태/열기/삭제)
  - `ReportDetail.jsx`: 개별 리포트 편집, debounce 500ms 낙관적 업데이트
  - `ReportEditor.jsx`: 공종별 그룹 테이블, `suggestTrades()` AI 공종 자동 제안, LocationMapEditor, AddDefectDialog
  - `AddDefectDialog.jsx`: 하자 유형/영역(A~E)/장소/공종/심각도/조치메모/이미지
  - `DefectEditRow.jsx`: 인라인 수정/삭제/이미지 크롭
  - `ExcelExportButton.jsx`: SheetJS `.xlsx` (요약 시트 + 하자 목록 시트)
  - `PdfExportButton.jsx`: `@react-pdf/renderer` `.pdf` (Noto Sans KR 한글 폰트)
  - `LocationMapEditor.jsx`: 장소명 일괄 rename
  - `TradeSelect.jsx`: 공종 드롭다운 + "직접 입력"
  - `reportsStore.js` (Zustand): fetchAll/fetchOne/create/update/remove
  - `reportsApi.js`: localStorage 기반 CRUD (DB 연결 전 대체)
  - `reportApi.js`: `suggestTrades()` AI API
  - `preModelStore.js`: 사전 작업 모델 라이브러리
  - `trades.js`: 건설 공종 12종 마스터, CATEGORY_TRADE_MAP, LOCATION_PRESETS
  - `PreWork.jsx`: 사무실 사전 작업 (라벨→Level→업로드→Mock 3D→preModelStore 저장)
  - CI: `.github/workflows/vibe-log-check.yml`, `scripts/append_vibe_log.py`

### Phase 9. 드론 미션 제어 + 비디오 스트리밍 + 리포트 내보내기 (260417)
- [x] v2.7_260417 — **50개 파일**
  - **백엔드**: `services/recording.py` (RGB+Thermal 동시 mp4 녹화, `_CameraRecorder` cv2.VideoWriter), `services/floorplan_processor.py` (OpenCV 벽체 추출 — 그레이스케일→이진화→모폴로지→Canny→HoughLinesP→정규화), `api/stream.py` (MJPEG RGB/Thermal/Blend + 녹화 start/stop/status/list/download/delete), `api/floorplan.py` (업로드/처리/분석/목록/상세/삭제), `schemas/floorplan.py`
  - **프론트엔드 리포트 강화**: ExcelPreviewModal (HTML 테이블 미리보기), PdfPreviewModal (BlobProvider→iframe), TemplateExportButton, `templateExport.js` (ExcelJS 양식 주입 — 하자점검_결과보고서.xlsx 템플릿→데이터/이미지 삽입)
  - `SessionSetup.jsx` 확장: siteUnit/inspectionType/witness 등 필드 추가
  - 한글 폰트 2개: NotoSansKR-Bold.ttf, NotoSansKR-Regular.ttf

### Phase 10. Dashboard + DroneMarker 비행 경로 시각화 (260417)
- [x] v2.8_260417 — **2개 파일**
  - `DroneMarker.jsx` 대폭 개선: 비행 경로 폴리라인(`Line` dashed), 위치 히스토리 축적(MAX 500개, MIN_MOVE_DIST 0.05 필터링), 바닥 2D 투영 그림자, 미션 시작 시 초기화

### Phase 11. 풀스택 인증 시스템 완성 (260417)
- [x] v2.9_260417 — **18개 파일**
  - **백엔드**: `api/auth.py` (login/me), `api/oauth.py` (Google/Kakao/Naver 3종 — authorization code→token→userinfo→JWT, `_find_or_create_oauth_user` 3단계), `core/jwt.py` (create_access_token HS256/decode), `dependencies.py` (get_current_user Bearer 검증), `models/user.py` (oauth_provider/oauth_id 추가), `config.py` (JWT_SECRET, OAuth client_id/secret 6개)
  - **프론트엔드**: `authApi.js` (login/oauthLogin/getMe + OAuth URL 빌더 3종), `authStore.js` (token/user/isAuthenticated + setAuth/logout + localStorage 4키), `OAuthCallback.jsx` (URL code 추출→백엔드→JWT→/employee 리다이렉트), `Login.jsx` 소셜 버튼 실제 OAuth URL 연결

### Phase 12. 현장 관리 시스템 (260418)
- [x] v3.0_260418 — **22개 파일** (+2,822줄)
  - **백엔드**: `models/site.py` (UUID PK, seq 자동순번, name, inspection_type 6종 Enum, building_type 7종 Enum, total_area, assigned_members JSONB, recordings JSONB, status 4종 등 20+ 컬럼), `schemas/site.py` (SiteCreate/Update/Response + AssignedMember/Recording 중첩), `api/sites.py` (GET 목록 필터+페이지네이션, GET/:id, POST, PATCH JSONB 변환, DELETE)
  - **프론트엔드**: `sitesApi.js` (localStorage 시드 5건 — 헬리오시티/판교 알파돔/위례 자이/성북B2C/강남 래미안), `sitesStore.js` (Zustand CRUD), `SiteManagement.jsx` (히어로+KPI 4카드+검색+필터탭+테이블), `SiteDetail.jsx` (히어로+미니KPI+의뢰자/운영 2컬럼+탭 3개), `SiteFormModal.jsx`, 탭 컴포넌트 3개
  - `Analytics.jsx`, `TrendReport.jsx`, `WeeklyReport.jsx`, `mockTrendData.js`

### Phase 13. 풀스택 채팅 + 알림 + 조직 관리 (260420)
- [x] v3.1_260420 — **48개 파일** (+4,313줄)
  - **백엔드 DB 모델 5개**: Conversation(dm/group/channel), ConversationMember(M:N, last_read_at), Message(text+FK), Notification(10종 카테고리 Enum, JSONB metadata, is_read), Organization+OrganizationMember(biz_number 매칭, role 3종, status 3종)
  - **백엔드 API**: `api/chat.py` (대화방 목록/생성/메시지 목록/전송+WS 브로드캐스트/읽음/미읽음), `api/notifications.py` (목록+필터/미읽음수/단건읽음/전체읽음/삭제), `api/organization.py` (내 조직/멤버목록/생성/초대 admin권한/수정/삭제 owner보호)
  - **백엔드 서비스**: `email_service.py`, `notification_service.py`
  - **프론트엔드 채팅 UI 9개**: Chat.jsx (Slack 3컬럼), ConversationList, ConversationItem, MessageThread, MessageBubble (카카오톡 스타일), MessageInput, ChatHeader, NewChatModal (조직 멤버 선택), ParticipantPanel, FloatingChatButton
  - **프론트엔드 알림**: NotificationDropdown, notificationCategories.js 10종
  - **Store/API**: chatStore.js, notificationStore.js, chatApi.js, notificationApi.js, organizationApi.js

- [x] v3.2_260420 — OAuth 사용자 검색 개선: 이메일 대소문자 무시(`func.lower`), IntegrityError race condition 대응 (rollback→재조회→409)

### Phase 14. 20종 결함 분류 ONNX 추론 파이프라인 (260422)
- [x] v3.4_260422 — **41개 파일** (+6,392줄)
  - **ONNX 추론 엔진 4클래스** (`onnx_inference.py` 393줄): ONNXYoloDetector(letterbox+NMS+CUDA/CPU), ONNXResNetClassifier(ImageNet정규화+softmax top3), ONNXUNetSegmenter(온도맵→멀티클래스 마스크), ONNXPatchCoreDetector(anomalib 호환)
  - **20종 파이프라인** (`inference_pipeline_20.py` 351줄): M1(YOLO구조→ResNet균열 2-Stage), M2(YOLO마감→ResNet표면 2-Stage), M3(YOLO바닥창호→ResNet유형 2-Stage), M4(U-Net 열화상), M5+G1(YOLO-seg+기하학), M6(PatchCore 앙상블), Tier 기반 계층 실행
  - **앙상블** (`ensemble.py` 109줄): cross_model_nms + PatchCore 독립사건결합 승격
  - **정밀 검출기**: `alignment_detector.py` (647줄, YOLO-seg→서브픽셀 엣지→RANSAC→LiDAR→KCS 41 46 01 기준 수직도 ±3mm/m, 직각도 ±2mm/m), `insulation_detector.py` (237줄, U-Net+RGB 퓨전 4종 단열 하자), `temporal_filter.py` (120줄, 프레임간 시간 일관성)
  - **학습 스크립트 15+개**: `auto_train_all.py` (M1~M6 순차학습+ONNX 410줄), 개별 train_m1~m6 10개, `export_to_onnx.py`, 평가/벤치마크, configs/*.yaml 5개, Jupyter 노트북 2개
  - `defect_taxonomy.py`: DEFECT_20_MAP 20종 매핑 (code/display_ko/severity/area)

### Phase 15. 데이터셋 관리 (260423)
- [x] v3.5_260423 — `datasets_sources.md` (9개 데이터셋, 63,285장, 하자코드 A-01~E-02 ↔ 데이터셋 ↔ M1~M6 완전 매핑)

### Phase 16. 드론 테스트 스트림 + 대시보드 인프라 (260424)
- [x] v3.6_260424 — **33개 파일** (+2,787줄)
  - **핵심**: `test_stream.py` (1,053줄) — 카테고리별 균등 샘플링, RGB/Thermal 쌍 동기화, 재생 제어(start/pause/resume/stop), MJPEG 제너레이터, image_crop base64, 20종 ONNX 추론/목업 폴백, 7종 디렉토리 하자 매핑, 한글 PIL 렌더링
  - `api/stream.py` 테스트 모드 14개 엔드포인트: init/start/pause/resume/stop/state/rgb/thermal/source/upload CRUD/detection-mode/defect frame
  - `TestModeBar.jsx` (319줄): 재생 버튼, 소스 전환, 대량 업로드, bbox↔detection 모드
  - `floorplan_processor.py` +206줄: `validate_floorplan_quality()` (해상도/선명도/대비/직선비율/직각교차점/기울기/벽체수 7항목)
  - 프론트엔드 API 리팩토링: localStorage 목업 → axios 실제 API 호출로 대거 전환 (-1,000줄+)
  - `sessionStore.js`: 테스트 모드 상태 추가 (testSource/testPlayState/testDetectionMode)

### Phase 17. 조직/멤버 관리 + 채팅 고도화 (260424)
- [x] v3.7_260424 — **15개 파일** (+492줄)
  - **백엔드**: chat DM 중복 방지 (aliased 자기조인), 대화방 나가기 (참여자 0→대화방 삭제), organization 슈퍼어드민 전체 조직 목록/부서 목록, `invite_code` 필드
  - **프론트엔드**: AdminMembers 슈퍼어드민 조직 배정 4단계 워크플로우 (조직→역할→부서→직위), ParticipantPanel 대화 나가기, chatStore `leaveConversation()`, 채팅 컴포넌트 6개 참여자 데이터 구조 변경 대응

---

## 작업 목록 — @Hijin554 (branch: Hijin)

### Phase 1. 백엔드 텔레메트리 + AI 웹훅 + 리포팅 + SLAM + 평면도 (260416)
- [x] v1.0_260416 — **17개 파일** (+1,191줄)
  - `api/ai_webhook.py`: AI 탐지 단건/열화상/배치 3개 엔드포인트 (DefectLog DB 저장 + WS "defects"/"thermal" 브로드캐스트)
  - `api/telemetry.py`: POST(저장+WS "telemetry" Push, ROS2/MAVLink 호출용) + GET 목록(페이지네이션) + GET 최신 1건
  - `api/slam.py`: SLAM 맵 CRUD 5개 (POST 생성+WS, GET 목록 메타만, GET/:id 이미지포함, PATCH 실시간 갱신+WS, DELETE)
  - `api/floorplan.py`: JPG/PNG/PDF/DXF 업로드(aiofiles 비동기), OpenCV 벽체 추출 트리거, 목록/상세/삭제
  - `api/report.py`: 기존 LLM 보고서에 저장/조회/다운로드/삭제 추가 (마크다운 Content-Disposition)
  - **DB 모델 4개 신규**: telemetry_logs(pos xyz, roll/pitch/yaw, vel xyz, battery, flight_mode, sensor_status JSONB), slam_maps(name/resolution/width/height/원점/map_image Base64/metadata JSONB), floorplans(파일정보/처리상태/walls_data JSONB/gazebo_world_path), reports(제목/건물/점검자/본문 Text/하자 통계)
  - Pydantic 스키마 4세트 + router.py에 4개 라우터 등록

### Phase 2. 3-모델 통합 추론 + 실시간 스트림 워커 + REST 추론 + WS 프레임 수신 (260420)
- [x] v1.1_260420 — **23개 파일** (+2,139줄)
  - `services/inference_pipeline.py` (460줄): InferencePipeline 싱글톤 — YOLOv8s crack_moisture + YOLOv8s delamination + ResNet50 wallpaper 3-모델 순차 추론, `detect()`/`detect_async()`, severity 계산(YOLO=HIGH, 벽지심각=MED), 레거시 A-E taxonomy 호환
  - `services/wallpaper_classifier.py` (188줄): ResNet50 19클래스 벽지 분류 싱글톤, top1/top3 softmax
  - `services/defect_taxonomy.py` (188줄): WALLPAPER_CLASSES 19개, CLASS_DISPLAY_MAP("good"=터짐 Burst), YOLO_DISPLAY_MAP, WALLPAPER_SEVERE_CLASSES, LEGACY_MAP, xyxy_to_xywhn
  - `core/stream_inference.py` (239줄): StreamInferenceWorker 싱글톤 — asyncio.Queue(maxsize=1) 드롭큐, 프레임 스킵, to_thread 비블로킹, "stream"+"defects" WS 동시 브로드캐스트
  - `api/detect.py`: POST 단건/POST batch(최대 10장) multipart 추론
  - `api/ws_stream.py`: WS /ws/stream 바이너리 JPEG 프레임 수신→cv2.imdecode→드롭큐
  - `schemas/detection.py`: DetectionResult, YoloDetection, WallpaperPrediction, WSStreamMessage
  - `tests/test_inference_pipeline.py` (193줄): xyxy→xywhn 회귀, taxonomy "good"=Burst, /health, /detect 503/400/404

### Phase 3. 백엔드 구조 초기화 + 벽지 이중 게이트 도입 (260421)
- [x] v1.2_260421 — **5개 파일**
  - `services/inference_pipeline.py` 이중 게이트: `is_confident = (top1_conf >= 0.35) AND (top1_conf - top2_conf >= 0.15)` (val_acc 54% 대응, 근소차 예측 오탐 차단)
  - `config.py`: WALLPAPER_CONF_THRESHOLD 0.4→0.35, WALLPAPER_MARGIN_THRESHOLD 0.15 신규

### Phase 4. LiDAR 3D + 이미지 저장소 + 구조화 로깅 (260421)
- [x] v1.3_260421 — **19개 파일** (+819줄)
  - `services/telemetry_cache.py` (104줄): DronePose dataclass 메모리 캐시 싱글톤, asyncio.Lock O(1) 갱신, snapshot_fresh(5초 stale 판정)
  - `services/image_storage.py` (95줄): Base64→파일시스템 전환 (`./uploads/defects/{YYYY-MM-DD}/{uuid}.jpg`), StaticFiles URL, 하자 삭제 시 파일 정리
  - `core/logging.py` (74줄): structlog JSON(운영)/컬러 콘솔(개발), request_id_ctx ContextVar
  - `core/middleware.py` (65줄): RequestIDMiddleware — X-Request-ID 자동 바인딩, http.request 이벤트 status/duration_ms
  - `core/stream_inference.py`: `_compute_lidar_xyz()` — telemetry_cache fresh pose + lidar_service → 3D 월드 좌표, 추론 결과에 lidar_position 필드
  - `main.py`: lidar_service/telemetry_cache 초기화, RequestIDMiddleware 등록
  - DB: defect_logs image_crop_path 컬럼 마이그레이션
  - **테스트 3개**: test_telemetry_cache, test_image_storage, test_wallpaper_double_gate

### Phase 5. 결함 로깅 + 벽지 임계값 최적화 + 점검 커버리지 (260422)
- [x] v1.4_260422 — **9개 파일** (+421줄)
  - `api/coverage.py` (146줄): site별 텔레메트리 convex hull 면적 (Andrew's monotone chain O(n log n) + Shoelace 면적), covered/supplied/ratio/uncovered/hull 폴리곤 반환
  - `api/stream.py` +`GET /stream/stats`: 추론 워커/텔레메트리 캐시/LiDAR 상태
  - `scripts/sweep_wallpaper_thresholds.py` (132줄): JSONL 기반 conf/margin 격자 탐색, precision/recall/F1 CSV
  - `tests/test_coverage_geometry.py`: convex hull/면적 기하 단위 테스트

### Phase 6. 벽지 더블 게이트 + 모니터링 스키마 + 테스트 보강 (260422)
- [x] v1.5_260422 — **8개 파일** (+387줄)
  - `schemas/monitoring.py` (69줄): StreamStatsResponse(WorkerStats/TelemetryCacheStats/LidarStats), CoverageResponse
  - `api/coverage.py`: dict→CoverageResponse Pydantic 전환
  - `api/defects.py`: DELETE 시 image_storage.delete 보완
  - **테스트 3개**: test_coverage_response_shape (UUID/ratio/hull/fallback), test_defect_delete_cleanup (DB→파일 순서 보장), test_wallpaper_double_gate 보완

### Phase 7. 텔레메트리 로깅 + site_id FK (260422)
- [x] v1.6_260422 — **7개 파일** (+272줄)
  - telemetry_logs에 site_id FK 마이그레이션 (nullable, 테스트/디버그 허용)
  - `api/coverage.py`: site별 필터링 + fallback(site 레코드 0건→전역 최근 N건)
  - `tests/test_defects_api.py` 전면 리팩토링: 조직 스코핑 적용, dependency_overrides + AsyncMock

### Phase 8. Refresh Token + Auth Guards + Prometheus + Push + Redis WS (260422)
- [x] v1.7_260422 — **26개 파일** (+1,532줄)
  - `core/jwt.py`: create_refresh_token (type="refresh"), decode_refresh_token (교차 사용 차단), 레거시 호환
  - `api/auth.py`: POST /auth/refresh, login/OAuth 응답에 refresh_token 포함
  - `core/metrics.py` (158줄): PrometheusMiddleware (HTTP 수/지연 자동), 커스텀: stream_frames, defect_detected(severity), lidar_distance, telemetry_cache_age, queue_size, /metrics 엔드포인트
  - `core/ws_manager_redis.py` (155줄): RedisConnectionManager — broadcast→Redis publish→subscribe→로컬 재분배, `create_ws_manager()` 팩토리 (memory|redis, 미기동 시 폴백)
  - `services/push_notifications.py` (136줄): FCM/APNs 스켈레톤 — PUSH_PROVIDER=noop|fcm|apns, send_to_user(DeviceToken 전부), _mark_inactive(실패 시 비활성화)
  - `models/device_token.py` (55줄): device_tokens 테이블 (platform fcm/apns/web, UNIQUE)
  - `api/notifications.py`: POST /tokens 등록/갱신, DELETE /tokens/:id, POST /push/test
  - 인증 가드: slam 5개 + telemetry GET 2개 + floorplan 전체 + POST /floorplan/:id/calibrate (scale_px_per_meter)
  - config: JWT_REFRESH_EXPIRE_DAYS, LOG_JSON/LEVEL, PUSH_PROVIDER, WS_BACKEND, REDIS_URL
  - 마이그레이션 2개: device_tokens, floorplans scale_px_per_meter
  - **테스트 6개**: test_refresh_token, test_metrics, test_push_service, test_ws_manager_redis, test_logging_json, test_floorplan_calibration

---

## 작업 목록 — @unknownName-15 (branch: SH)

### Phase 1. 프론트엔드 인증 UI & 모바일 반응형 (260417~260420)
- [x] v1.0_260417 — package-lock.json 생성 (의존성 버전 잠금)
- [x] v1.1_260420 — **7개 파일** (+146줄)
  - **Remix Icon CDN 도입**: `index.html`에 `remixicon@4.5.0` 전역 등록
  - **LandingHeader 모바일 햄버거 메뉴**: `isMobileMenuOpen` state + `mobileMenuRef` 외부클릭 닫기, 햄버거 버튼(`md:hidden`, `ri-menu-line`/`ri-close-line` 토글, aria-label/aria-expanded), 드롭다운 메뉴(직원전용+TEMP 뱃지/로그인/도입문의), 스크롤 상태별 배경 분기(slate-900/white)
  - **네비게이션 UX 통일**: Login.jsx/Signup.jsx/FindAccount.jsx의 "뒤로가기"를 `navigate(-1)` + `ri-corner-up-left-line` 아이콘 + aria-label로 통일
  - **포커스 링 전역 제거**: `index.css` button:focus outline:none, HeroSection/LandingHeader focus:ring 클래스 제거
  - **데스크탑 정리**: "도입 문의하기" CTA `hidden md:block` (모바일 햄버거에서 대신 표시)

---

## 작업 목록 — @Antigravity (branch: main, 자동화/인프라)
- [x] v1.0_260413 — Task.md, Implementation_Plan.md 초기 생성
- [x] v1.1_260413 — 프로젝트 문서를 backend/, frontend/로 분화
- [x] v1.2_260413 — Gemini 대응 가이드라인 수정
- [x] v1.3_260413 — .clauderules, .geminirules 생성
- [x] v1.8_260414 — Notion 연동 스크린샷 캡쳐 폴백 로직 통합 (`sync_notion_logs.py` 단일화, `.gitignore` 등록)
- [x] v1.9_260427 — 리포지토리 루트의 README.md 내용을 현재 진행 상황(AI, RL, Frontend)과 맞춰 최신화

---

## 요구사항
1. `team_project_rules.md` 모든 협업 규칙 준수
2. 시니어 멘토 모드 개발 가이드
3. Better Comment 규칙 (`// //!`, `// //*`)
4. 코드 수정 시 필수 보고서 (Scope, Refactoring, Checklist, Full-Stack Sync, Mentor's Tip)
5. Task.md / Implementation_Plan.md 실시간 동기화

---

## Revision History

### v5.1_260503 (작성자: @youminsu0523 / branch: MS)
- **tasks 문서 양식 정정**: API 명세서 `v1.1.md → v1.2.md` 파일명 rename + 부록을 4.17/2.1.5/8.5 인라인으로 분산. ERD `v1.0.md → v1.1.md` rename + 4.19/5장/6장/8.3/12.1/13장 인라인 갱신, 문서 이력 위치 마지막→목차 이전 이동. 가이드 3종(AI 추론/Frontend/Backend) 도 문서 이력 위치 정정. tasks 8개 문서 팀명 `다마코더 → AeroInspect` 일괄 교체.
- **DB 마이그레이션 + 시드 실 적용**: alembic 분기 head 병합(`89b53c16de85`) + `defect_logs` 누락 컬럼 10개 ALTER 보정 + `seed_demo_data --reset` 실행 → org/depts/users(백승희·오희진)/sites=8/defects=315/reports=12/today_schedules=3 (잠실 리센츠 14:00 KST 백승희 정상 시드).
- **CHANGES_2026-05-03.md 신설**: Claude 웹 문서 변환용 산출물 목록 + 변환 프롬프트 템플릿.

### v5.0_260503 (작성자: @youminsu0523 / branch: MS)
- **Swagger Phase 1~3 + 운영 보안 가드** (backend R24): main.py에 HTTPBearer/AIWebhookSecret 보안 스키마 명시 등록(bearerFormat=JWT) + 17개 tags_metadata + servers + persistAuthorization. config.py/init_db.py에 `APP_ENV=production` 가드 (placeholder secret 차단 + create_all 자동 스킵). schemas/common.py 신규(PROTECTED/PUBLIC/WEBHOOK responses), 핵심 schema 4종에 example 추가.
- **Mockup → DB 전환 (KPI 0 방지 시드)** (backend R25 + frontend R12): InspectionSchedule 모델 + alembic migration `i2c3d4e5f6a7` + `/api/v1/employee/{schedule/today, kpi/monthly, activities}` 라우터 신규. 시연 시드 스크립트 `scripts/seed_demo_data.py` 신설(조직/부서/사용자 백승희·오희진/현장 8개/하자 25~60건/보고서 3~5건/오늘 일정 3건/알림). EmployeeLanding.jsx의 MOCK_* 4개 const 삭제 + axios useEffect API fetch로 완전 교체.
- **프론트 mockup 팀원명 정리** (frontend R12): mockTrendData / chatConstants / SiteFormModal / EmployeeLanding 4파일에서 가짜 팀원명(김다연/이준혁/박지훈/이서현/박서연) → 실제 팀(백승희/오희진/유민수)로 통일.
- **문서**: API 명세서 v1.1 → **v1.2** (Employee API 섹션 + Swagger 보강 부록 추가), ERD v1.0 → **v1.1** (inspection_schedules 테이블 정의 부록 추가, 총 19 테이블/12 alembic 리비전).
- **보안 점검**: .env git 추적 0건 / 소스 하드코딩 시크릿 0건 검증.

### v4.0_260427 (작성자: @youminsu0523 / branch: MS)
- 전면 재작성: 팀원 4명 전체(@youminsu0523, @Hijin554, @unknownName-15, @Antigravity) 10일간 작업 상세 기록
- 각 버전별 변경 파일 수, 구체적 파일 경로, 함수명/컴포넌트명/API 엔드포인트/DB 모델 상세 기술
- 커밋 로그 기반 정확한 날짜 및 작업자 기록

### v1.8_260414 (작성자: @Antigravity / branch: main)
- Notion 연동 스크린샷 캡쳐 폴백 로직 통합

### v1.0_260413 (작성자: @Antigravity / branch: main)
- Task.md 초기 생성 및 협업 프로토콜 정의
