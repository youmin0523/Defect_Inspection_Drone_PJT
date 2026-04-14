# 🚁 AeroInspect AI (Defect Inspection Drone Project)

## 📖 프로젝트 개요

AeroInspect AI는 자율 비행 드론과 인공지능(Reinforcement Learning, Vision AI)을 결합하여, 건축물 및 산업 현장의 결함을 실시간으로 탐지하고 3D 디지털 트윈 환경으로 매핑하는 통합 풀스택 플랫폼입니다.

---

## 🛠️ Onboarding Tutorial (새로운 팀원을 위한 셋업 가이드)

본 프로젝트를 처음 클론(Clone) 받으신 개발자분들은 작업을 시작하기 전 **반드시 아래 순서대로 초기 환경을 구성**하시기 바랍니다.

### Step 1: Git 환경 세팅 (가장 중요 🌟)

우리 팀은 "투명하고 질서 있는 코드 베이스"를 지향합니다. 변경 내역을 알아볼 수 없는 `수정1` 같은 의미 없는 커밋을 원천 차단하기 위해 **Git Commit Hook 검사기**를 적용합니다.
터미널 창(루트 디렉토리)에서 아래의 명령어를 단 한 번! 실행해 주세요.

```bash
git config core.hooksPath .githooks
```

_(세팅을 완료하면 커밋 시 잘못된 형식을 작성했을 때 자동으로 에러를 내며 차단해 줍니다.)_

### Step 2: 팀 내 특수 규칙 (AI Vibe Coding)

우리 팀은 **AI(Cursor, Claude, Gemini 등) 에이전트와의 페어 프로그래밍(Vibe Coding)**을 적극 권장합니다.

- AI로 기능 개발이나 버그 수정을 진행할 경우, 가장 먼저 AI에게 루트에 있는 `team_project_rules.md`를 읽으라고 지시하세요.
- AI가 생성하고 트러블슈팅한 모든 의사결정 내역은 로컬의 `Vibe_Coding_Log.md` 파일에 마크다운 형식으로 차곡차곡 쌓이게 됩니다.

### Step 3: Notion 자동 동기화 구조 이해 (정보성)

우리 프로젝트는 팀원들이 각자 작성해준 `Vibe_Coding_Log.md` 내용이 **팀 리드(Admin)의 리뷰와 `git pull` 과정을 거칠 때 중앙 노션(Notion)에 한 번에 자동 통합**되는 중앙 집중식 파이프라인을 가집니다.
따라서 **일반 팀원분들은 별도의 API 키 발급 파일(`.env`)을 만드실 필요가 전혀 없습니다!** 그저 AI와 함께 코딩하시고, `Vibe_Coding_Log.md`가 수정되면 기존 코드들과 함께 평소처럼 Commit & Push 해주시기만 하면 됩니다. (노션 동기화는 리드 개발자 PC에서 알아서 백그라운드 처리됩니다 😎)

---

## 💻 커밋 규칙 (Conventional Commits)

위의 Step 1 설정을 마쳤다면 앞으로 모든 커밋 메시지는 **최소 10자 이상**이어야 하며, 아래 접두사 중 하나로 시작해야 합니다.

- `feat:` (새로운 기능을 추가할 때)
- `fix:` (에러, 버그 등을 수정할 때)
- `docs:` (README 등 문서를 수정할 때)
- `style:` (코드 포맷팅 관련 처리, 동작 변동 없음)
- `refactor:` (동작 변동 없이 내부 로직의 개선 및 리팩토링)
- `test:` (테스트 코드 수정, 추가)
- `chore:` (패키지 설정, 빌드 파일, 설정 변경 등)

👉 **멋진 사용 예시**: `feat: 드론 이동 경로 최적화 강화학습(RL) 로직 추가`

---

## 📂 파일 구조 컨텍스트

- `/frontend` : React 기반 3D (R3F) 디지털 트윈 모니터링 대시보드
- `/backend` : FastAPI 기반 YOLO 비전 판독 및 데이터베이스 연동 엔진
- `.githooks/` : 전사적 공통 Git 검사 스크립트 모음
- `sync_notion_logs.py` : 로그를 노션 워크스페이스로 던져주는 자동화 파이썬 엔진
- `team_project_rules.md` : 풀스택 개발 및 AI 에이전트 행동 지침명세서

---

**Happy Vibe Coding! 💡**
기록을 두려워하지 말고 함께 최고의 플랫폼을 개발해 봅시다! 🎉
