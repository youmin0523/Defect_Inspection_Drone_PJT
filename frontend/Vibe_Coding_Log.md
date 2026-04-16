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

#### ⏱ 2026-04-16 14:03 | 계정 찾기 페이지 신규 추가 (아이디/비밀번호 찾기)
- **피드백**: 백엔드(Node.js/Express)에서 `POST /api/find-id`(type/name/email/bizNumber) 와 `POST /api/find-pw`(type/userId/email/bizNumber) 를 Nodemailer 기반으로 구현 중. 이에 맞춰 프론트에 계정 찾기 UI를 추가하고, 사용자가 첨부한 HTML 목업(탭 2개 + 개인/사업자 토글 + 사업자번호 조건부 노출)을 프로젝트 톤에 맞춰 포팅해달라.
- **반영**:
  - `pages/FindAccount.jsx` 신규 생성. 상단 탭(`아이디 찾기` / `비밀번호 찾기`)은 Login/Signup 과 동일한 폰트·색 컨벤션을 따르되 목업의 "border-bottom 2px accent" 스타일을 유지. 탭 하부에 개인/사업자 세그먼트 컨트롤(선택 시 `bg-blue-50 border-blue-200 text-blue-700`) 배치, `isBusiness` 시에만 사업자등록번호 input 노출(숫자만 10자리, 자동 필터링).
  - 아이디 찾기 모드: `이름`(사업자 시 `담당자명`으로 라벨 변경) + 이메일. 비밀번호 찾기 모드: `아이디` + 이메일. 제출 버튼 컬러도 모드별로 분기(`slate-900` vs `blue-600`)해 시각적으로 모드 인지 가능.
  - 제출 payload 를 백엔드 스펙과 정렬: `{ type, email, bizNumber?, (name | userId) }`. 현재 단계에서는 실제 fetch 대신 `console.log` + 600ms 지연 mock 으로 남겨두고(주석 처리된 fetch 블록 포함), 상태(`idle / loading / success / error`)에 따라 상태 메시지 색상(slate/green/red) 표시.
  - URL 쿼리 `?tab=id|pw` 로 초기 탭 지정 + `handleModeChange` 시 `navigate('/find-account?tab=...', { replace: true })` 로 동기화해 북마크·뒤로가기 일관성 확보. `useEffect([location.search])` 로 외부에서 쿼리만 바뀌어도 탭이 따라오도록 처리.
  - `App.jsx` 에 `<Route path="/find-account" element={<FindAccount />} />` 추가(로그인/회원가입 그룹에 합침). `Login.jsx` 하단의 `<a href="#">아이디 찾기 | 비밀번호 찾기</a>` 를 `<Link to="/find-account?tab=id">`, `<Link to="/find-account?tab=pw">` 로 교체 — 클릭 시 해당 탭으로 바로 진입.
  - 타이틀 헤더는 Login 과 동일한 3분할 레이아웃(좌측 로고 / 중앙 제목 "계정 찾기" + 서브카피 "잃어버린 계정 정보를 안전하게 찾아드립니다." / 우측 "로그인으로..")로 통일. 하단에도 "로그인 화면으로 돌아가기" 언더라인 링크 유지.

