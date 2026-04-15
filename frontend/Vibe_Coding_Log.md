# 🤖 바이브코딩(Vibe Coding) 프롬프트 & 결과 추적 로그

> **💡 설명**: 프론트엔드(Frontend) 전용 바이브코딩 로그입니다. AI에게 언제, 어떤 프롬프트를 입력하여 어떤 코드를 도출했는지 기록합니다.

---

## 📝 기본 정보 (Meta)

- 작성자 (Who): @youminsu0523
- 작성 일자 (When): 2026-04-14 17:35   <!-- 착수(질문) 시점 — YYYY-MM-DD HH:MM -->
- 목표 기능 (Objective): AeroInspect 드론 하자점검 플랫폼 프론트엔드 전체 스캐폴드 구축 (React18 + Vite + Tailwind + R3F 3D 대시보드)
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
- **카메라 전환 UI**: `CameraToggle.jsx` 버튼 클릭 → `POST /api/v1/stream/mode` 호출 + `droneStore.setCameraMode()` 낙관적 업데이트
- **droneStore cameraMode**: `"rgb" | "thermal" | "blend"` 상태, WS `camera.mode_changed` 이벤트로 멀티클라이언트 동기화
- **LiveVideoFeed**: `key={streamUrl}` 속성으로 모드 변경 시 `<img>` 강제 리마운트 (MJPEG 스트림 재연결)

### 3️⃣ 구현된 프론트엔드 핵심 아키텍처

#### Zustand 스토어 설계
```javascript
// store/defectStore.js — 하자 데이터 관리
{
  defects: [],          // 최대 500개 (오래된 항목 자동 삭제)
  filters: { severity: 'ALL', area: 'ALL', categoryCode: null },
  selectedDefect: null,
  addDefect(d),         // WS defect.new 이벤트 수신 시 호출
  getFilteredDefects(), // 필터 적용 후 반환
  getSeverityCounts(),  // HIGH/MED/LOW 카운트
}

// store/droneStore.js — 드론 상태 관리
{
  connectionStatus: 'disconnected', // connected/reconnecting/disconnected
  telemetry: { altitude, battery, speed, heading, signal },
  cameraMode: 'rgb',    // 'rgb' | 'thermal' | 'blend'
  setCameraMode(mode),
  syncCameraMode(mode), // WS 이벤트 수신 시 다른 클라이언트 동기화
}
```

#### WebSocket 자동 재연결 (지수 백오프)
```javascript
// hooks/useWebSocket.js 핵심 패턴
const reconnect = useCallback(() => {
  delay = Math.min(delay * 2, 30000)  // 1s → 2s → 4s ... 최대 30s
  setTimeout(connect, delay)
}, [])

// 메시지 라우팅
"defect.new"          → defectStore.addDefect(payload)
"telemetry.update"    → droneStore.updateTelemetry(payload)
"camera.mode_changed" → droneStore.syncCameraMode(payload.mode)
"ping"                → ws.send(JSON.stringify({type:"pong"}))
```

#### React Three Fiber 3D 하자 마커
```javascript
// components/map3d/DefectMarker.jsx
// LiDAR 좌표 매핑: lidar_z(고도) → Three.js Y축
const x = defect.lidar_x ?? 0
const y = defect.lidar_z ?? 1  // Z(고도)를 Three.js Y축으로 매핑
const z = defect.lidar_y ?? 0

// 선택된 마커 펄스 애니메이션
useFrame(() => {
  if (isSelected) mesh.scale.setScalar(1.2 + Math.sin(Date.now() * 0.005) * 0.15)
})
```

#### LLM 보고서 스트리밍
```javascript
// api/reportApi.js — fetch ReadableStream 청크 수신
const reader = response.body.getReader()
while (true) {
  const { done, value } = await reader.read()
  if (done) break
  onChunk(new TextDecoder().decode(value))
}
```

---

## ✅ 최종 결과 (Final Outcome)

