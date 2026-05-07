# 03. 캘리브레이션 — 카메라 / 광학흐름 / ToF / IMU

> 자율비행 정밀도와 안전은 캘리브레이션 품질이 좌우합니다. 본 문서 4개 항목은 첫 비행 전 **반드시** 모두 통과해야 합니다.

## 1. RGB 카메라 (DJI O4 Pro / Skydroid OTG 수신)

### 1-1. 캘리브레이션 보드 준비
- 7×9 체크보드 패턴 (사각형 25mm) — A4 출력 후 평평한 보드에 부착
- 체크보드 PDF: https://markhedleyjones.com/projects/calibration-checkerboard-collection

### 1-2. 캡처
1. 백엔드 PC에 Skydroid USB 수신기 연결 → `/dev/video*` 또는 Windows 카메라 인덱스 식별
2. `tools/slam/calibrate_camera.py` (아래 스크립트)로 30 ~ 50장 다양한 각도/거리 캡처
3. OpenCV `cv2.calibrateCamera`로 fx, fy, cx, cy + 왜곡 계수 산출

### 1-3. 결과 저장
- `tools/slam/config/skydroid_otg.yaml` 에 저장 (ORB-SLAM3 어댑터가 직접 읽음):
  ```yaml
  Camera.type: "PinHole"
  Camera.fx: 528.4
  Camera.fy: 528.6
  Camera.cx: 320.5
  Camera.cy: 180.2
  Camera.k1: -0.21
  Camera.k2: 0.05
  Camera.p1: 0.0
  Camera.p2: 0.0
  Camera.width: 640
  Camera.height: 360
  Camera.fps: 30.0
  ```

> 정확도 기준: re-projection error **< 0.5 px**. 0.8 이상이면 재촬영.

## 2. 광학흐름 (PMW3901)

### 2-1. INAV CLI 점검
1. Configurator → CLI → `status` 명령
2. `OPFLOW: present, healthy` 확인
3. `task` 명령에서 OPFLOW Hz가 25~50 안정

### 2-2. 표면 시각화 테스트
1. FC를 손에 들고 바닥 위 30cm 평행 이동
2. Configurator → **Sensors** → **Optical Flow** 그래프가 이동 방향에 비례해 변하는지 확인
3. 무특징 표면(흰 벽지/반짝 바닥)에서는 신호가 죽음 — 정상. 패턴 있는 바닥에서만 안정

### 2-3. INAV 가중치 튜닝
- `inav_w_xy_flow_p` 기본 1.0. 실내에서 불안정하면 0.7~1.5 사이로
- `inav_w_xy_flow_v` 기본 2.0. 위와 동일

## 3. ToF (VL53L0X 또는 VL53L1X)

### 3-1. 거리 검증
1. `status` → `RANGEFINDER: present, healthy` 확인
2. Configurator → **Sensors** → **Sonar** 그래프
3. 손바닥을 ToF 센서 앞에 두고 5cm / 30cm / 1m 거리에서 값 확인
4. 노이즈가 ±2cm 이내여야 PositionHold 안정

### 3-2. INAV 가중치
- `inav_w_z_surface_p = 3.5`, `inav_w_z_surface_v = 6.1` (프로파일 기본값)
- 천장 가까이 비행 시 (autonomous 천장 face 캡처) ToF가 천장 거리도 잡음 — INAV는 surface(아래)만 인식하므로 별도 처리 X

## 4. IMU (Kakute H7 Mini 내장)

### 4-1. Acc 캘리브레이션
1. Configurator → Setup → **Calibrate Accelerometer**
2. FC를 평평한 면에 두고 클릭 → 노란색 진행 바
3. 5면 더 (각 면 평행) 반복
4. **Restart** 후 자세계 0,0 표시 확인

### 4-2. 자이로 안정 검증
- FC를 가만히 둔 상태에서 자이로 노이즈 RMS < 0.1 dps
- 진동 큰 위치(모터 가까이)에 두면 노이즈 ↑ — fc 마운트에 폼/실리콘 댐퍼 권장

## 5. 열화상 카메라 (IRC-256CA)

### 5-1. 시간 동기화
- RGB와 열화상은 별도 카메라 → 캡처 시각 정합 필요
- mission_orchestrator의 `CELL_DOUBLE_CAPTURE_SEC = 0.6`이 두 채널 도착을 ±150ms 윈도우로 매칭
- 첫 비행 시 RGB-Thermal 동시 캡처본을 검사 → 시각 차이 큰지 확인

### 5-2. 온도 보정
- IRC-256CA는 출고 시 라벨된 NETC <50mK
- 비행 전 5분 워밍업 → 안정 후 운용

## 캘리브레이션 결과 보존

- `data/calibration/skydroid_otg.yaml`
- `data/calibration/inav_dump.txt` (CLI `dump` 명령 결과)
- `data/calibration/imu_offsets.txt`
- 모든 파일을 git 커밋해 두면 분실 시 빠르게 복구 가능

## 다음 단계

→ [04_field_ops.md](04_field_ops.md) — 단계별 실기 검증 절차