#### ⏱ 2026-04-16 15:10 | 회원가입 사업자 진위 확인 — 국세청(odcloud.kr) API 실연동
- **피드백**: 사용자가 Node.js + axios 기반 공공데이터포털 "사업자등록정보 진위확인 및 상태조회" 샘플 코드를 제시하며, Signup.jsx 의 `verifyBusiness` 시뮬레이션(`setTimeout` mock)을 실제 API 연동으로 교체 요청. API 키는 `.env` 에 양식만 만들어두면 본인이 입력하겠다고 지정.
- **반영**:
  - `frontend/src/api/businessVerifyApi.js` 신규 생성. `checkBusinessStatus(b_no)` 함수가 `POST /api/nts-businessman/v1/status` 에 `{ b_no: [번호] }` 페이로드로 호출하고 `data[0]` 결과 객체 반환. `interpretStatus(result)` 헬퍼로 `b_stt_cd`(01 계속 / 02 휴업 / 03 폐업)에 따라 `{ ok, message }` 로 정규화 — 01 이면 과세유형을 포함한 성공 메시지, 02/03 은 상태별 한글 안내(폐업 시 `end_dt` 부착), 빈 응답이면 미등록 사업자 처리.
  - CORS 우회: `vite.config.js` `server.proxy` 에 `/odcloud → https://api.odcloud.kr`(rewrite 로 prefix 제거) 추가. dev 환경에서는 `import.meta.env.DEV` 체크해 `/odcloud/api/nts-businessman/v1` 경유, prod 는 직접 호출(필요 시 백엔드 프록시 전환 전제).
  - 키 관리: `.env.example` / `.env` 에 `VITE_ODCLOUD_SERVICE_KEY=` 항목 추가. 공공데이터포털 발급 "Decoding" 키를 그대로 붙여넣기. 키 미설정 시 API 함수가 즉시 Error throw 해 "환경변수 미설정" 메시지 노출. `VITE_` 접두사 env 는 번들에 노출됨을 주석에 경고로 기재.
  - `Signup.jsx` 상단에 `checkBusinessStatus, interpretStatus` import. 기존 `verifyBusiness`(1초 setTimeout mock → `bizNum === '0000000000'` 만 실패 처리하던 로직)를 async 함수로 교체. 유효성 체크(10자리 숫자 + 대표자명) 통과 시 `status: 'loading'` 세팅 → `checkBusinessStatus(bizNum)` 호출 → `interpretStatus(result).ok` 여부로 `success`/`error` 분기. catch 블록에서 `err.response.data.msg`/`message`/`err.message` 우선순위로 서버 오류 메시지 추출해 "조회 실패: ..." 포맷으로 표시.
  - 폼 필드는 그대로 유지(`bizNumber`/`bizCeoName`). status 엔드포인트 자체는 대표자명을 사용하지 않지만, 가입 레코드/회원 DB 저장용으로 계속 수집. (향후 `/validate` 엔드포인트로 전환 시 개업일자 입력 필드 추가 필요 — 현재는 사용자 UX 단순화를 위해 status 엔드포인트 유지.)

#### ⏱ 2026-04-16 15:22 | 사업자 진위확인 API — 랜딩 "도입 문의하기" 모달에도 확산 적용
- **피드백**: "현재 프로젝트에 관련된 사업자 진위여부 조회가 필요한 구간에 다 적용해줘" — 신규 구축한 `businessVerifyApi` 를 프로젝트 전반으로 확산 요청.
- **조사**: 프로젝트 내 `bizNumber`/`사업자`/`진위` 키워드 매치 5개 파일 전수 검토 — `Signup.jsx`(방금 연동 완료), `ContactModal.jsx`(진위 확인 버튼 + setTimeout mock 보유), `Login.jsx`(로그인 식별자로만 사용, 진위 확인 버튼 없음), `FindAccount.jsx`(계정 찾기 식별자로만 사용, 진위 확인 버튼 없음). 후자 2개는 이미 가입 단계에서 진위 검증이 끝난 사업자번호를 식별자로 쓰는 위치라 DB lookup 영역으로 판단 → 실제 진위확인 API 호출이 필요한 구간은 Signup + ContactModal 두 곳으로 확정.
- **반영**:
  - `components/landing/ContactModal.jsx` 상단에 `../../api/businessVerifyApi` 상대경로로 `checkBusinessStatus`, `interpretStatus` import.
  - `verifyBusiness` 를 async 로 전환. `setTimeout(1000) + bizNum === '0000000000'` 분기 mock 을 제거하고 `checkBusinessStatus(bizNum)` 호출 → `interpretStatus(result)` 로 `{ ok, message }` 정규화 → `ok ? '✅' : '❌'` 이모지 프리픽스 유지(기존 모달 UI 톤 보존)하며 상태 세팅. catch 블록에서 `err.response.data.msg`/`message`/`err.message` 순으로 서버 오류 추출해 "❌ 조회 실패: ..." 포맷으로 표시. 10자리 숫자 검증 로직은 유지(네트워크 호출 전 조기 실패).
  - Login/FindAccount 는 **의도적으로 제외** — 로그인·계정 찾기는 "이미 등록된 회원인지" 확인하는 단계지 "국세청에 존재하는지"를 확인하는 단계가 아님. 여기서 국세청 API 를 호출하면 DB 에 없는 사업자번호도 국세청 존재하면 통과시키는 의미 충돌이 생김. 포맷(10자리 숫자) 검증만 유지하고 실제 진위확인은 회원가입·도입문의 두 진입점에 한정.
  - 결과: 프로젝트 내 "사업자 진위 확인 버튼을 가진 모든 폼"이 단일 `businessVerifyApi` 모듈을 통해 odcloud.kr 에 직접 호출하는 구조로 통일. 키·엔드포인트·상태 코드 해석이 한 파일에 수렴해 향후 백엔드 프록시로 전환할 때 `BASE_URL` 한 곳만 바꾸면 됨.