### 📁 생성된 프론트엔드 파일 목록 (34개)
- `package.json` — react@18, zustand@5, recharts@2, @react-three/fiber@8, @react-three/drei@9, three@0.170, axios, date-fns
- `vite.config.js` — `/api`, `/ws`, `/stream` → localhost:8000 프록시
- `tailwind.config.js` — brand, severity.high/med/low, dashboard.bg/surface/border 커스텀 컬러
- `src/App.jsx` — BrowserRouter + Header + Sidebar + Routes, 최상위에서 `useWebSocket()` 호출
- `src/store/defectStore.js` / `droneStore.js` — Zustand 상태 관리
- `src/hooks/useWebSocket.js` — 지수 백오프 재연결 + 메시지 라우팅
- `src/components/video/LiveVideoFeed.jsx` — `key={streamUrl}` 강제 리마운트로 스트림 전환
- `src/components/video/CameraToggle.jsx` — RGB/열화상/블렌드 전환 버튼
- `src/components/defects/DefectPanel.jsx` — 심각도 필터 탭 + 스크롤 목록
- `src/components/charts/ThermalGraph.jsx` — Recharts 슬라이딩 윈도우 실시간 그래프
- `src/components/map3d/BuildingScene.jsx` — R3F Canvas + OrbitControls (lidar_x/y/z 있는 하자만 마커)
- `src/components/map3d/DefectMarker.jsx` — 심각도별 색상 구체 + 펄스 애니메이션 + Html 툴팁
- `src/components/report/ReportPanel.jsx` — Claude/Gemini 선택 + 스트리밍 실시간 표시
- `src/components/report/ReportExport.jsx` — 마크다운 클립보드 복사 + .md 파일 다운로드
- `src/constants/defectCategories.js` — 20종 하자 정의 (5개 영역 A-E, 심각도 매핑)

### 📊 UI 레이아웃 구조
```
Dashboard (12-col grid)
├── [col-span-7] 좌측 패널
│   ├── LiveVideoFeed + CameraToggle  ← MJPEG 스트림
│   ├── ThermalGraph                  ← Recharts 실시간 그래프
│   └── BuildingScene (R3F)           ← 3D 하자 위치 맵
└── [col-span-5] 우측 패널
    ├── DefectPanel                   ← 하자 목록 + 필터
    └── ReportPanel + ReportExport    ← LLM 보고서
```

---

## 💡 배운 점 및 인사이트 (Lessons Learned)

- **MJPEG 스트림 전환**: `<img src>` 변경만으로는 브라우저가 기존 스트림 연결을 재사용할 수 있어, `key={streamUrl}` 패턴으로 DOM 요소 강제 재생성이 필요
- **R3F LiDAR 좌표 매핑**: 드론 좌표계(X=동서, Y=남북, Z=고도)와 Three.js 좌표계(Y=상하) 불일치 → `lidar_z`를 Three.js Y축으로 매핑
- **Zustand 최대 항목 제한**: WS를 통해 지속적으로 들어오는 하자 데이터가 메모리를 무한 누적하지 않도록 `addDefect`에서 500개 초과 시 오래된 항목 자동 제거
- **WS 재연결 전략**: 지수 백오프(1s→30s max) + 백그라운드 탭 처리(`visibilitychange` 이벤트)로 안정적인 연결 유지

### 4️⃣ 트러블슈팅 및 디버깅 (Troubleshooting)
- **이슈 (Issue)**: 프론트엔드 실행 시 `Maximum update depth exceeded` 무한 루프 렌더링 에러 발생 (빈 화면 출력).
- **원인 (Root Cause)**: `Header.jsx`와 `DefectPanel.jsx`에서 Zustand의 셀렉터(예: `getFilteredDefects()`)를 직접 함수로 파생하면서, 렌더링마다 매번 새로운 배열(참조값)을 반환했습니다. 이에 따라 리액트는 상태가 변경된 것으로 착각하여 무한정 재렌더링 트리거.
- **해결 (Solution)**:
  - Zustand 스토어에서 상태를 원시 배열(`state.defects` 등) 단위로만 구독하여 불필요한 재렌더링 방지.
  - 리렌더링 시 발생하던 불필요한 참조 변경을 개선하여 안정적인 렌더링 보장 완료.

