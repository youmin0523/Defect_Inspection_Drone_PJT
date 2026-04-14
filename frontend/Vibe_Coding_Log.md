# 🤖 바이브코딩(Vibe Coding) 프롬프트 & 결과 추적 로그

> **💡 설명**: 프론트엔드(Frontend) 전용 바이브코딩 로그입니다. AI에게 언제, 어떤 프롬프트를 입력하여 어떤 코드를 도출했는지 기록합니다.

---

## 📝 기본 정보 (Meta)

- 작성자 (Who): @youminsu0523
- 작성 일자 (When): 2026-04-14
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
