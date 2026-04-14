/**
 * components/map3d/BuildingScene.jsx
 * 역할: React Three Fiber 3D 캔버스 래퍼
 *       - OrbitControls로 마우스 드래그 회전/줌 지원
 *       - BuildingMesh: 건물 와이어프레임
 *       - DefectMarker: 탐지된 하자 위치 마커
 *       - lidar 좌표가 있는 하자만 마커로 표시
 */

import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import { Suspense } from 'react'
import BuildingMesh from './BuildingMesh.jsx'
import DefectMarker from './DefectMarker.jsx'
import useDefectStore from '../../store/defectStore.js'

export default function BuildingScene() {
  const defects = useDefectStore((s) => s.defects)

  // LiDAR 좌표가 있는 하자만 마커 표시
  const mappedDefects = defects.filter(
    (d) => d.lidar_x != null && d.lidar_y != null && d.lidar_z != null
  )

  return (
    <div className="w-full h-full rounded overflow-hidden">
      <Canvas shadows>
        <PerspectiveCamera makeDefault position={[8, 6, 8]} fov={50} />
        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          maxPolarAngle={Math.PI / 2}
          minDistance={2}
          maxDistance={30}
        />

        {/* 조명 */}
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 10, 5]} intensity={0.8} castShadow />

        <Suspense fallback={null}>
          {/* 건물 구조 */}
          <BuildingMesh />

          {/* 하자 마커 */}
          {mappedDefects.map((defect) => (
            <DefectMarker key={defect.id} defect={defect} />
          ))}
        </Suspense>
      </Canvas>

      {/* 범례 */}
      <div className="absolute bottom-2 left-2 flex items-center gap-3 text-[10px] text-slate-500">
        <LegendItem color="#ef4444" label="HIGH" />
        <LegendItem color="#f97316" label="MED" />
        <LegendItem color="#eab308" label="LOW" />
        <span className="ml-2">{mappedDefects.length}개 마커</span>
      </div>
    </div>
  )
}

function LegendItem({ color, label }) {
  return (
    <div className="flex items-center gap-1">
      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
      <span>{label}</span>
    </div>
  )
}