---

### 5️⃣ 추가 피드백 & 반영 (Feedback Iterations)

> *초기 구현 이후, 협업 도구(Notion 싱크) 품질을 높이기 위한 피드백 라운드 기록*

#### ⏱ 2026-04-14 17:40 | 노션 타임스탬프 기준 변경
- **피드백**: Notion에 찍히는 시간이 싱크 실행 시각이라, 팀원들의 로그를 합쳤을 때 시간순이 뒤죽박죽됨. "질문(착수) 시점" 기준으로 바꿔달라.
- **반영**:
  - `sync_notion_logs.py`의 `extract_meta()`를 수정하여 `작성 일자 (When)` 필드에서 `YYYY-MM-DD HH:MM` 포맷을 파싱.
  - `append_session_to_page()`가 파싱된 착수 시각을 우선 사용하고, 없을 때만 현재 시각으로 폴백.
  - 로그 템플릿의 When 필드 포맷을 `2026-04-14 17:35`처럼 시분 포함으로 갱신.

#### ⏱ 2026-04-14 17:42 | Notion UI 디자인 개선
- **피드백**: 세션 블록이 단조로움 — 디자인을 좀 더 신경써달라.
- **반영**:
  - 영역별 이모지 헤딩 (`🎨 [Frontend]`, `⚙️ [Backend]`)
  - 메타 콜아웃(회색 배경): `🕒 착수 HH:MM · 👤 @author · 🌿 branch`
  - 스크린샷을 세션 상단으로 이동 → 시각적 훅 강화

#### ⏱ 2026-04-14 17:46 | 파일트리/코드블록 가독성 복구
- **피드백**: 이전에 보이던 파일 구조 트리가 사라졌음. 접힘 없이 바로 보이게 해달라.
- **원인**: UI 개선 과정에서 본문 전체를 "📝 상세 로그 펼치기" 토글로 감쌌더니, 트리처럼 시각적으로 중요한 코드블록이 접혀 안 보임.
- **반영**: 토글 제거, 본문 블록을 그대로 노출하도록 `append_session_to_page()` 재수정. 메타 콜아웃과 상단 스크린샷은 유지.

#### ⏱ 2026-04-14 17:55 | 피드백 흐름도 로그에 기록
- **피드백**: 초기 질문과 결과만이 아닌, 피드백/수정 요구 라운드도 대화 흐름에 시각과 함께 남겨달라. 팀원 로그를 합쳐도 시간순 추적이 가능하도록.
- **반영**: 본 `5️⃣ 추가 피드백 & 반영` 섹션 신설. 이후 라운드마다 `⏱ YYYY-MM-DD HH:MM | 피드백 → 반영` 형식으로 append하는 규칙을 정립.

---

### 6️⃣ 랜딩 페이지 섹션 확장 & 스크롤 UX (2026-04-15)

#### ⏱ 2026-04-15 | "서비스 소개" HTML → React 변환
- **피드백**: 제공된 서비스 소개 정적 HTML(다크 배너 + 3개 가치 카드: 안전성/정밀성/효율성)을 리액트 컴포넌트로 이식해달라.
- **반영**:
  - `components/landing/ServiceIntroSection.jsx` 신설. 카드 데이터 배열 + `map`으로 DRY화, Tailwind JIT 안전을 위해 accent별 full class name 매핑(`ACCENT_STYLES`).
  - `pages/Landing.jsx`에 `<ServiceIntroSection />` 삽입(Hero 아래).
  - 원본 `<h1>` → `<h2>`로 강등(페이지 h1은 HeroSection이 소유). 중복되는 `<header>`/CDN Tailwind 태그는 제외.

