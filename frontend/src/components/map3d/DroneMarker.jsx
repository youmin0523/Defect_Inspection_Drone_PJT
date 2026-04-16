/**
 * components/map3d/DroneMarker.jsx
 * 역할: 3D 미니맵 상 드론 실시간 위치 아이콘
 *       - droneStore.telemetry 의 x/y/z + yaw 구독
 *       - group (main body cone + 4 small cylinders as props) + accent glow
 *       - yaw 회전은 Y축(수직) 기준. position 은 (x, z, y) 매핑 — Three.js 좌표계 주의
 *         (드론 텔레메트리는 월드 X/Y 평면 + Z 고도, Three.js 는 Y 가 위이므로 Y ↔ Z 스왑)
 *       - <Billboard> 로 드론 ID 라벨 카메라 대면 고정
 */

import { Billboard, Html } from '@react-three/drei'
import useDroneStore from '../../store/droneStore.js'

export default function DroneMarker() {
  const telemetry = useDroneStore((s) => s.telemetry)
  const selectedDroneId = useDroneStore((s) => s.selectedDroneId)
  const missionStatus = useDroneStore((s) => s.missionStatus)

  // 텔레메트리 → Three 좌표 매핑: (x, z_alt, y) 로 스왑
  const px = telemetry.x ?? 0
  const py = (telemetry.z ?? 1.5) // 고도
  const pz = telemetry.y ?? 0
  const yawDeg = telemetry.yaw ?? 0
  const yawRad = (yawDeg * Math.PI) / 180

  const accent = missionStatus === 'flying' ? '#10b981' : '#64748b'

  return (
    <group position={[px, py, pz]} rotation={[0, yawRad, 0]}>
      {/* 본체 (cone — 진행 방향이 +X) */}
      <mesh rotation={[0, 0, -Math.PI / 2]}>
        <coneGeometry args={[0.18, 0.5, 12]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.4} />
      </mesh>

      {/* 4개 프로펠러 — 얇은 원판 */}
      {[
        [ 0.35,  0.35],
        [ 0.35, -0.35],
        [-0.35,  0.35],
        [-0.35, -0.35],
      ].map(([dx, dz], i) => (
        <mesh key={i} position={[dx, 0.08, dz]}>
          <cylinderGeometry args={[0.15, 0.15, 0.02, 16]} />
          <meshStandardMaterial color="#1e293b" transparent opacity={0.7} />
        </mesh>
      ))}

      {/* 아래로 내려오는 포인트 (고도 표시 라인) */}
      <mesh position={[0, -py / 2, 0]}>
        <cylinderGeometry args={[0.01, 0.01, Math.max(py, 0.01), 4]} />
        <meshBasicMaterial color={accent} transparent opacity={0.35} />
      </mesh>

      {/* ID 라벨 — 항상 카메라 대면 */}
      <Billboard position={[0, 0.6, 0]}>
        <Html center distanceFactor={10}>
          <div
            className="px-1.5 py-0.5 rounded bg-slate-900/80 border text-[9px] font-mono tracking-wider whitespace-nowrap"
            style={{
              color: accent,
              borderColor: accent + '99',
            }}
          >
            {selectedDroneId.replace('drone-0', 'D')} · {telemetry.z?.toFixed(1) ?? '0.0'}m
          </div>
        </Html>
      </Billboard>
    </group>
  )
}
