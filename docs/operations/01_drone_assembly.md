# 01. 드론 조립 가이드 — AeroInspect Cinewhoop v1.1

> 본 문서는 본 시스템의 BOM 기준으로 조립 절차를 정리합니다. 안전상 모든 작업은 **배터리 분리 상태**에서 진행하고, 첫 시동 전 반드시 [04_field_ops.md](04_field_ops.md) 사전 점검을 거치세요.

## 부품 목록(BOM)

| 카테고리 | 부품 |
|---|---|
| 프레임 | GEPRC GEP-CL35 V3 또는 Cinelog35 V3 (3.5인치 cinewhoop) |
| FC | Holybro Kakute H7 Mini 2020 |
| ESC | Holybro Tekko32 F4 4in1 mini 45A |
| 모터 | GEPRC SPEEDX2 1804 2450/3450KV ×4 |
| 프롭 | HQPROP T76MMx3 (76mm 3블레이드) |
| VTX/카메라 | DJI O4 Pro Air Unit (4K) |
| 영상 수신 | Skydroid FUAV 5.8GHz USB OTG (백엔드 PC 측) |
| 위치/거리 | Matek PMW3901 광학흐름 + VL53L0X (혹은 VL53L1X 권장) ToF |
| 배터리 | GAONENG GNB 1100mAh 14.8V 4S 120C |
| 컴패니언 | Raspberry Pi Zero 2 W (512MB) + 냉각 케이스 |
| 저장 | Samsung EVO Plus microSD 64GB+ |
| 열화상 | 기존 IRC-256CA (Holybro S500용 보유 자산 이식) |
| BEC | U-BEC 5V 3A (2~6S) |
| 배선 | JST SH 1.0mm 커넥터 세트 + 18~30AWG 실리콘 와이어 |

## 조립 순서

### 1. 프레임 + 모터 + ESC
1. 프레임 베이스 플레이트에 모터 4개 장착 — **회전 방향 확인**(좌상/우하 CW, 좌하/우상 CCW)
2. ESC 4-in-1 PDB 위치에 고정 (수축튜브 + 양면 폼)
3. ESC 출력선 → 모터 (3선 솔더링, 색상 통일 권장)
4. ESC 신호선 → FC 의 모터 1~4 패드 (FC 보드 도식 참조)

### 2. FC + 컴패니언 컴퓨터
1. Kakute H7 Mini를 ESC 위 standoff로 격리 장착 (4mm 이상)
2. **UART2** 패드 → Pi GPIO14(TX)/GPIO15(RX) — TX↔RX 교차
3. FC 5V 패드 → Pi 5V (또는 별도 BEC) + GND 공통화
4. PMW3901 + VL53L0X 모듈 → FC **UART4** + I2C
5. DJI O4 Pro Air Unit → FC SBus/CRSF 신호선 + 별도 BEC 5V

### 3. 안테나 + 영상 시스템
- DJI O4 안테나는 본체 외부로 빼서 신호 차폐 최소화
- 카메라는 프레임 노즈 마운트 (각도 살짝 위 권장 — 자율비행 천장 캡처용)

### 4. 열화상(이전 BOM 자산 이식)
- IRC-256CA를 노즈 또는 하단 짐벌 마운트에 고정 (RGB와 가까울수록 동기화 좋음)
- USB → Pi USB 포트
- 무게: **추가 약 60~80g** → 비행시간 약 8~12분으로 단축 (배터리 1100mAh 4S 기준)

### 5. 배터리 + Pi microSD
- 배터리 마운트 위치는 무게 중심 정중앙
- Pi microSD에 Raspbian Lite 32-bit 설치 후 [pi/README.md](../../pi/README.md) 절차 적용

## 배선 점검 체크리스트

조립 완료 후 **배터리 연결 전** 다음을 확인:

- [ ] 모든 솔더링이 단단함 (fingertip pull test)
- [ ] 단락 없음 (멀티미터 통전 검사 — 5V↔GND, VBAT↔GND)
- [ ] 모터 회전 방향 4개 모두 표시됨 (스티커 또는 매직)
- [ ] FC UART2 핀 배선이 Pi 와 교차 (TX↔RX)
- [ ] 광학흐름 모듈 렌즈가 아래(바닥)를 향함
- [ ] ToF 모듈이 막힘 없음
- [ ] 안테나 케이블이 모터/프롭에 닿지 않음

## 다음 단계

→ [02_inav_flashing.md](02_inav_flashing.md) — INAV 펌웨어 + AeroInspect CLI 프로파일
