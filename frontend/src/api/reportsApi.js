/**
 * api/reportsApi.js
 * 역할: 완료된 점검 리포트 아카이브 CRUD — **API 모양의 추상화**
 *
 *   현재 구현: localStorage (zustand persist 와 별개의 키)
 *   백엔드 연결 후: 이 파일의 함수 body 만 `fetch()` 호출로 교체하면 호출부(reportsStore / 컴포넌트) 변경 불필요.
 *
 *   예상 백엔드 엔드포인트 (DB 연결 단계에서 신설):
 *     GET    /api/v1/reports           → list
 *     GET    /api/v1/reports/{id}      → detail
 *     POST   /api/v1/reports           → create
 *     PATCH  /api/v1/reports/{id}      → update
 *     DELETE /api/v1/reports/{id}      → delete
 *
 *   리포트 스키마 (backend 연결 시 SQLAlchemy 모델 / Pydantic schema 로 변환):
 *     {
 *       id: uuid,
 *       site_name: str,
 *       operator_name: str,
 *       inspection_date: str (YYYY-MM-DD),
 *       level: int,
 *       model_source: 'premodel' | 'drone',
 *       session_id: uuid,
 *       started_at: int (epoch ms),
 *       finished_at: int (epoch ms),
 *       status: 'draft' | 'published',
 *       defects: [
 *         {
 *           ...원본 DefectLog fields,
 *           trade: str,                // 공종 (AI 제안 + 편집)
 *           trade_confidence: float,   // AI 제안 신뢰도
 *           location_label: str,       // location_map 적용된 결과 ("거실" 등)
 *           verified: bool,            // 검증 체크
 *           action_note: str,          // 조치 메모
 *           is_manual: bool,           // 수동 추가 플래그
 *         }
 *       ],
 *       location_map: { A: "거실", B: "공용주방", ... },
 *       narrative_content: str,       // LLM 스트리밍 결과 캐시
 *       created_at: int,
 *       updated_at: int,
 *     }
 */

const STORAGE_KEY = 'drone-inspect-reports-archive'

function readAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch (err) {
    console.warn('[reportsApi] 파싱 실패, 빈 배열로 복구:', err)
    return []
  }
}

function writeAll(reports) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reports))
  } catch (err) {
    // 쿼터 초과 가능성
    console.error('[reportsApi] 저장 실패 (localStorage 쿼터 확인):', err)
    throw err
  }
}

// 네트워크 지연 시뮬레이션 — 백엔드 교체 시 실제 fetch 가 수행
const simulateLatency = () => new Promise((r) => setTimeout(r, 80))

/* ──────────────────────────────────────────────────────────────
   Public API
   ────────────────────────────────────────────────────────────── */

/** GET /api/v1/reports */
export async function listReports() {
  await simulateLatency()
  return readAll().sort((a, b) => (b.updated_at ?? b.created_at) - (a.updated_at ?? a.created_at))
}

/** GET /api/v1/reports/{id} */
export async function getReport(id) {
  await simulateLatency()
  return readAll().find((r) => r.id === id) ?? null
}

/** POST /api/v1/reports */
export async function createReport(payload) {
  await simulateLatency()
  const reports = readAll()
  const now = Date.now()
  const report = {
    id: payload.id ?? crypto.randomUUID(),
    status: payload.status ?? 'draft',
    ...payload,
    created_at: payload.created_at ?? now,
    updated_at: now,
  }
  reports.push(report)
  writeAll(reports)
  return report
}

/** PATCH /api/v1/reports/{id} */
export async function updateReport(id, patch) {
  await simulateLatency()
  const reports = readAll()
  const idx = reports.findIndex((r) => r.id === id)
  if (idx < 0) throw new Error(`리포트를 찾을 수 없습니다: ${id}`)
  const updated = { ...reports[idx], ...patch, id, updated_at: Date.now() }
  reports[idx] = updated
  writeAll(reports)
  return updated
}

/** DELETE /api/v1/reports/{id} */
export async function deleteReport(id) {
  await simulateLatency()
  const next = readAll().filter((r) => r.id !== id)
  writeAll(next)
  return { ok: true }
}

/** (개발 편의용) 전체 삭제 */
export async function clearAllReports() {
  await simulateLatency()
  writeAll([])
  return { ok: true }
}
