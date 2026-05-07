/**
 * components/map3d/DroneMarker.jsx
 * 역할: 3D 미니맵 상 드론 실시간 위치 + 비행 경로 폴리라인
 *       - droneStore.telemetry 의 x/y/z + yaw 구독
 *       - missionStatus === 'flying' 일 때 위치 히스토리 축적 → Line 으로 경로 렌더
 *       - 드론 형태: selectedDroneId 별 실제 모델 적용 (실측 미터 단위 비율)
 *           drone-01 → GEPRC GEP-CL35 V3 / Cinelog35 V3 / O4 Pro RC FPV (Cinewhoop 3.5")
 *           drone-02 → HolyBro S500 V2 (480mm 표준 X-쿼드)
 *       - BuildingMesh 단위계 = 미터 (1 R3F unit = 1m). 드론도 동일 미터 단위.
 *       - 고도 라인: 드론 위치 → 바닥 점선
 *
 *   좌표 매핑: 텔레메트리(X/Y 평면 + Z 고도) → Three.js(X/Z 평면 + Y 위)
 */

import { useRef, useEffect } from 'react'
import { Billboard, Html, Line } from '@react-three/drei'
import useDroneStore from '../../store/droneStore.js'

// 경로 히스토리 최대 포인트 수 — 너무 많으면 성능 저하
const MAX_PATH_POINTS = 500
// 최소 이동 거리(씬 좌표) — 미세 진동 필터링
const MIN_MOVE_DIST = 0.05

// 드론 ID → 실모델 매핑.
//   drone-01 → Cinelog35 V3 (실내 점검용 Cinewhoop 3.5")
//   drone-02 → HolyBro S500 (외부/광역용 480mm 표준 X-쿼드)
//
// 주의: 이건 droneStore.DRONE_CAMERA_MAP(drone-01=RGB, drone-02=THERMAL)과
// 별개 차원의 매핑이다. 기체 모델 = "어떤 드론으로 비행하는가"(사이즈/용도/실내외),
// 카메라 매핑 = "그 기체에 어떤 페이로드가 실렸는가"(RGB vs THERMAL). 두 매핑은
// 우연히 같은 selectedDroneId 키를 공유할 뿐 인과관계 없음.
// 추후 페이로드 가변(같은 기체에 RGB/THERMAL 교체) 시점에 카메라 매핑은 별 필드로
// 이관되고 본 모델 매핑은 그대로 유지되어야 함.
const DRONE_MODEL_MAP = {
  'drone-01': 'cinelog35',
  'drone-02': 's500',
}

// 모델별 실측 사양 (미터 단위, 사용자 명시 사양 기준)
const SPECS = {
  cinelog35: {
    label: 'CINELOG35 V3',
    wheelbase: 0.142,        // motor-to-motor 대각 (mm 142)
    outerSize: 0.188,        // 덕트 포함 외곽 한 변
    frameHeight: 0.025,      // 중앙 frame stack 두께
    propRadius: 0.0445,      // 3.5" prop = 88.9mm 직경 → 반지름 44.5mm
    ductOuterRadius: 0.048,  // 덕트 hoop 외경 ≈ 96mm 직경
    labelOffsetY: 0.18,      // ID 라벨 띄우는 높이
  },
  s500: {
    label: 'HOLYBRO S500',
    wheelbase: 0.480,        // 480mm
    outerSize: 0.480,
    frameHeight: 0.05,       // 중앙 frame plate 두께
    propRadius: 0.127,       // 10" prop = 254mm 직경 → 반지름 127mm
    armLength: 0.24,         // arm 길이 (wheelbase / 2)
    landingGearLen: 0.10,    // 다리 길이 (지면 클리어런스)
    labelOffsetY: 0.45,
  },
}

// ── 드론 본체 컴포넌트 ─────────────────────────────────────────

/** GEPRC Cinelog35 V3 (Cinewhoop 3.5") — O4 Pro RC FPV 카메라 탑재.
 * 실측 188×188×~70mm, wheelbase 142mm. 4 덕트(hoop)로 프로펠러 보호.
 * 실내 안전 점검용 — 충돌 시 덕트가 프로펠러 보호 + 벽/사람 보호. */