#### ⏱ 2026-04-15 | 네비 구조 확인 — 싱글페이지 스크롤 방식
- **피드백**: "서비스 소개" 클릭 시 페이지 이동이 아닌 같은 페이지 내 스크롤로 동작하는 거냐? 위치 확인하고 스크롤 이펙트 줘라.
- **확인 결과**:
  - `LandingHeader`의 네비 링크가 `#intro` / `#features` / `#cases` 앵커.
  - `#cases` 타겟 부재 → 클릭해도 동작 안 함.
  - Sticky 헤더(80px)에 섹션 제목이 가려지는 문제 → `scroll-mt` 보정 필요.

#### ⏱ 2026-04-15 | 핵심 기술 섹션 — 기존/신규 내용 융합
- **피드백**: 기존 FeaturesSection(3가지 모델링 파이프라인)과 새로 전달한 "핵심 기술 스택"(3D 복원 / AI 분석 / 공간 매핑)을 병합해달라.
- **반영**: `FeaturesSection.jsx` 전면 재작성. 3개 기술 축을 카드로 세우고, 첫 카드(MODELING) 하단에 기존 3개 파이프라인(`CAD 연동`·`2D 역설계`·`자율비행 스캔`)을 칩(chip) 리스트로 품음 → 중복 제거 + 정보 손실 없음.

#### ⏱ 2026-04-15 | 도입 사례 섹션 신설 + 스크롤 이펙트 통합
- **피드백**: 제공된 "도입 사례" HTML(B2B 건설사 / 정밀 안전진단 / B2C 입주민 3개 카드)을 반영하고, 스크롤 이펙트/앵커 오프셋까지 한번에 처리해달라.
- **반영**:
  - `components/landing/CasesSection.jsx` 신설, `id="cases"` + `scroll-mt-20 md:scroll-mt-24`.
  - `pages/Landing.jsx`에 `<CasesSection />` 연결 → `#cases` 앵커 활성화.
  - `hooks/useReveal.js` + `components/common/Reveal.jsx` 추가. IntersectionObserver 기반 "뷰포트 진입 시 1회 페이드업" 패턴. `prefers-reduced-motion` 존중, `delay` prop으로 카드 스태거(120ms 간격) 연출.
  - `ServiceIntroSection` / `FeaturesSection` / `CasesSection` 카드에 `<Reveal>` 래핑 적용.
  - `index.html` `<html>`에 `scroll-smooth` 클래스 추가 → 앵커 점프가 부드럽게 스크롤되도록.
  - 모든 섹션에 `scroll-mt-20 md:scroll-mt-24` 적용하여 sticky 헤더에 제목이 가려지는 문제 해소.

#### ⏱ 2026-04-15 | 앵커 스크롤 속도 커스터마이즈
- **피드백**: 네비 메뉴를 눌렀을 때 섹션으로 넘어가는 속도가 너무 빠르다. 조금 더 느긋하게 넘어가면 좋겠다.
- **원인**: CSS `scroll-smooth`는 브라우저가 자체 속도로 애니메이션해서 duration 제어가 불가.
- **반영**:
  - `utils/smoothScroll.js` 신설 — rAF + easeInOutCubic 기반 커스텀 스크롤. duration/headerOffset 파라미터화, `prefers-reduced-motion` 존중, 휠/터치/키 입력 시 즉시 중단.
  - `LandingHeader`의 네비 `<a>`에 `onClick={handleAnchorClick(...)}` 연결 → 기본 점프를 가로채 1100ms easeInOutCubic으로 부드럽게 이동, 헤더 오프셋 96px 보정.

#### ⏱ 2026-04-15 | 이징 커브 교정 (즉시 출발 + 느긋한 도착)
- **피드백**: "누르면 바로 움직이되 내려가는 속도를 늦춰라"는 의도였는데, 현재 구현은 시작도 느리게 움직여서 멈칫한 느낌이 난다.
- **원인**: `easeInOutCubic`은 시작(t=0)과 끝(t=1) 모두 속도 0 → 클릭 직후 "멈칫" 후 가속하는 체감.
- **반영**: `smoothScroll.js`의 이징을 `easeOutCubic`으로 교체 (t=0 속도 최대 → 감속하며 정지). duration은 1100 → 1400ms로 소폭 증가하여 "느긋하게 도착하는" 느낌 강화.

