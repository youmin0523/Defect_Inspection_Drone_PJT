# 02. INAV 펌웨어 플래싱 + AeroInspect 프로파일 적용

> Kakute H7 Mini에 INAV 7.x를 플래싱하고 [`tools/inav/aeroinspect_profile.txt`](../../tools/inav/aeroinspect_profile.txt) 프로파일을 한 번에 적용합니다. **프롭 분리 상태**에서 진행하세요.

## 사전 준비

- INAV Configurator 최신 (https://github.com/iNavFlight/inav-configurator/releases)
- USB Type-C 케이블 (데이터 가능)
- 빈 microSD 카드 권장 (블랙박스용)
- 윈도우면 ImpulseRC Driver Fixer (FC가 DFU 모드 인식 안 될 때)

## 1. INAV 펌웨어 플래싱

1. FC 의 boot 버튼을 누른 채 USB 연결 → DFU 모드 진입
2. INAV Configurator → **Firmware Flasher** 탭
3. Board: **MATEKH743** 또는 **KAKUTEH7MINI** 검색 → INAV 7.x 최신 안정버전 선택
4. **Full chip erase** ✓ + **Flash on Connect** ✓
5. **Load Firmware [Online]** → **Flash Firmware**
6. 플래싱 완료 후 자동 재부팅 → Configurator가 다시 연결됨

## 2. AeroInspect CLI 프로파일 적용

1. Configurator → **CLI** 탭 진입
2. 텍스트 에디터에서 [`tools/inav/aeroinspect_profile.txt`](../../tools/inav/aeroinspect_profile.txt) 전체 내용 복사
3. CLI 입력창에 붙여넣기 → Enter
4. 마지막 줄 `save` 가 자동 실행되면서 FC 재부팅
5. CLI에서 `diff all` 으로 적용 결과 확인:
   ```
   feature OPFLOW
   feature TELEMETRY
   feature -GPS
   ...
   ```
   가 들어 있으면 OK

## 3. 핵심 설정 검증 (Configurator 탭별)

| 탭 | 확인 항목 |
|---|---|
| **Configuration** | Mixer = QUADX, ESC/Motor protocol = DSHOT600 권장 |
| **Ports** | UART2 = MSP @ 115200, UART4 = SmartPort/Telemetry 비활성 (광학흐름이 사용) |
| **Modes** | ARM/ANGLE/POSHOLD/NAV WP/NAV RTH/NAV LAND 가 AUX 채널에 매핑됨 |
| **Receiver** | RX 신호 수신 확인 (DJI O4 SBus/CRSF) |
| **Sensors** | OPFLOW + RANGEFINDER 활성, IMU 안정 |

## 4. 프롭 OFF 회전 방향 검증 (모터 1~4)

> **반드시 프롭 분리 상태**

1. Configurator → **Motors** 탭
2. **Motor Test Mode** ✓
3. Master 슬라이더를 1100 부근까지 살짝 ↑ → 4개 모터가 천천히 도는지 확인
4. Motor 1/2/3/4 슬라이더 각각 올려서 **회전 방향**이 프레임 도식과 일치하는지 확인
5. 반대로 도는 모터가 있으면:
   - **DSHOT** 사용 시: Configurator에서 해당 모터 우클릭 → **Reverse Direction**
   - 또는 ESC 출력선 3선 중 2선을 swap

## 5. 가속도계 / 자기계 캘리브레이션

- **Setup** 탭 → **Calibrate Accelerometer**: FC를 6면 평평하게 두고 각 면마다 캘리브레이션
- (실내 자율비행에선 자기계 미사용 — 광학흐름 + IMU 만으로 위치 추정)

## 6. PID 초기 검증 (호버 안정성)

본 프로파일의 PID는 cinewhoop 1804/3450KV 기준 보수적 시작값입니다. 첫 호버 후 진동이 있으면:
- **PID Tuning** 탭에서 P/D 5%씩 단계적 조정
- 완전히 튜닝 안 된 상태에선 **속도 0.3 m/s 이하**로만 운용

## 다음 단계

→ [03_calibration.md](03_calibration.md) — 카메라/광학흐름/ToF 정밀 캘리브레이션