function Cinelog35Body({ accent }) {
  const s = SPECS.cinelog35
  // 4 덕트 중심 좌표 — wheelbase 대각 142mm 기준 X-arm
  const armHalf = s.wheelbase / 2 / Math.SQRT2  // ≈ 0.0502
  const ductPositions = [
    [ armHalf, 0,  armHalf],
    [ armHalf, 0, -armHalf],
    [-armHalf, 0,  armHalf],
    [-armHalf, 0, -armHalf],
  ]

  return (
    <group>
      {/* 4 덕트(cinewhoop hoop) + 내부 프로펠러 디스크 */}
      {ductPositions.map(([dx, dy, dz], i) => (
        <group key={i} position={[dx, dy, dz]}>
          {/* 덕트 hoop — torus, ductOuterRadius 외경 */}
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[s.ductOuterRadius, 0.004, 6, 24]} />
            <meshStandardMaterial color="#0f172a" />
          </mesh>
          {/* 프로펠러 디스크 (회전 모션 표현) */}
          <mesh position={[0, 0.005, 0]}>
            <cylinderGeometry args={[s.propRadius, s.propRadius, 0.003, 16]} />
            <meshStandardMaterial color="#475569" transparent opacity={0.45} />
          </mesh>
          {/* 모터 (덕트 하부 마운트) */}
          <mesh position={[0, -0.008, 0]}>
            <cylinderGeometry args={[0.008, 0.008, 0.012, 12]} />
            <meshStandardMaterial color="#1e293b" />
          </mesh>
        </group>
      ))}

      {/* 중앙 frame stack — 작은 박스 (FC + ESC + VTX 더미) */}
      <mesh position={[0, 0.005, 0]}>
        <boxGeometry args={[0.05, s.frameHeight, 0.05]} />
        <meshStandardMaterial color="#0f172a" emissive={accent} emissiveIntensity={0.15} />
      </mesh>

      {/* O4 Pro RC 카메라 — frame 앞 (X+ 방향이 forward) */}
      <mesh position={[0.035, 0.012, 0]}>
        <boxGeometry args={[0.022, 0.022, 0.022]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      {/* 카메라 렌즈 — emissive 작은 점 */}
      <mesh position={[0.046, 0.012, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.006, 0.006, 0.003, 12]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.6} />
      </mesh>

      {/* VTX 안테나 — 뒤쪽 위로 (방향 인지용 액센트) */}
      <mesh position={[-0.022, 0.04, 0]}>
        <cylinderGeometry args={[0.0012, 0.0012, 0.045, 6]} />
        <meshStandardMaterial color="#dc2626" />
      </mesh>
    </group>
  )
}

/** HolyBro S500 V2 — 480mm 표준 X-쿼드, 10" 프로펠러, GPS + 짐벌.
 * 실측 480×480×196mm. 외부/광역 점검 + 큰 페이로드 (열화상 카메라 등). */