#### ⏱ 2026-04-15 | 초기 가속 추가 강화 (easeOutQuart)
- **피드백**: easeOutCubic도 클릭 직후 움직이기까지 살짝 뜸을 들이는 느낌이다. 그 지연을 더 줄여달라.
- **원인**: easeOutCubic은 t=0에서의 파생값이 3 → 초기 몇 프레임의 변위가 작아 체감상 "딜레이".
- **반영**: `easeOutQuart`(파생값 4)로 교체. 첫 프레임부터 더 큰 변위가 발생하여 "누르자마자 팍" 출발하는 체감. 감속은 더 급격하지만 도착은 여전히 부드러움 유지.

#### ⏱ 2026-04-15 15:42 | 서비스 소개 첫 카드 카피 교체 (실내 사각지대 강조)
- **피드백**: 첫 번째 카드(SAFETY FIRST / 고소 작업 사고율 0%)가 외벽 점검 맥락이라, 실내 하자점검 서비스의 차별점과 어긋난다. 3개 옵션 중 "옵션 1 — 접근성 & 사각지대 해소"로 교체해달라.
- **반영**: `ServiceIntroSection.jsx`의 `VALUE_CARDS[0]`를 아래로 교체 (accent=blue 유지).
  - kicker: `SAFETY FIRST` → `BLIND SPOT ZERO`
  - tag: `안전성` → `접근성`
  - title: `고소 작업 사고율 0%` → `실내 난접근 구역 사각지대 0%`
  - desc: 외벽 로프 작업 대체 문구 → "높은 천장·좁은 틈새·어두운 배관/공조실 등 실내 사각지대를 드론이 진입해 빈틈없이 스캔" 문구로 교체.

#### ⏱ 2026-04-15 15:45 | 가치 카드 키커 영역 비중 축소
- **피드백**: `BLIND SPOT ZERO` / `ACCURACY` / `EFFICIENCY` 같은 영문 키커가 본문보다 더 큰 공간을 차지해 시선이 분산된다.
- **반영**: `ServiceIntroSection.jsx` 키커 패널을 `h-48 → h-20`, 글자 `font-bold text-lg → font-semibold text-xs tracking-[0.2em]`로 축소. 컬러 띠 + 태그라인 성격만 유지하고 본문(title/desc)이 카드의 주연이 되도록 레이아웃 재정돈.

#### ⏱ 2026-04-15 15:48 | 키커 재강조 (디스플레이 타이포)
- **피드백**: 직전 축소가 너무 과했다. `BLIND SPOT ZERO` 같은 키커를 좀 더 강조해달라.
- **반영**: 패널 `h-20 → h-28`, 글자 `text-xs → text-2xl md:text-3xl`, `font-semibold → font-extrabold`, tracking은 `0.2em → 0.15em`로 약간 타이트하게. 본문 영역은 침범하지 않으면서 "컬러 히어로 타이포" 느낌으로 키커가 시선을 잡도록 조정.

#### ⏱ 2026-04-15 15:52 | 키커 방향 전환 — 크기 대신 굵기 + 그라데이션
- **피드백**: 크기 강조가 원했던 방향이 아니다. 폰트를 더 두껍게 하고 그라데이션으로 강조해달라.
- **반영**: 사이즈 `text-2xl md:text-3xl → text-xl md:text-2xl`, 굵기 `font-extrabold → font-black`, 패널 `h-28 → h-24`로 소폭 축소. `ACCENT_STYLES`의 단색 `kickerText`를 `kickerGradient`로 교체 — accent별 3-stop 그라데이션(blue: blue-700→blue-500→sky-400 / yellow: amber-600→yellow-500→orange-400 / green: green-700→emerald-500→teal-400)을 `bg-gradient-to-r + bg-clip-text + text-transparent`로 텍스트에 적용. 크기로 밀지 않고 색과 굵기로 무게감을 주는 방향.