#### ⏱ 2026-04-16 15:30 | 계정 찾기 헤더 서브카피 제거
- **피드백**: 계정 찾기 페이지 헤더의 "잃어버린 계정 정보를 안전하게 찾아드립니다." 서브카피를 빼달라 — 페이지 제목 "계정 찾기"만으로도 목적이 충분히 전달됨.
- **반영**: `FindAccount.jsx` 헤더 중앙 컬럼의 `<p className="text-gray-500 mt-1 text-xs">...</p>` 문단을 제거. h1 "계정 찾기"만 남기고 좌측 로고 / 중앙 타이틀 / 우측 "로그인으로.." 3분할 레이아웃은 유지 — Login/Signup 과의 헤더 구조 일관성은 그대로. 상단 여백이 소폭 줄어드는 대신 탭(아이디/비밀번호) 영역과의 시각적 거리가 자연스러워짐.

#### ⏱ 2026-04-16 16:10 | 도입 문의 모달 — 한 화면 수납 + 고객 유형 라벨 정합
- **피드백**: 사업자 탭에서 사업자등록번호 영역이 열리면 모달 하단 "상담 신청하기" 버튼이 뷰포트 밖으로 밀려 잘린다. 한 페이지에 모두 들어오도록 배치를 수정하고, 고객 유형 라벨도 로그인/회원가입에서 쓰는 `개인` / `사업자 (개인/법인)` 표기로 통일해달라.
- **반영**:
  - `components/landing/ContactModal.jsx` 레이아웃 밀도 상향. 컨테이너 `max-w-3xl max-h-[90vh]` → `max-w-2xl max-h-[92vh]`로 세로 여유 확보. 헤더 `py-10 px-8` → `py-5 px-6`, 제목 `text-3xl mb-2` → `text-2xl mb-1`, 서브카피 `text-sm` → `text-xs`로 상단 블록을 컴팩트하게 축소.
  - 폼 `p-8 md:p-10 space-y-8` → `p-6 md:p-7 space-y-4`. 라디오 카드 `p-4 gap-4` → `px-3 py-2.5 gap-3`, 라벨 폰트에 `text-sm` 추가. 사업자 섹션 `p-6 space-y-4` → `p-4 space-y-2`, 내부 인풋 `py-3` → `py-2`, "진위 확인" 버튼 `px-6 py-3` → `px-5 py-2 text-sm`.
  - 성함/연락처 그리드 `gap-6` → `gap-4`, 라벨 `mb-2` → `mb-1.5`, 인풋 `py-3` → `py-2`. 문의 내용 `rows={5}` → `rows={3}`로 축소(본문 입력은 유지). 제출 버튼 `py-5 text-xl` → `py-3 text-base`로 과한 히어로감 제거.
  - 고객 유형 옵션 배열의 라벨을 `개인 (입주민)` → `개인`, `사업자 / 법인` → `사업자 (개인/법인)`로 교체. Signup `SIGNUP_TABS`·Login 탭과 동일 표기 → 3개 진입점(로그인/회원가입/도입문의)의 고객 유형 언어가 완전히 정렬됨.
  - 결과: 사업자 섹션이 펼쳐진 상태에서도 헤더 + 고객유형 + 사업자등록번호 + 성함/연락처 + 문의 내용 + 제출 버튼이 92vh 안에 스크롤 없이 수납됨. `max-h-[92vh] overflow-y-auto`는 유지해 저해상도 뷰포트에서는 안전망 역할.

