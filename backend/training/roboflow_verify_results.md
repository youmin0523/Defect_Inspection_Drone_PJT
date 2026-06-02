# Roboflow 학습모델 검증 (CPU, conf=0.05, 2026-05-30 15:24)

검출률 = test 이미지 중 1건+ 검출 비율(Recall proxy). 우리 모델과 ensemble 보조 기여 가늠용.

| 모델 | model_id | N | 검출(장%)/건 | 상위클래스 |
|---|---|---|---|---|
| thermal-idt-6cls(thermalval) | thermal-images-in-building-inspection/3 | 40 | 32(80%)/134 | moisture:110, delamination:12, insulation:7, air leakage:3 |
| M1-building-defect(crack) | building-defect-on-walls/4 | - | LOAD FAIL | Could not find requested Roboflow resource. Check  |
| M1-crack-seg(crack) | crack-bphdr/2 | 40 | 40(100%)/980 | crack:980 |
| M3-glass-capjamesg(glass) | glass-defect-detection-fvbcu/3 | - | LOAD FAIL | Could not find requested Roboflow resource. Check  |
| M4-room-detection(surface) | room-detection-tfaxd/1 | 6 | 3(50%)/5 | 0:4, 2:1 |
| M4-wall-ceiling-floor(surface) | wall-ceiling-floor-m6bao/1 | 6 | 6(100%)/7 | wall:6, ceiling:1 |
| M5-walls-door(surface) | walls-door-detection/1 | 6 | 6(100%)/130 | -:80, undefined:50 |