#### ⏱ 2026-04-15 15:56 | 키커 글리프 팻닝 + 자간 타이트
- **피드백**: 폰트를 더 두껍게 해달라 + 자간도 줄여달라.
- **제약**: Tailwind 폰트 weight 최대치(`font-black` = 900)를 이미 사용 중 → 추가 굵기는 CSS 수준에서 글리프 윤곽선을 덧씌워야 함.
- **반영**: `ACCENT_STYLES`에 `kickerStroke` 추가 — `[-webkit-text-stroke:1px_<accent-700>] [paint-order:stroke_fill]` 조합으로 각 accent의 짙은 톤을 외곽선에 얹음. `paint-order: stroke fill`로 스트로크를 먼저 깔아 그라데이션 fill이 위에 찍히게 해 색 손상 최소화. 자간은 `tracking-[0.12em] → tracking-[0.06em]`로 축소해 글리프 밀도를 높임 → "두껍고 꽉 찬" 디스플레이 타이포 느낌.

#### ⏱ 2026-04-15 16:05 | 한글 단어 중간 줄바꿈 방지 (break-keep 일괄 적용)
- **피드백**: Hero에서 "3D 모델링,"이 "모델" / "링," 으로 쪼개지고, 카드 본문에서 "안전하게"가 "안" / "전하게"로 쪼개지는 등 한글 단어 중간 wrap이 어색하다.
- **원인**: 기본 `word-break: normal`은 CJK에서 음절 단위로 끊음.
- **반영**: 한글 카피 전체에 Tailwind `break-keep`(= `word-break: keep-all`) 일괄 적용.
  - `HeroSection.jsx`: `<h1>`, 서브 `<p>`.
  - `ServiceIntroSection.jsx` / `CasesSection.jsx` / `FeaturesSection.jsx`: 카드 `<h3>` 제목 + `<p>` 설명.
  - 공백/문장부호 기준으로만 줄바꿈되도록 통일 → "모델링"·"안전하게" 같은 복합어가 한 덩어리로 움직임. 영문/숫자 혼합 토큰(`3D`, `0.1mm` 등)은 원래도 분리되지 않음.

#### ⏱ 2026-04-15 16:12 | 로고 클릭 → 최상단 스크롤 동작 수정
- **피드백**: 좌측 상단 로고를 눌러도 페이지 최상단으로 올라가지 않는다.
- **원인**: 로고가 `<Link to="/">`인데, 이미 `/` 경로에 있는 경우 react-router가 리렌더·네비게이션을 트리거하지 않아 스크롤이 전혀 발생하지 않음.
- **반영**: `LandingHeader.jsx`에 `useLocation` + `handleLogoClick` 추가. `location.pathname === '/'`이면 `event.preventDefault()` 후 `smoothScrollTo(0, 1000)`으로 최상단까지 스무스 스크롤(네비 메뉴와 동일한 `easeOutQuart`, 1000ms). `replaceState`로 해시도 정리. 다른 경로(예: `/dashboard`)에서 로고를 누르면 기존대로 `/`로 라우팅.

#### ⏱ 2026-04-15 16:20 | B2C 카드 설명 문구 구체화 (실내 하자 요소 명시)
- **피드백**: "프리미엄 개별 세대 리포트" 카드 설명이 "샷시 외부 및 외벽 상태"로 되어 있어, 실내 하자점검 서비스 맥락과 어긋난다. 3개 옵션 중 "옵션 1 — 직관성 강조"(도배/마루/마감재 등 구체적 하자 요소 명시)로 교체해달라.
- **반영**: `CasesSection.jsx`의 `CASE_CARDS[b2c].desc`를 "세대주가 직접 접속하여 도배, 마루, 마감재 등 실내 공간의 하자 상태를 3D 뷰어로 확인하고 보수 이력을 트래킹."으로 교체. 세대주가 일상에서 마주치는 구체 요소를 노출해 서비스 직관성을 높이고, B2C 카드가 실내 스캔 포지션과 정렬되도록 조정.