#### ⏱ 2026-04-16 16:55 | Notion 라운드별 스크린샷 보완
- **피드백**: `sync_notion_logs.py` 가 세션당 대표 스크린샷 1장만 찍어서, 하루에 라운드가 5개인데도 Notion에 이미지가 1장뿐이라 과소 표현됨. 라운드별로 해당 UI 상태를 캡쳐해서 덧붙여달라.
- **반영**:
  - `_capture_rounds_2026-04-16.py` 일회성 스크립트 작성 — `sync_notion_logs` 의 `upload_to_imgbb`/`find_daily_page`/`_notion_headers` 를 재사용하고 Playwright 로 5개 UI 상태를 순회 캡쳐.
  - 라운드 정의: R1 `/find-account?tab=id`, R1' `/find-account?tab=pw`, R2 `/signup` + 사업자 탭 클릭, R3+R5 `/` + "도입 문의하기" CTA 클릭 + 사업자 라디오 선택, R4 `/find-account`.
  - 첫 실행 시 ContactModal 사업자 라디오에서 `<input type="radio" class="opacity-0">` 가 pointer events 를 가로채 Playwright 클릭 30s 타임아웃 발생 → 로케이터를 `label:has-text("사업자 (개인/법인)")` 로 교체해 해당 라운드만 재캡쳐.
  - imgBB 업로드 후 오늘 페이지 하단에 `📸 라운드별 스크린샷 (2026-04-16)` H2 섹션으로 묶어 "라운드 라벨(H3) + 이미지 블록" 쌍으로 append. Notion API 의 `PATCH /v1/blocks/{id}/children` 를 2회 호출해 초기 5장 + 재캡쳐 1장 총 6장 첨부.

#### ⏱ 2026-04-16 15:19 | 랜딩 도입사례 배너에 "직원 전용 · DRONE INSPECT 진입" 임시 버튼 추가
- **피드백**: 이미 구축된 DRONE INSPECT UI(`/dashboard`)를 랜딩 페이지 "도입사례" 섹션 우측에 `직원 전용` 임시 버튼으로 연결해달라.
- **반영**:
  - `components/landing/CasesSection.jsx` 상단에 `react-router-dom`의 `Link` import 추가. 기존 다크 배너 `<div>` 에 `relative` 포지셔닝을 부여하고, 우측 상단(`absolute top-6 right-6`)에 `<Link to="/dashboard">` 버튼을 배치.
  - 스타일: 랜딩 전체 톤을 해치지 않도록 accent 컬러인 yellow-400 을 차용 — `border-yellow-400/60 bg-yellow-400/10 text-yellow-300` 기본 + hover 시 `bg-yellow-400 text-slate-900` 로 반전. 좌측에 1.5px LIVE 도트(`bg-yellow-300`)를 두고, 라벨은 "직원 전용 · DRONE INSPECT 진입"으로 목적(진입 경로)을 명시.
  - `title` 속성에 "임시 진입 버튼 — 실제 배포 시 인증 게이트 적용 예정" 을 넣어 마우스 호버 시 운영 의도를 남김. 추후 로그인/권한 체크가 붙으면 이 버튼 자체가 `Link` → 권한 가드 래퍼로 교체될 예정.
  - 기존 배너 카피(`DRONE INSPECT 현장 스케치` / 서브카피)는 `text-center` 그대로 유지 — 버튼은 절대 위치라 중앙 정렬을 흐트러뜨리지 않음.

