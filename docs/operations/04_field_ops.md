# 04. 필드 운용 — 단계별 실기 검증 절차

> 본 문서는 자율비행을 **실내 실기 환경**에서 단계적으로 검증하는 절차입니다. 각 단계는 이전 단계가 통과한 후에만 진행하세요. 안전상 **모든 비행은 사람 1인 RC 송신기를 든 채 대기**하고, 첫 자율비행 단계에선 **그물망 또는 닫힌 안전공간**을 권장합니다.

## 사전 점검 — 매 비행 전 체크리스트

### 하드웨어
- [ ] 프롭 4개 모두 단단히 조여짐 + 손상 없음
- [ ] 모터 4개 자유 회전(걸림 없음)
- [ ] 배터리 voltage ≥ 16.0V (4S 4.0V/cell)
- [ ] 배터리 strap 단단함
- [ ] 안테나가 모터 회전면과 안 닿음

### 소프트웨어
- [ ] INAV Configurator → `status` : 모든 센서 healthy
- [ ] 광학흐름 / ToF 표시 정상
- [ ] Pi `systemctl status aeroinspect-fc-bridge` Active(running)
- [ ] 백엔드 `GET /api/v1/mission/state` 응답에 `fc_attached: true`
- [ ] DJI Goggle/수신기 영상 신호 정상

### 환경
- [ ] 비행 공간 4m × 4m 이상 + 천장 2.4m+
- [ ] 바닥에 패턴 있는 매트 또는 카펫 (광학흐름 필수)
- [ ] 강한 자연광/그림자 변화 없음
- [ ] 사람·반려동물·장애물 정리

## Stage A — 백엔드 단위/통합 무비행 검증

```bash
# 단위 테스트 (외부 환경 없이)
pytest backend/app/tests/test_path_planner.py \
       backend/app/tests/test_room_segmenter.py \
       backend/app/tests/test_obstacle_avoider.py \
       backend/app/tests/test_floorplan_verifier.py \
       backend/app/tests/test_inspection_area.py \
       backend/app/tests/test_safety_monitor.py \
       backend/app/tests/test_mission_orchestrator_fsm.py
```

모두 통과 후 다음 단계.

## Stage B — INAV SITL 가상 검증 (실기 없음)

```bash
# 1) SITL + socat 가상 UART 기동
bash tools/inav-sitl/run.sh up

# 2) 별도 터미널 — Pi 측 fc_bridge 가상 UART 연결
AEROINSPECT_FC_UART=/tmp/aeroinspect-fc-uart \
AEROINSPECT_BACKEND_WS_URL=ws://localhost:8000/api/v1/mission/fc-bridge \
python3 pi/fc_bridge.py

# 3) 백엔드 띄우기
cd backend && uvicorn app.main:app --reload

# 4) 통합 테스트
pytest --integration backend/app/tests/integration/
```

`test_arm_does_not_disarm_due_to_aux` 통과 → 버그 #10 회귀 없음.

## Stage C — 실기 단계적 검증

> 각 단계 통과 후 다음. 진동·표류·이상음 발생 시 즉시 LAND 후 분석.

### C-1. 수동 ARM + 정지 확인 (지면 위)
- RC 송신기로 직접 ARM → 모터가 idle RPM (20~30%) 회전 시작
- 5초간 가만히 둔 채 진동/소음 확인
- DISARM

### C-2. 수동 hover 1m, 30초
- RC 송신기 + ANGLE 모드
- 천천히 throttle ↑ → 1m 호버
- 30초 안정 — 진동 없으면 PID 문제 없음
- DISARM

### C-3. INAV PositionHold 1분 hover (자율 시동)
- AUX 채널을 POSHOLD 로 전환 → 광학흐름 + ToF 가 위치 잡음
- 1분 호버 → ±0.3m 이내 흔들림이면 OK
- 백엔드 텔레메트리 화면에서 pos_x/pos_y 변화 확인

### C-4. 백엔드 외부 명령 검증 (단순 직진)
1. RC 송신기로 ARM
2. POSHOLD 진입
3. 백엔드 → `POST /api/v1/mission/start` (Pi attach 필수)
4. mission_orchestrator 가 _do_takeoff → MAPPING(짧게) 진입
5. 사람 RC 송신기 항시 "테이크오버 가능" 모드 유지
6. 1m 직진 + 1m 후진 후 PATH_PLAN 단계 진입 시도

