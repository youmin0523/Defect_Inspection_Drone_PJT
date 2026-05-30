# 약점 모델 보강 실행 계획 (2026-05-30)

컨셉: 약점 모델은 Roboflow 데이터(상업 가능 라이선스) + 우리 데이터로 추가 fine-tuning → 우리 모델.
강한 모델(M1/M2/M3)은 fine-tune 대신 Roboflow twin + WBF 앙상블(후순위).
실행: 로컬 순차(GCP X), GPU 1개씩만(OOM 방지), 데이터는 이미 전량 로컬.

## 현재 자동 가동 상태
- M4 seg: resume_m4_seg.py (pid 3616) 진행 중 — 건드리지 않음.
- 대기 체인: auto_after_m4.ps1 (M4 종료 감지 → thermal → furniture 순차, GPU<2500MiB 확인 후 시작).
- 모니터: cron c6a1a8b6 (5분), monitor_status.ps1 → PushNotification.

## 로컬 데이터 현황 (다운로드 불필요)
| 데이터셋 | train | val |
|---|---|---|
| thermal_yolo | 6994 | 595 |
| furniture_aware | 23215 | 2117 |
| frames (M5) | 7068 | 442 |
| m4_context | 41856 | 4220 |

## 학습 스크립트 보유 여부
- thermal: train_thermal_yolo.py ✅ (device=0, yolov8m, imgsz960)
- furniture: train_furniture_aware.py ✅ (device=0, yolov8m, imgsz640, 80ep)
- M4 seg: train_m4_context_seg.py / resume_m4_seg.py ✅
- M5 frames: ❌ 전용 스크립트 없음 → 작성 필요 (frames data.yaml 클래스명이 '0'~'3','object' 제네릭이라 매핑 확인 후 작성)

## 순서
1. (진행중) M4 seg 완주
2. thermal fine-tune (체인 자동)
3. furniture fine-tune (체인 자동)
4. M5 frames — 스크립트 작성 후 학습 (수동 단계)
5. M1/M2/M3 — Roboflow twin + WBF 앙상블 (후순위)

## Roboflow 후보 (자체 학습용 데이터 소스, .pt 직접 다운 불가 → 데이터셋+자체학습)
- thermal: roboflow_thermal_candidates.md (idt 6클래스, scanx — CC BY 4.0)
- M4/furniture/M5: roboflow_other_candidates.md
  - M4 context: panopticindoor/panoptic-indoor-segmentation, bytetrooper/room-detection-tfaxd (CC BY 4.0 seg)
  - furniture: panoptic-indoor + countortop/insignia (kitchen_island·built-in은 자체 라벨 필요)
  - M5 frames: walls-door-detection, nicolai/window-segmentation(PD) — frame-ring은 자체 라벨 필요
- 채택 전 라이선스 칩 육안 확인 필수(스니펫 기반, NC 배제).
