# Task.md

## 프로젝트 개요
- **목적**: 드론을 활용한 아파트 사전 점검 자동화 플랫폼 (AeroInspect AI) 개발
- **주요 스택**: React, React Three Fiber, FastAPI/Standard Python, PostgreSQL, WebSocket

- [x] v1.0 - 팀 프로젝트 협업 가이드 적용 및 프로젝트 초기화 (작성자: @youminsu0523 / branch: MS)
- [x] v1.1 - 백엔드/프론트엔드 개별 문서 구조 분화 (작성자: @youminsu0523 / branch: MS)
- [x] v1.2 - 팀 가이드라인 Gemini 대응 업데이트 (작성자: @youminsu0523 / branch: MS)
- [x] v1.3 - 자동 규칙 참조를 위한 .clauderules, .geminirules 생성 (작성자: @youminsu0523 / branch: MS)
- [x] v1.4 - 별전 레포지토리 이전 대비 가이드라인 복제 (작성자: @youminsu0523 / branch: MS)
- [x] v1.5 - 독립 레포지토리 가이드라인 무결성 강화 (작성자: @youminsu0523 / branch: MS)
- [x] v1.6 - 프로젝트 구조 분석 완료: 하이레벨 아키텍처 및 데이터 플로우 명세 (작성자: @youminsu0523 / branch: MS)
- [ ] v1.7 - 서브 모듈(Backend/Frontend) 상세 분석 및 API 문서화 (작성자: @youminsu0523 / branch: MS)

## 요구사항
1. `team_project_rules.md`에 명시된 모든 협업 규칙 준수
2. 시니어 멘토 모드로 개발 가이드 제공
3. 코드 수정 시 Better Comment (`// //!`, `// //*`) 규칙 적용
4. 모든 답변에 필수 보고서 (Scope, Refactoring, Checklist 등) 포함

## Revision History

### v1.6_260413 (작성자: @youminsu0523 / branch: MS)
**[Root]**
- 완료: 프로젝트 전체 아키텍처 및 데이터 플로우 전수 조사
- 문서: `Implementation_Plan.md`에 시스템 구조 및 데이터 여정(Data Journey) 기록 완료

### v1.5_260413 (작성자: @youminsu0523 / branch: MS)
**[Root]**
- 수정: `backend`, `frontend` 개별 레포지토리용 가이드라인의 "독립적 루트" 인식 강화
- 확인: `.clauderules`, `.geminirules` 내용 동기화 완료

### v1.3_260413 (작성자: @Antigravity / branch: main)
**[Root]**
- 추가: `.clauderules`, `.geminirules` 생성. 팀원들이 `git pull` 시 별도 설정 없이 AI가 규칙을 자동 참조하도록 개선

### v1.2_260413 (작성자: @Antigravity / branch: main)
**[Root]**
- 수정: `team_project_rules.md` 내 "Claude 전용" 문구를 "AI 어시스턴트 공통"으로 수정 및 Gemini 대응 명시

### v1.1_260413 (작성자: @Antigravity / branch: main)
**[Root]**
- 수정: 프로젝트 문서를 `backend/`, `frontend/`로 분화하여 관리 규칙 업데이트
- 추가: 각 디렉토리 내부 `Task.md`, `Implementation_Plan.md` 생성

### v1.0_260413 (작성자: @Antigravity / branch: main)
**[Root]**
- 추가: `Task.md`, `Implementation_Plan.md` 초기 생성
- 설정: `team_project_rules.md` 기반 협업 가이드라인 시스템 적용