#### ⏱ 2026-04-15 16:28 | B2B 건설사 카드 카피 교체 (규모·확장성 강조)
- **피드백**: B2B 건설사 카드가 "외벽 및 로프 접근 불가 구역" 중심이라 실내 전수조사 서비스 포지션과 어긋난다. 3개 옵션 중 "옵션 1 — 규모/확장성 강조"로 교체해달라.
- **반영**: `CasesSection.jsx`의 `CASE_CARDS[b2b]` 제목을 "수도권 1,500세대 신축 점검" → "대규모 신축 단지 실내 전수조사"로, desc를 "수천 세대 규모의 현장도 문제없이 완벽한 전수조사 지원. 기존 인력 대비 점검 기간을 60% 단축하며, 전 세대 내부 마감재 스캔 및 하자 리포트를 일괄 제출합니다."로 교체. 외벽/로프 뉘앙스를 제거하고 실내 전수조사·확장성 메시지로 정렬.

#### ⏱ 2026-04-15 16:35 | 정밀 안전진단 카드 카피 교체 (문제 해결 직관성 강조)
- **피드백**: "준공 20년 차 주상복합 진단" 카드가 특정 사례 한 건 느낌이라 서비스 포괄성을 덜 전달한다. 3개 옵션 중 "옵션 1 — 직관적인 문제 해결 강조"로 교체해달라.
- **반영**: `CasesSection.jsx`의 `CASE_CARDS[diagnosis]` 제목을 "준공 20년 차 주상복합 진단" → "도면 미보유 노후 건축물 정밀 진단"으로, desc를 "도면이 소실되거나 현행화되지 않은 현장이라도 문제없습니다. 드론 자율비행(Photogrammetry)을 통해 실내 3D 디지털 트윈을 즉각 생성하고 숨은 결함을 분석합니다."로 교체. 한 건의 사례 소개 톤에서 "도면 없는 현장도 해결" 포지션으로 메시지 확장.

#### ⏱ 2026-04-15 16:48 | FeaturesSection 카드 비주얼 도입 (코드 스트립 → 이미지 + 코드 오버레이)
- **피드백**: 핵심 기술 섹션 3개 카드가 회색 placeholder + 코드 라벨만 있어 비주얼이 빈약하다. MODELING 카드에 "건물 와이어프레임 3D 복원" 이미지를 우선 적용하고, AI/MAPPING도 같은 구조로 확장 가능한 틀을 잡아달라.
- **자산**: `frontend/src/assets/features/{modeling,ai,mapping}/` 3개 폴더 신설. MODELING 카드용 `01-wireframe-building.png`(268KB, 건물 와이어프레임 적·청 2톤) 배치. 파일명에 `.webp.png` 이중 확장자로 들어와 `.png`로 정리.
- **반영**: `FeaturesSection.jsx`에 `import.meta.glob`(eager + `?url`) 패턴을 추가해 각 카드 폴더의 이미지를 정렬된 URL 배열로 수집(`modelingImages`/`aiImages`/`mappingImages`). `TECH_CARDS` 각 엔트리에 `image: <firstImage>` 필드 주입. 상단 비주얼 영역을 `relative h-48 overflow-hidden`로 바꾸고, `card.image`가 있으면 `<img object-cover>` + 다크 반투명 배경의 `<span>` 코드 라벨 오버레이를, 없으면 기존 코드 스트립을 폴백으로 렌더. 호버 시 `scale-105 duration-500`로 약간의 줌 효과. AI/MAPPING 폴더에 이미지를 추가하면 즉시 동일 스타일로 반영됨(코드 수정 불필요).

