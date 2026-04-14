/**
 * components/map3d/BuildingMesh.jsx
 * 역할: 3D 건물 박스 지오메트리 컴포넌트
 *       - 간단한 직육면체로 건물 내부 구조 시각화
 *       - 와이어프레임 모드로 내부 구조 투시
 *       - 바닥, 벽 영역 별도 레이어로 구분
 */

export default function BuildingMesh({ width = 10, depth = 8, height = 3 }) {
  return (
    <group>
      {/* 바닥 */}
      <mesh position={[0, 0, 0]} receiveShadow>
        <boxGeometry args={[width, 0.1, depth]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>

      {/* 벽체 외곽 (와이어프레임) */}
      <mesh position={[0, height / 2, 0]}>
        <boxGeometry args={[width, height, depth]} />
        <meshStandardMaterial
          color="#334155"
          wireframe
          transparent
          opacity={0.3}
        />
      </mesh>

      {/* 그리드 헬퍼 */}
      <gridHelper args={[Math.max(width, depth) + 4, 20, '#1e3a8a', '#1e293b']} position={[0, 0, 0]} />
    </group>
  )
}