#### ⏱ 2026-04-16 15:21 | "직원 전용" 버튼 — 로그인 우회 임시 모드 명시화
- **피드백**: 원래 직원 전용은 로그인 후에만 노출되어야 하지만, DB 미연결 단계이므로 임시로 로그인 없이 접근 가능하도록 해달라.
- **조사**: `App.jsx` `<Route path="/dashboard">`에는 이미 인증 가드가 없고, 방금 추가한 `<Link to="/dashboard">` 도 권한 체크 없이 직행 — 기능적으로는 이미 로그인 없이 접근 가능한 상태. 다만 이 "임시 우회" 의도가 UI 상 드러나지 않아, 추후 누가 보더라도 "인증 붙이기 전 임시 단계"임을 인지할 수 있도록 가시화 보완.
- **반영**:
  - `components/landing/CasesSection.jsx` 버튼 내부에 `TEMP` 뱃지(`rounded-sm bg-yellow-400/30 text-[10px] font-bold tracking-wider`) 삽입 — hover 시 반전 스타일과 맞물려 slate 톤으로 전환. 버튼 라벨 끝에 붙여 클릭 없이도 임시 상태가 보이게 처리.
  - 버튼 아래 `text-[10px] text-yellow-200/70` 서브 라벨로 **"DB 미연결 — 로그인 우회 중"** 문구 추가. `flex flex-col items-end gap-1` 컨테이너로 버튼 + 서브 라벨 수직 정렬.
  - `title` 툴팁을 "임시 진입 버튼 — 실제 배포 시 인증 게이트 적용 예정" → **"DB 미연결 단계 — 로그인 없이 임시 접근. 실제 배포 시 인증 가드 적용 예정"** 으로 교체. 사유(DB 미연결)와 해소 시점(배포 전 가드 추가)을 명시.
  - 컴포넌트 상단 주석에 NOTE 블록 추가 — AWS 프리티어 제약으로 DB 기동이 최종 단계인 점, 그 전까지는 로그인 우회 직행 링크로 운영한다는 팀 컨텍스트를 코드 근처에 남겨 이후 합류하는 개발자가 맥락 없이 이 링크를 "권한 누락 버그"로 오해하지 않도록 함.
  - 결과: 기능은 변함없이 `/` 랜딩 → 버튼 클릭 → 로그인 화면을 거치지 않고 `/dashboard` 직행. 시각적으로는 "직원 전용 · DRONE INSPECT 진입 [TEMP] / DB 미연결 — 로그인 우회 중" 조합이 노출돼 임시 모드임이 즉시 인지됨. 향후 인증 붙을 때는 이 블록 전체를 `<RequireAuth role="staff">` 래퍼로 교체하고 TEMP 뱃지 / 서브 라벨만 제거하면 됨.

#### ⏱ 2026-04-16 15:24 | "직원 전용" 버튼 위치 재조정 — 섹션 배너 → 상단 헤더 네비 우측
- **피드백**: "그렇다고 하기엔 아직 직원전용 버튼이 안보이는데?" — 사용자가 랜딩 최상단을 보는데 버튼이 안 보였음. 원래 지시 "도입사례 우측에" 를 CasesSection 다크 배너 우측으로 해석했으나, 사용자의 실제 의도는 **헤더 네비의 "도입 사례" 링크 우측(= 항상 보이는 위치)** 이었던 것으로 재해석됨.
- **반영**:
  - `components/landing/CasesSection.jsx` — 앞 라운드에 추가했던 다크 배너 내부 `<Link to="/dashboard">` 블록 + `react-router-dom` import 전부 롤백. 원래 중앙 정렬 배너로 원복.
  - `components/landing/LandingHeader.jsx` 우측 버튼 그룹 최좌측(= "도입 사례" 네비 바로 다음, 로그인 버튼 앞)에 `<Link to="/dashboard">` 신규 삽입.
  - 스타일: 헤더가 스크롤 상태에 따라 투명 ↔ 흰 배경으로 바뀌므로 `isAtTop` 분기. 투명 모드에서는 `border-yellow-300/60 bg-yellow-300/10 text-yellow-200` (어두운 히어로 위에서 yellow accent 유지), 스크롤 후 흰 헤더에서는 `border-yellow-500/70 bg-yellow-50 text-yellow-800` 로 대비 확보. hover 시 두 상태 모두 `bg-yellow-*` 솔리드 + `text-slate-900` 로 반전. 좌측 LIVE 도트 + 우측 `TEMP` 뱃지(`text-[10px] font-bold tracking-wider`) 유지.
  - 반응형: `hidden md:inline-flex` — 모바일(기존 네비 숨김 구간)에서는 함께 숨김. 로그인/도입 문의하기와 동일한 브레이크포인트 규칙.
  - `title` 툴팁 "DB 미연결 단계 — 로그인 없이 임시 접근. 실제 배포 시 인증 가드 적용 예정" 은 그대로 유지. 코드 주석에도 AWS 프리티어 제약으로 DB 기동 전까지 로그인 우회 운영 중임을 기록.
  - 결과: 랜딩 어느 스크롤 위치에서도 상단 고정 헤더에 `🟡 직원 전용 [TEMP]` 버튼이 보이며, 클릭 시 로그인 경유 없이 `/dashboard`(DRONE INSPECT UI) 로 직행. 사용자가 앞선 메시지에서 버튼을 못 봤던 이슈 해소.