### C-5. 단일 룸 단일 면 보스트로페돈 (벽 1면만)
- `path_planner.params.scan_walls=True, scan_ceiling=False, scan_floor=False, scan_windows=False`
- 룸 폴리곤은 prior_polygons 로 직접 입력 (4×4m 직사각형)
- mission start → 벽 4면 중 1개 면만 선택해 그리드 비행
- 통과 기준: 비행 종료 후 coverage ≥ 90% + 충돌 없음

### C-6. 단일 룸 4면 + 천장 + 바닥 + 창호
- 모든 face 토글 ON
- nose-tilt 가 동작하는지 — 천장/바닥 face WP 에서 자세가 ±30° 이내로 기울어짐 + 즉시 복귀
- 통과 기준: 룸 전체 captured ≥ 95%

### C-7. 다중 룸 자동 전환 (도어웨이 통과)
- 두 룸 (room_segmenter 가 자동 분리) + 폭 0.85m 도어웨이
- mission start → 첫 룸 완료 후 자동 전환
- 통과 기준: 도어웨이 통과 시 속도 ≤ 0.25 m/s, 충돌 없음

## 비상 절차

### LAND (정상 종료)
- UI `RTL` 또는 `START` 버튼 토글 OFF
- INAV 자체 LAND 모드 진입 → 천천히 하강 후 자동 disarm

### E-Stop (비상 정지)
- UI `E-STOP` 버튼 (빨강, 항상 활성)
- 어떤 phase 에서도 즉시 LAND 강제
- 모터 즉시 정지가 아닌 LAND — 추락 방지

### RC 테이크오버
- RC 송신기에서 ANGLE/MANUAL 모드로 AUX 전환 → INAV 가 자율 명령 무시하고 RC 입력 우선
- 위험 상황 시 가장 빠른 안전 회피

### Fail-safe 자동 동작
| 트리거 | 자동 동작 |
|---|---|
| RC 끊김 (`failsafe_procedure=LAND`) | 즉시 LAND |
| Pi heartbeat > 2초 누락 | INAV `GCS_FAILSAFE` LAND |
| 배터리 < 35% 또는 셀당 < 3.55V | 백엔드 `safety_monitor` → RTL |
| SLAM 신뢰도 저하 | obstacle_avoider hover → 1.5초 안 회복 → LAND |
| 자세 ±60° 초과 | safety_monitor → LAND |

## 비행 후 절차

1. 배터리 분리
2. microSD 비행 로그 백업 (INAV blackbox + 백엔드 mission_plans + coverage_grids)
3. 점군/영상 백업 (`data/pointclouds/<mission_id>/`)
4. 4면 face 별 captured 비율 확인 — `GET /api/v1/coverage/mission/<id>/summary`
5. 결함 검출 결과 + 차이영역 리포트 확인 (`/api/v1/defects` + verification.discrepancies)

## 트러블슈팅

| 증상 | 원인 후보 | 대응 |
|---|---|---|
| ARM 후 즉시 disarm | RC 캐시 / failsafe / 자세 큼 | 본 펌웨어의 RC 캐시 적용됐는지(`pi/fc_bridge.py` 최신) 확인 |
| PositionHold 표류 | 광학흐름 무특징 / ToF 노이즈 | 패턴 있는 바닥, ToF 1m 미만 검증 |
| `/mission/start` 412 fc_bridge_not_attached | Pi WS 연결 실패 | systemctl status / 토큰 / Wi-Fi |
| `/mission/start` 412 skydroid_otg_not_recognized | OTG 미인식 / 디코딩 실패 | 다른 USB 포트 / 디바이스 인덱스 / OS 백엔드 |
| 천장 face WP 에서 추락 | nose-tilt ±30° 임계 초과 / 추력 부족 | TILT_CAPTURE_LIMIT_RAD 줄이기 / 배터리 신선도 |
| PATH_PLAN skip | occupancy 미생성 + prior 미입력 | SLAM_BACKEND=dummy 검증 / prior_polygons 입력 |