#### ⏱ 2026-04-15 17:05 | AI / MAPPING 카드 이미지 추가
- **피드백**: MODELING 카드만 이미지가 있고 AI/MAPPING은 placeholder 상태. 각 카피와 어울리는 Unsplash 이미지 톤(다크/그레이/세피아) 추천 후 확정된 이미지 2장 배치.
- **반영**: `features/ai/01-concrete-crack.png`(콘크리트 균열 클로즈업 — "픽셀 단위 하자 식별" 카피 직결), `features/mapping/01-isometric-floor-plan.png`(아이소메트릭 실내 평면도 스케치 — "X, Y, Z 정밀 공간 매핑" 카피 직결) 배치. 기존 `import.meta.glob` 자동 수집 구조 덕분에 컴포넌트 코드 수정 없이 새로고침만으로 반영. 3개 카드가 "다크 네온 / 그레이 리얼 / 세피아 스케치"로 톤이 분기되어 "복원 → 분석 → 매핑" 프로세스 스토리라인 형성.

#### ⏱ 2026-04-15 17:15 | 코드 라벨 워터마크화 (중앙 pill → 우측 하단 은은한 태그)
- **피드백**: 이미지가 들어오면서 중앙의 코드 라벨(`// 3D_RECONSTRUCTION_ENGINE` 등)이 과하다. 삭제 대신 "은은한 워터마크" 스타일로 톤 다운.
- **반영**: `FeaturesSection.jsx`에서 코드 라벨 스타일을 `relative z-10 text-white/90 text-xs bg-slate-900/60` → `absolute bottom-2 right-2 z-10 text-white/60 text-[10px] tracking-wider bg-slate-900/30`으로 교체. 위치를 중앙에서 우측 하단 구석으로 이동해 이미지 주제를 가리지 않으면서 시스템 식별자(테크 아이덴티티)는 유지. 패딩도 `px-2 py-1 → px-1.5 py-0.5`로 축소, `tracking-wider`로 모노스페이스 가독성 확보.

#### ⏱ 2026-04-15 17:25 | 코드 라벨 `//` 프리픽스 제거 + 라이브 상태 점 도입
- **피드백**: `//` 주석 프리픽스가 과하다. 다른 방식으로 표현해달라. 3가지 대안(브래킷 / 꺽쇠 / 상태 점) 중 "상태 점 + accent 컬러 펄스"를 선택.
- **반영**: `TECH_CARDS[*].code`에서 `//` 프리픽스 제거(순수 시스템 식별자만 노출). `ACCENT_STYLES`에 `dot` 필드 추가 — slate 카드는 `bg-cyan-400`(와이어프레임 블루와 매칭), indigo는 `bg-indigo-400`, orange는 `bg-orange-400`. 워터마크 `<span>`을 `flex items-center gap-1.5`로 바꾸고 1.5px 크기 원형 점을 라벨 앞에 배치. `animate-ping`으로 펄스 잔상 레이어를 겹쳐 "시스템 LIVE" 느낌 구현. 폴백(이미지 없는 경우)에도 동일 점 적용해 시각 언어 통일.

#### ⏱ 2026-04-15 17:35 | Hero 첫 줄 "모델링," 홀로 줄바꿈 해소
- **피드백**: Hero `<h1>` 첫 줄 "도면이 없어도 완벽한 3D 모델링," 중 "모델링,"만 다음 줄로 밀려 어색하다. 한 줄로 붙여달라.
- **원인**: 뷰포트 md 구간에서 `text-6xl`(60px) × 한글 18자 ≈ 1080px가 컨테이너 `max-w-4xl`(896px)을 초과해 공백 기준으로 자동 줄바꿈.
- **반영**: `HeroSection.jsx`의 h1 폰트 스케일을 `text-4xl md:text-6xl` → `text-4xl md:text-5xl lg:text-6xl`로 단계화. md 구간은 `text-5xl`(48px)로 낮춰 한 줄에 수용. 컨테이너도 `max-w-4xl` → `max-w-4xl lg:max-w-5xl`로 lg 이상에서 폭 여유 확보. 추가 안전장치로 해당 문구를 `<span className="md:whitespace-nowrap">`로 감싸 md 이상에서는 강제 한 줄 유지(모바일은 기본 줄바꿈 허용).