#### ⏱ 2026-04-16 15:36 | Dashboard 풀 리디자인 — 카드 그리드 → 풀스크린 HUD 관제실 톤 + DRONE↔카메라 연동
- **피드백**: 사용자가 산업 플랜트 위성 맵 레퍼런스 이미지를 첨부하며 "UI가 너무 AI틱하다 — 이 레퍼런스처럼 맵이 풀스크린 배경이고 HUD 패널이 떠있는 관제실 톤으로 바꿔달라". 추가로 "현재 화면은 DRONE 01 = RGB 카메라, DRONE 02 클릭 시 열화상 카메라로 자동 전환" 규칙 요청.
- **사전 조사**: Explore 에이전트로 store/컴포넌트/스타일 토큰 전수 파악 — `droneStore` 에 선택 드론 state 없음, `cameraMode` 는 rgb/thermal/blend 3단, `BuildingScene` 은 부모 높이 의존, `DashboardLayout` 이 Sidebar+Header+p-4 padding 으로 카드 그리드 전제, index.css 에 `.card`/`.card-accent`/`.badge-*` 컴포넌트 클래스 + tailwind 커스텀 색(`accent-*`, `dashboard-bg/surface/panel/border`) 존재.
- **반영**:
  - `store/droneStore.js` — `selectedDroneId: 'drone-01'` state 추가, `DRONE_CAMERA_MAP = { 'drone-01': 'rgb', 'drone-02': 'thermal' }` 상수 export, `setSelectedDrone(id)` 액션이 selectedDroneId + cameraMode 를 원자적으로 set (drone ↔ 카메라 1:1 매핑 내재화). 초기 reset 에도 selectedDroneId 포함.
  - `App.jsx` — `DashboardLayout` 에서 `Header` import/렌더 제거, `main` 의 `p-4` 제거 + `relative overflow-hidden` 부여해 Dashboard 가 뷰포트 전체(Sidebar 제외)를 캔버스로 차지. Sidebar(w-14) 는 내비게이션 용도로 유지.
  - `components/dashboard/DashboardTopBar.jsx` 신규 — 맵 위 플로팅 상단 바. 좌측: 브랜드 로고 + Global Search, 중앙: `Satellite Map` 토글(현재 UI only, 추후 Mapbox 도입 예정 주석), 우측: `Flightpaths` 버튼 + WS 상태(LIVE/SYNC/OFFLINE/ERROR) + 알림 벨(HIGH 카운트 > 0 시 붉은 점) + 프로필 U 박스. 전체 `pointer-events-none` 바탕에 자식만 `pointer-events-auto` 로 맵 클릭 방해 방지. `backdrop-blur-md` + `bg-slate-900/70` + `border-slate-700/60` 조합으로 "HUD" 질감.
  - `components/dashboard/DronesPanel.jsx` 신규 — 좌하단(`absolute bottom-4 left-4`) 플로팅 카드. DRONE 01(RGB) / DRONE 02(THERMAL) 2열 그리드. 각 카드 클릭 시 `setSelectedDrone(id)` 호출 → cameraMode 자동 매핑. 선택된 카드는 accent(emerald) 글로우(`shadow-[0_0_12px_rgba(16,185,129,0.25)]`) + `ACTIVE` 뱃지, 비선택은 slate 톤 + `IDLE` 뱃지. 배터리 바는 DRONE 01 만 실 텔레메트리 연결, DRONE 02 는 데모값 83%(멀티 드론 API 도입 전).
  - `pages/Dashboard.jsx` 풀 리라이트 — 루트가 `relative h-full w-full overflow-hidden`, `<BuildingScene>` 를 `absolute inset-0` 배경으로 깔고 `radial-gradient` 비네팅 오버레이 추가(패널 가독성 확보). 기존 12-col 그리드(영상/온도/3D/하자/보고서) 해체하고 4개 플로팅 aside 로 재배치:
    - 상단: `<DashboardTopBar />`
    - 좌상단(`top-20 left-4 w-[320px]`): LIVE Feed(`<LiveVideoFeed>`) + Thermal Trend(`<ThermalGraph>`). Live Feed 헤더에 "D01 · RGB · 일반 카메라" 처럼 **선택 드론 + 카메라 모드** 실시간 라벨링. 빨간 LIVE 도트(`animate-pulse`).
    - 좌하단: `<DronesPanel />`
    - 우측(`top-20 right-4 bottom-4 w-[360px]`): AI Defect Analysis 플로팅 카드. 헤더에 `<Activity />` 아이콘 + 타이틀 + 녹색 LIVE 도트 + "Real-time detection" 서브 라벨(레퍼런스 문구 그대로). 본문은 기존 `<DefectPanel />` 재사용.
  - `components/map3d/BuildingScene.jsx` — 루트에 `relative` 부여(풀스크린 배경 시 범례 absolute 기준 필요). 범례를 `bottom-2 left-2` → `bottom-4 left-1/2 -translate-x-1/2` 로 이동(DronesPanel/AI 패널과 충돌 없는 bottom-center). `rounded-full` pill 형태에 `bg-slate-900/60 backdrop-blur-sm` 입혀 HUD 질감 통일. `pointer-events-none` 으로 맵 조작 방해 제거.
  - `components/layout/Sidebar.jsx` — `NAV_ITEMS` 의 대시보드 링크 `to: '/'` → `to: '/dashboard'` 수정(랜딩/대시보드 라우트 분리 후 경로 오류 고침).
