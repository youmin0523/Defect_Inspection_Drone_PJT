# Frontend Implementation Plan

## 아키텍처 개요
- **데이터 흐름**: Backend API -> State Management (Hooks/Zustand 등) -> Component Props -> R3F Canvas
- **컴포넌트 의존성**: `App` -> `Layout` -> `Scene` -> `Drone`/`Building`

## 구현 계획 (단계별)

### Step 1. 프론트엔드 구조 분석
- **담당 파일**: `frontend/` 내부 전체
- **영향도 분석 [주의]**: 기존 R3F 씬 구성 및 UI 이벤트 핸들러 보존 (Rule 3-6 준수)
- **테스트 플랜**: 로컬 개발 서버 구동 및 3D 캔버스 렌더링 확인

### Step 2. 직원 전용 랜딩 (`/employee`) — 사무실 허브 (v2)
- **담당 파일**:
  - 전면 재작성: `src/pages/EmployeeLanding.jsx` (v1 Interior HUD → v2 Office Hub)
  - 변경 없음: `src/App.jsx`, `src/components/landing/LandingHeader.jsx` (라우트/버튼 구조 유지)
- **UX 경계 정의** (메모리 고정):
  - `/employee` = **사무실 허브** — 도면 사전 작업, 보고서 작성, 현장/팀 관리, KPI/일정/알림 확인
  - `/session/setup → /session/level → /session/modeling → /dashboard` = **현장 실무** — 실시간 드론 관제, 하자 탐지
- **섹션 구성** (상→하):
  1. `EmployeeHeader` — sticky 흰색 헤더 (메인으로 / 브랜드 / 알림 / 프로필 / 로그아웃)
  2. `WelcomeBanner` — slate-900 다크 배너 + 개인화 인사 + `SummaryPill`(오늘 일정/승인 대기)
  3. `QuickActionsSection` — 4카드 (현장 점검 시작 / 도면 업로드 / 보고서 작성 / 현장 관리 SOON)
  4. `KPISection` — 4카드 (이번 달 점검/현재 세션 하자/심각 하자/비행 시간) + LIVE·MOCK 뱃지
  5. `TodayScheduleSection` + `NotificationsSection` — 2열
  6. `TeamAssignmentsSection` — 팀원 상태·담당 현장 테이블
  7. `RecentActivitySection` — 최근 활동 타임라인
- **데이터 흐름**:
  - 실데이터(zustand store): `useSessionStore`(siteName/operatorName/level) · `useDefectStore`(defects/severity) · `useDroneStore`(missionStatus/Started/EndedAt)
  - 목업 상수: `MOCK_MONTHLY_KPI` · `MOCK_TODAY_SCHEDULE` · `MOCK_NOTIFICATIONS` · `MOCK_TEAM_MEMBERS` · `MOCK_RECENT_ACTIVITIES`
  - 교체 전략: 각 `MOCK_*` 상수를 동일한 스키마의 API 훅 호출로 점진 교체 (키·타입 고정)
- **영향도 분석 [주의]**:
  - 기존 라우트/세션 플로우 전면 보존. 직원 전용 버튼 플로우는 v1.4 에서 이미 `/employee` 경유로 전환됨 — 이번 라운드는 `/employee` 페이지 **내용물만** 교체.
  - 현재 라우트 **미가드**. 운영 배포 전 `ProtectedEmployeeLayout`(세션/직원 role) 필요.
  - `MOCK_*` 상수는 파일 내부에만 존재. 외부에서 import 하지 않으므로 API 교체 시 해당 파일만 수정하면 됨.
- **테스트 플랜**:
  - Landing → "직원 전용" → `/employee` 렌더. 헤더/배너/4섹션 모두 표시.
  - "현장 점검 시작" → `/session/setup` · "도면 업로드" → `/session/level` · "보고서 작성" → `/dashboard/report` overlay.
  - 팀원 "재배정" 버튼 / "현장 관리" 카드는 SOON placeholder — 클릭 시 동작 없음(툴팁만).
  - LIVE KPI: 기존 세션이 진행 중이면(`siteName` 존재) 배너에 현장명/상태 표시, 하자 카드에 실제 값 표시. 세션 없으면 빈 기본값.
  - 반응형: Mobile(1열 스택) / Tablet(`md` — 2열, 테이블 축소) / Desktop(`lg` — 4열 그리드, 2열 섹션).

## Revision History

### v1.2_260416 (작성자: @youminsu0523 / branch: MS)
**[Step 2 재정의]**
- Step 2 의 `/employee` 를 "Interior Inspection 목업" 에서 **"사무실 허브 (v2)"** 로 방향 전환
- UX 경계선 고정: `/employee` = 사무실 허브 / `/session/*`·`/dashboard` = 현장 실무 — 두 영역 섞지 않음
- `EmployeeLanding.jsx` 전면 재작성 (9개 서브 컴포넌트), 실데이터 + 목업 상수 혼용 구조 명세화

### v1.1_260416 (작성자: @youminsu0523 / branch: MS)
**[추가 단계]**
- Step 2. 직원 전용 랜딩 (`/employee` · Interior Inspection Dashboard) 신설 계획 반영
- `src/pages/EmployeeLanding.jsx` 신규, `App.jsx` 라우트 1개 추가, `LandingHeader.jsx` 버튼 라우트 교체(기존 동작 주석 보존)

### v1.0_260413 (작성자: @Antigravity / branch: main)
- 프론트엔드 구현 계획서 초기화
