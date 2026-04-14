/**
 * store/droneStore.js
 * 역할: 드론 텔레메트리 및 연결 상태 전역 관리 (Zustand)
 *       - telemetry: 드론 위치·자세·배터리 실시간 데이터
 *       - connectionStatus: WebSocket 연결 상태
 *       - cameraMode: 현재 활성 카메라 모드 (rgb/thermal/blend)
 *       - setCameraMode: 카메라 모드 전환 (CameraToggle에서 호출)
 */

import { create } from 'zustand'

const useDroneStore = create((set) => ({
  // ── 연결 상태 ────────────────────────────
  connectionStatus: 'disconnected', // 'connecting' | 'connected' | 'disconnected' | 'error'

  // ── 드론 텔레메트리 ──────────────────────
  telemetry: {
    x: 0,           // 월드 좌표 X (m)
    y: 0,           // 월드 좌표 Y (m)
    z: 0,           // 고도 (m)
    roll: 0,        // 롤 각도 (deg)
    pitch: 0,       // 피치 각도 (deg)
    yaw: 0,         // 요 각도 (deg)
    battery: 100,   // 배터리 잔량 (%)
    speed: 0,       // 속도 (m/s)
    distance: null, // LiDAR 거리 (m)
    armed: false,   // 모터 암드 여부
    mode: 'MANUAL', // 비행 모드
  },

  // ── 카메라 모드 ──────────────────────────
  // 'rgb': RGB 카메라 단독
  // 'thermal': 열화상 카메라 단독
  // 'blend': RGB + 열화상 합성
  cameraMode: 'rgb',

  // ── Actions ─────────────────────────────

  /** WebSocket 연결 상태 업데이트 */
  setConnectionStatus: (status) => set({ connectionStatus: status }),

  /** 드론 텔레메트리 업데이트 (WS "telemetry.update" 이벤트) */
  updateTelemetry: (data) =>
    set((state) => ({
      telemetry: { ...state.telemetry, ...data },
    })),

  /**
   * 카메라 모드 전환.
   * CameraToggle.jsx에서 호출 → POST /api/v1/stream/mode API도 함께 호출.
   */
  setCameraMode: (mode) => {
    if (!['rgb', 'thermal', 'blend'].includes(mode)) return
    set({ cameraMode: mode })
  },

  /** WS "camera.mode_changed" 이벤트 수신 시 동기화 */
  syncCameraMode: (mode) => set({ cameraMode: mode }),

  /** 전체 초기화 */
  reset: () =>
    set({
      connectionStatus: 'disconnected',
      telemetry: {
        x: 0, y: 0, z: 0,
        roll: 0, pitch: 0, yaw: 0,
        battery: 100, speed: 0,
        distance: null, armed: false, mode: 'MANUAL',
      },
      cameraMode: 'rgb',
    }),
}))

export default useDroneStore