function HolyBroS500Body({ accent }) {
  const s = SPECS.s500
  // 4 모터 위치 — X자, arm length 절반씩 ±X/±Z
  const motorOffset = s.armLength / Math.SQRT2  // ≈ 0.17
  const motorPositions = [
    [ motorOffset, 0,  motorOffset],
    [ motorOffset, 0, -motorOffset],
    [-motorOffset, 0,  motorOffset],
    [-motorOffset, 0, -motorOffset],
  ]

  return (
    <group>
      {/* 4 arms (X자) — 박스를 모터 방향으로 회전 */}
      {motorPositions.map(([mx, , mz], i) => {
        // 중앙(0,0,0) → 모터(mx,0,mz) 방향 각도
        const angle = Math.atan2(mz, mx)
        const dist = Math.hypot(mx, mz)
        return (
          <mesh
            key={`arm-${i}`}
            position={[mx / 2, 0, mz / 2]}
            rotation={[0, -angle, 0]}
          >
            <boxGeometry args={[dist, 0.012, 0.024]} />
            <meshStandardMaterial color="#0f172a" />
          </mesh>
        )
      })}

      {/* 4 모터 + 프로펠러 디스크 */}
      {motorPositions.map(([mx, , mz], i) => (
        <group key={`motor-${i}`} position={[mx, 0, mz]}>
          {/* 모터 */}
          <mesh position={[0, 0.013, 0]}>
            <cylinderGeometry args={[0.018, 0.018, 0.022, 16]} />
            <meshStandardMaterial color="#1e293b" />
          </mesh>
          {/* 모터 캡 — 작은 액센트 */}
          <mesh position={[0, 0.025, 0]}>
            <cylinderGeometry args={[0.014, 0.014, 0.004, 12]} />
            <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.3} />
          </mesh>
          {/* 프로펠러 (10") */}
          <mesh position={[0, 0.032, 0]}>
            <cylinderGeometry args={[s.propRadius, s.propRadius, 0.005, 16]} />
            <meshStandardMaterial color="#64748b" transparent opacity={0.4} />
          </mesh>
        </group>
      ))}

      {/* 중앙 frame plate (top + bottom 샌드위치) */}
      <mesh position={[0, 0.018, 0]}>
        <boxGeometry args={[0.18, 0.006, 0.18]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      <mesh position={[0, -0.018, 0]}>
        <boxGeometry args={[0.18, 0.006, 0.18]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      {/* 중앙 stack(FC/PDB/ESC) */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[0.10, 0.03, 0.10]} />
        <meshStandardMaterial color="#0f172a" emissive={accent} emissiveIntensity={0.15} />
      </mesh>

      {/* GPS 마운트 — 뒤쪽 polestand */}
      <mesh position={[-0.06, 0.05, 0]}>
        <cylinderGeometry args={[0.0025, 0.0025, 0.06, 6]} />
        <meshStandardMaterial color="#475569" />
      </mesh>
      {/* GPS dome — 위쪽 원반 (M8N/M9N 형태) */}
      <mesh position={[-0.06, 0.085, 0]}>
        <cylinderGeometry args={[0.025, 0.025, 0.012, 16]} />
        <meshStandardMaterial color="#22d3ee" emissive="#0891b2" emissiveIntensity={0.3} />
      </mesh>

      {/* 짐벌 카메라 (앞쪽 아래) */}
      <mesh position={[0.06, -0.038, 0]}>
        <boxGeometry args={[0.05, 0.04, 0.04]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>
      <mesh position={[0.087, -0.038, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.012, 0.012, 0.008, 16]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.6} />
      </mesh>

      {/* 4 landing gear (다리 4개) */}
      {[
        [ 0.07, 0.07], [ 0.07, -0.07],
        [-0.07, 0.07], [-0.07, -0.07],
      ].map(([dx, dz], i) => (
        <mesh key={`leg-${i}`} position={[dx, -0.06, dz]}>
          <cylinderGeometry args={[0.004, 0.004, s.landingGearLen, 6]} />
          <meshStandardMaterial color="#475569" />
        </mesh>
      ))}
      {/* 다리 가로대 (스키드) */}
      {[0.07, -0.07].map((dz, i) => (
        <mesh key={`skid-${i}`} position={[0, -0.108, dz]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.004, 0.004, 0.16, 6]} />
          <meshStandardMaterial color="#475569" />
        </mesh>
      ))}
    </group>
  )
}

// ── 메인 ────────────────────────────────────────────────────────

export default function DroneMarker() {
  const telemetry = useDroneStore((s) => s.telemetry)
  const selectedDroneId = useDroneStore((s) => s.selectedDroneId)
  const missionStatus = useDroneStore((s) => s.missionStatus)

  // 텔레메트리 → Three 좌표 매핑 (X/Y 평면, Z 고도 → X, Y up, Z forward)
  const px = telemetry.x ?? 0
  const py = telemetry.z ?? 1.5 // 고도
  const pz = telemetry.y ?? 0
  const yawRad = ((telemetry.yaw ?? 0) * Math.PI) / 180

  const accent = missionStatus === 'flying' ? '#10b981' : '#64748b'
  const droneModel = DRONE_MODEL_MAP[selectedDroneId] || 'cinelog35'
  const spec = SPECS[droneModel]

  // ── 비행 경로 히스토리 ──
  const pathRef = useRef([])
  const lastPosRef = useRef(null)

  useEffect(() => {
    if (missionStatus === 'flying') {
      pathRef.current = []
      lastPosRef.current = null
    }
  }, [missionStatus])

  if (missionStatus === 'flying') {
    const last = lastPosRef.current
    const moved = !last || Math.hypot(px - last[0], py - last[1], pz - last[2]) > MIN_MOVE_DIST
    if (moved) {
      pathRef.current.push([px, py, pz])
      if (pathRef.current.length > MAX_PATH_POINTS) {
        pathRef.current = pathRef.current.slice(-MAX_PATH_POINTS)
      }
      lastPosRef.current = [px, py, pz]
    }
  }
  const pathPoints = pathRef.current

  return (
    <>
      {/* 비행 경로 폴리라인 — 비행 중 + 종료 후에도 표시 */}
      {pathPoints.length >= 2 && (
        <Line
          points={pathPoints}
          color="#10b981"
          lineWidth={1.5}
          dashed
          dashScale={8}
          dashSize={0.3}
          dashOffset={0}
          transparent
          opacity={0.7}
        />
      )}

      {/* 바닥에 경로 그림자 (고도 제거한 2D 투영) */}
      {pathPoints.length >= 2 && (
        <Line
          points={pathPoints.map(([x, , z]) => [x, 0.05, z])}
          color="#10b981"
          lineWidth={1}
          transparent
          opacity={0.2}
        />
      )}

      {/* 드론 본체 — 모델별 실측 비율 */}
      <group position={[px, py, pz]} rotation={[0, yawRad, 0]}>
        {droneModel === 'cinelog35' ? (
          <Cinelog35Body accent={accent} />
        ) : (
          <HolyBroS500Body accent={accent} />
        )}

        {/* 고도 라인 (드론 → 바닥) */}
        <mesh position={[0, -py / 2, 0]}>
          <cylinderGeometry args={[0.01, 0.01, Math.max(py, 0.01), 4]} />
          <meshBasicMaterial color={accent} transparent opacity={0.35} />
        </mesh>

        {/* ID + 모델 라벨 — 모델 사이즈에 비례한 높이 */}
        <Billboard position={[0, spec.labelOffsetY, 0]}>
          <Html center distanceFactor={10}>
            <div
              className="px-1.5 py-0.5 rounded bg-slate-900/85 border text-[9px] font-mono tracking-wider whitespace-nowrap leading-tight"
              style={{ color: accent, borderColor: accent + '99' }}
            >
              <div>{selectedDroneId.replace('drone-0', 'D')} · {(telemetry.z ?? 0).toFixed(1)}m</div>
              <div className="text-[8px] opacity-70">{spec.label}</div>
            </div>
          </Html>
        </Billboard>
      </group>
    </>
  )
}
