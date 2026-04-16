# Frontend Task.md

## 프로젝트 개요
- **목적**: AeroInspect AI - 실시간 3D 대시보드 및 리포트 뷰어
- **주요 스택**: React, Three.js, React Three Fiber, Tailwind CSS

## 작업 목록
- [x] v1.0 - 프론트엔드 전용 협업 문서 초기화 (작성자: @youminsu0523 / branch: MS)
- [x] v1.1 - 독립 레포지토리 운영 대비 가이드라인 파일 복제 (작성자: @youminsu0523 / branch: MS)
- [x] v1.2 - Frontend 전용 독립 가이드라인 무결성 설정 완료 (작성자: @youminsu0523 / branch: MS)
- [ ] v1.3 - 프론트엔드 컴포넌트 구조 분석 및 3D 렌더링 검토 (작성자: TBD / branch: TBD)
- [x] v1.4 - 직원 전용 랜딩(`/employee` · Interior Inspection Dashboard) 신설 및 버튼 라우트 교체 (작성자: @youminsu0523 / branch: MS)
- [x] v1.5 - 직원 전용 랜딩 "사무실 허브" 형태로 전면 재설계 (v1 현장 HUD → v2 사무실 허브) (작성자: @youminsu0523 / branch: MS)

## 요구사항
1. `team_project_rules.md` 준수
2. JSX/TSX `// //!`, `// //*` Better Comment 규칙 적용
3. 모든 컴포넌트 반응형(`7-2`) 및 상태 UI(`7-1`) 처리 필수

## Revision History

### v1.5_260416 (작성자: @youminsu0523 / branch: MS)
**[src/pages/EmployeeLanding.jsx]** (전면 재작성 — v1 → v2)
- 교체: v1 "Interior Inspection Dashboard" (실시간 드론 HUD + 평면도 핀 + 결함 사이드패널) → v2 "사무실 허브" (Welcome/QuickActions/KPI/일정·알림/팀원/최근활동)
- 이유: `/employee` 는 **사무실 허브**, `/session/setup~/dashboard` 는 **현장 실무**라는 UX 경계 재정의 (사용자 피드백)
- 톤: 랜딩(`/`) 과 톤온톤 — `bg-gray-50` + 흰 카드 + slate-900 다크 배너 + blue/yellow/green accent
- 데이터: 현재 세션 실데이터(store) + 이번 달 목업 상수(`MOCK_*`) 혼용, 각 KPI 카드에 LIVE/MOCK 뱃지 명시
- 신규 섹션: 알림·공지, 팀원 현황 및 담당 현장 할당

**[team_project_rules / 메모리]**
- 추가: `project_ux_boundary_employee_vs_session.md` — 사무실/현장 UX 경계선 프로젝트 메모리화

### v1.4_260416 (작성자: @youminsu0523 / branch: MS)
**[src/pages/EmployeeLanding.jsx]** (신규)
- 추가: Interior Inspection Dashboard 목업 기반 직원 전용 랜딩 (상단 HUD 네비 + 실내 평면도 + Drone-Mini HUD + 결함 분석 패널)
- 추가: `DefectCard` 서브 컴포넌트로 하자 카드 중복 JSX DRY 처리
- 추가: `/session/setup`, `/dashboard/report` 로의 실용 링크 2개 (기존 플로우 보존)

**[src/App.jsx]**
- 추가: `EmployeeLanding` import + `<Route path="/employee" element={<EmployeeLanding />} />` 공개 라우트

**[src/components/landing/LandingHeader.jsx]**
- 수정: 직원 전용 `<Link>` `to="/session/setup"` → `to="/employee"` (기존 코드 `// //! [Original Code]` 주석 보존, Rule 3-2)
- 이유: 사용자 요청 — 직원 버튼 클릭 시 Interior Inspection 랜딩을 거치도록 플로우 변경

### v1.1_260413 (작성자: @youminsu0523 / branch: MS)
**[Frontend]**
- 추가: `.clauderules`, `.geminirules`, `team_project_rules.md` 복제 (독립 운영 가능)
