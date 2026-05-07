# AeroInspect — Pi Zero 2 W 컴패니언 컴퓨터 배포

본 디렉터리는 Pi 측에 올라가는 **메시지 펌프** 코드만 담는다. 자율비행 알고리즘(SLAM/추론/경로계획/회피/FSM)은 모두 백엔드 GPU 서버에서 실행되며, Pi 는 단순한 WS↔UART 게이트웨이다.

## 배선

| Pi GPIO | 신호 | FC(Kakute H7 Mini) |
|---|---|---|
| GPIO14 (TXD) | UART TX → | UART2 RX |
| GPIO15 (RXD) | UART RX ← | UART2 TX |
| GND          | GND  ↔ | GND |
| 5V (BEC)     | 전원 ↔ | (별도 BEC 권장) |

`raspi-config` → Interface Options → Serial Port: 콘솔 비활성화, 하드웨어 UART 활성화.

## 의존성 설치

```bash
sudo apt update
sudo apt install -y python3 python3-pip ffmpeg
sudo pip3 install pyserial websockets
```

## 코드 배포

```bash
sudo mkdir -p /opt/aeroinspect
sudo cp fc_bridge.py thermal_relay.sh /opt/aeroinspect/
sudo chmod +x /opt/aeroinspect/thermal_relay.sh
sudo cp systemd/*.service /etc/systemd/system/
```

## 환경변수 (`/etc/aeroinspect.env`)

```
AEROINSPECT_BACKEND_WS_URL=ws://192.168.1.10:8000/api/v1/mission/fc-bridge
AEROINSPECT_FC_UART=/dev/serial0
AEROINSPECT_FC_BAUD=115200
AEROINSPECT_PI_TOKEN=<공유 시크릿>
AEROINSPECT_THERMAL_DEV=/dev/video0
AEROINSPECT_RTSP_OUT=rtsp://192.168.1.10:8554/thermal
AEROINSPECT_THERMAL_SIZE=256x192
AEROINSPECT_THERMAL_FPS=25
```

## 기동

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now aeroinspect-fc-bridge.service
sudo systemctl enable --now aeroinspect-thermal-relay.service
sudo journalctl -u aeroinspect-fc-bridge -f
```

## 안전

- WS 연결 끊겨도 INAV 의 `failsafe_procedure=LAND` 가 RX/GCS 끊김 시 자동 LAND.
- Pi heartbeat 200ms — 백엔드가 2초 누락 감지 시 INAV `GCS_FAILSAFE` LAND.
- E-Stop: 백엔드 UI → fc_bridge → INAV LAND. 추가로 RC 송신기 보조채널에 LAND 모드 매핑 권장.

## 디버그

- MSP 송수신 raw 로그: `MSP_DEBUG=1` 환경변수 추가 후 실행 (TODO: fc_bridge.py 에 옵션 추가)
- UART 직접 테스트: `screen /dev/serial0 115200` (INAV CLI)