- **제외 / 결정 사항**:
  - `components/layout/Header.jsx` 파일은 보존하되 참조 없음 상태로 남김 — 추후 다른 레이아웃(예: Reports 페이지)에서 재사용 가능성.
  - `DroneStatusCard.jsx` 도 보존하되 Dashboard 에서는 DronesPanel 로 대체. 두 컴포넌트의 책임이 겹치지만 DroneStatusCard 는 4칸 텔레메트리 상세(고도/속도/모드/배터리) 용, DronesPanel 은 드론 선택 + 카메라 매핑 용으로 목적이 다름.
  - `ReportPanel` 은 이번 HUD 레이아웃에서 일단 제외 — 레퍼런스에 대응물 없고, 풀스크린 캔버스 철학과 어긋남. 추후 "리포트" 별도 탭/페이지로 분리 예정.
  - **위성 이미지 베이스맵**(레퍼런스의 실제 아쉬워 보이는 요소)은 이번 라운드 제외 — 현재 R3F 기반 BuildingMesh 와 데이터 소스가 다르고 Mapbox/MapLibre 도입이 선행 필요. TopBar 의 "Satellite Map" 버튼은 자리만 잡아 둠.
- **검증**: `npm run dev` → Vite 6.4.2 231ms 부팅(port 5174). Dashboard.jsx / DashboardTopBar.jsx / DronesPanel.jsx 모두 HMR transform 성공, 컴파일 에러 0건. lucide-react@1.8.0(실제 번들은 최신 아이콘 export 포함) 에서 `Search/Satellite/Route/Bell/Video/Activity` named export 존재 확인 후 import.
- **결과**: 사용자가 "너무 AI틱"이라 한 "카드 카탈로그" 톤이 "풀스크린 위성 관제실" 톤으로 전환. DRONE 01/02 카드 클릭 → 좌상단 LIVE Feed 의 카메라 스트림(rgb/thermal MJPEG URL)이 즉시 전환되어 사용자가 제시한 "드론=카메라" 매핑 규칙이 UI 에 내재화됨.

#### ⏱ 2026-04-16 15:42 | 3D 맵 강등 + LIVE 피드 승격 — 메인 캔버스 재편
- **피드백**: 이전 라운드 결과 화면을 보고 "3D 맵이 주 화면처럼 나온다. 3D 맵(도면/평면도/시뮬레이션 모델링 용)은 우측 하단 미니맵이 맞고, 메인은 다른 것"이라 재정비 요청. 사용자가 일관되게 주장한 "DRONE 01 = 일반 카메라 / DRONE 02 = 열화상" 규칙과 맞물려, 메인 캔버스는 **선택 드론의 LIVE 카메라 피드**가 돼야 한다는 쪽으로 확정.
- **반영**:
  - `components/video/LiveVideoFeed.jsx` — `fill` prop 추가. fill=true 시 컨테이너 `w-full h-full`(16/9 강제 해제), `object-cover`(16/9 박스 꽉 채움). No-Signal 플레이스홀더도 fill 모드 전용으로 개편: `radial-gradient` 다크 배경 + 8% opacity 그린 그리드 오버레이(레이더 톤) + "Signal Standby" 모노스페이스 라벨 + 현재 카메라 모드 서브 라벨. 기존 top-2 모드 뱃지/LIVE 점멸 마커는 fill 모드에서 숨김(상위 Dashboard HUD 에서 처리).
  - `pages/Dashboard.jsx` 재배치 — 기존 `<BuildingScene>` 풀스크린 배경 구조 폐기. 메인 영역에 `<LiveVideoFeed fill />` 를 16/9 박스로 렌더링. 좌상단 Live Feed PIP 도 제거(메인으로 승격되어 중복).
  - 3D 맵은 우하단 300×200 카드 (`3D Mini Map` 타이틀 + "floor plan · sim" 서브 라벨)로 강등. `<BuildingScene>` 는 이 카드 안에 삽입.
  - AI Defect Analysis 패널은 미니맵과 수직 겹침 방지 위해 `bottom: MINIMAP_H + 24` offset 적용.
  - `components/map3d/BuildingScene.jsx` 의 범례 pill 은 그대로 유지(미니맵 bottom-center 안에 자연스럽게 앉음).
- **결과**: 메인 캔버스가 "선택된 드론의 시점 영상" 이 되고, 3D 시뮬레이션/평면도 모델링은 우하단 미니맵으로 내려가 "맵은 부가 정보" 의 위계 확립.

#### ⏱ 2026-04-16 15:45 | LIVE 피드 16:9 비율 유지 + 패널/미니맵 겹침 방지
- **피드백**: "16:9 카메라 비율 유지하면서 AI DEFECT ANALYSIS랑 3D MINIMAP 구간에 안 겹치게 해줄 수 있을까?"  — 앞 라운드에서 LiveVideoFeed `fill` 모드가 `object-cover + w-full h-full` 이어서 피드가 뷰포트 전체를 덮고 우측 HUD 패널들 뒤로 깔려 있었음. 원본 영상 비율(16:9) 유지하면서 패널·미니맵 바깥으로만 확장되게 해달라는 요청.
- **반영**:
  - `pages/Dashboard.jsx` 에 `SAFE = { top:100, bottom:150, left:316, right:400 }` 상수 정의. 각 값은 주변 HUD 패널 폭/높이 + margin + gap 기준:
    - `top: 100` → DashboardTopBar(56px) + 여백(44)
    - `bottom: 150` → DronesPanel(≈134) + gap. 우하단 Minimap(h=200) 은 horizontal 로 이미 오른쪽에 치우쳐 수평 분리되므로 vertical offset 은 DronesPanel 기준만 반영.
    - `left: 316` → Thermal Trend(w=280) + margin(4) + gap(32)
    - `right: 400` → AI Defect Analysis(w=360) + margin(4) + gap(36). 미니맵(w=300) 은 이미 이 범위 안에 들어오므로 별도 고려 불필요.
  - 기존 "absolute inset-0 + LiveVideoFeed fill" 구조를 `absolute { top, bottom, left, right } = SAFE` + `flex items-center justify-center` 래퍼로 교체. 내부 16/9 박스는 `{ aspectRatio: '16 / 9', width: '100%', maxHeight: '100%' }` 조합으로 safe zone 안에서 자동 피팅 — 화면 비율에 따라 가로/세로 기준 중 하나로 맞춰짐.
  - 피드 박스에 `bg-black rounded-xl border border-slate-700/60 shadow-2xl` 로 letterbox 영역을 자연스럽게 처리. 박스 바깥(safe zone 안의 여백)은 `bg-dashboard-bg` 가 비침.
  - 기존 상단 중앙에 따로 떠있던 "드론·카메라 컨텍스트 뱃지" 는 피드 박스 좌상단(`absolute top-3 left-3`) 으로 이동 — 피드 자체의 HUD 로 자리 잡음.
- **검증**: Vite dev 재기동 328ms, Dashboard.jsx / LiveVideoFeed.jsx transform 모두 성공. 컴파일 에러 0.
- **결과**: LIVE 피드가 16:9 letterbox 박스로 가운데 정렬되고, AI Defect Analysis(우상단) + 3D Mini Map(우하단) + Thermal Trend(좌상단) + Drones(좌하단) 네 개 HUD 카드와 어떤 화면 비율에서도 겹치지 않음. 사용자가 지목한 "사각지대" 영역이 해소됨.
  - 결과: 한 세션에 대표 스크린샷 1장 + 라운드별 세부 캡쳐 6장이 함께 보이는 구조. 향후 sync 스크립트 자체에 "세션 내 `#### ⏱` 라운드 스캐너 + prepare 훅" 을 정식 기능으로 편입할지는 별건으로 둠(현재는 일회성 보완).
