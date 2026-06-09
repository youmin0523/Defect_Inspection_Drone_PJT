# Roboflow Universe 대체 데이터셋 검증 (2026-06-02)

약점 모델 보강용 신규 후보. 검증 방식: rfenv python + requests 로 `/{ws}/{proj}/{ver}/yolov8`
export link 를 실제 GET → ZIP(PK 헤더) 확인. **ZIP_OK 만 실다운로드 가능.**
HTTP 202(생성중)는 15s 간격 재시도 후 판정. 검증 스크립트: `training/verify_alt_export.py`, `verify_alt_export2.py`.

중복 제외(기사용): thermal idt/3, scanx nmh6j/2, M2 builddef, M4 wall-ceiling-floor-m6bao, room-detection-tfaxd, walls-door-detection, glass-defect-detection-fvbcu.

## M4 context (실내 wall/ceiling/floor 시맨틱) — 우리 [wall, ceiling, floor, window, door]

| 모델 | workspace/project | version | classes | license | 다운로드 |
|---|---|---|---|---|---|
| M4 | wallceilingfloor/wall-ceiling-floor-m6bao | 1 | wall, ceiling, floor (seg) | CC BY 4.0 | ZIP_OK (※기사용) |
| **M4 ★채택** | x-aqdd1/wall-floor-bjbya | 2 | background, floor, wall (seg) | CC BY 4.0 | **ZIP_OK** |
| M4 | part2val/wall-floor-hzf1m | 2 | floor, wall (seg) | CC BY 4.0 | ZIP_OK |
| M4 | part1-3dlw1/wall-floor-vc6qx | 2 | floor, wall (seg, 大) | CC BY 4.0 | ZIP_OK (v1 202) |
| M4 | celebal-henxz/wall-ceiling | 2 | ceiling, wall (seg) | CC BY 4.0 | ZIP_OK (v3/v1 202) |
| **M4 ★채택2** | park-jong-il-k1lxw/wall-floor-ceiling-recognition | 2 | ceiling, walls, floor (det) | CC BY 4.0 | **ZIP_OK** |
| M4 | celebal-technologies/walls-floor-detection | 2,3 | ceiling, floor, wall, frame | CC BY 4.0 | EXPORT_404 |
| M4 | test-3vtzt/mit-indoor-semantic-segmentation | 1,2 | (실내 다클래스) | CC BY 4.0 | HTTP 400 |

채택: **x-aqdd1/wall-floor-bjbya v2** (seg, wall/floor 대용량, 클래스 정확 일치) — seg 보강 1순위.
보조: park-jong-il/wall-floor-ceiling-recognition v2 (det, ceiling 포함 3클래스 완비).

## furniture (실내 빌트인 가구: cabinet/appliance/countertop)

| 모델 | workspace/project | version | classes | license | 다운로드 |
|---|---|---|---|---|---|
| **furn ★채택** | kitchenobjectdetection/kitchen-object-detection-acyvk | 1 | sink, countertopwood, countertopstone, refrigerator, microwave, blender ... | CC BY 4.0 | **ZIP_OK** |
| furn | ai2thor/ai2thor-kitchen-items-actions | 2 | Cabinet, CounterTop, Microwave, Sink ... (69cls, 합성) | CC BY 4.0 | ZIP_OK |
| furn | furniture-pp9ke/furniture-o6003 | 2 | bed, table, chair, closet, bookshelf, couch ... | CC BY 4.0 | ZIP_OK |
| furn | furniture-d9qab/furniture-hpuyb | 2 | sofa, bed, chair, carpet ... (빈클래스 다수) | CC BY 4.0 | ZIP_OK |
| furn | projects-iucr4/appliances | 2 | Rice Cooker, Microwave, Kettle (소량) | MIT | ZIP_OK |
| furn | cabinet-detection/floorplan-cabinet-detection | 2 | cabinet, sink, kitchen 등 | **Private** | ZIP_OK→제외(라이선스) |

채택: **kitchenobjectdetection/kitchen-object-detection-acyvk v1** — countertop(wood/stone)·sink·built-in appliance
실물(합성 아님) 라벨로 빌트인 가구 보강에 가장 적합. (ai2thor 는 합성렌더라 도메인갭, 보조용.)

## M3 floor_window (유리/창호 결함: glass defect)

| 모델 | workspace/project | version | classes | license | 다운로드 |
|---|---|---|---|---|---|
| **M3 ★채택** | maruf-workspace/glass-defect-detection-qjchk | 1 | scratch, broken, chipping, polish problem | CC BY 4.0 | **ZIP_OK** |
| M3 | yolo-0avst/scratch-fvsd0 | 1 | SCRATCH, DENT, PITS_and_CORROSION (금속 표면) | CC BY 4.0 | ZIP_OK (도메인갭) |

채택: **maruf-workspace/glass-defect-detection-qjchk v1** — 유리 결함(scratch/broken/chipping) 직접 일치.
(scratch-fvsd0 은 금속표면 결함이라 유리 도메인 아님 → 보조 불가.)

## thermal (건물 열화상 단열결함: FLIR pseudocolor) — 가장 중요, 가장 부족

| 모델 | workspace/project | version | classes | license | 다운로드 | 도메인 |
|---|---|---|---|---|---|---|
| thermal (보류) | university-of-ottawa-thermal-anomaly/thermal-anomaly-test-1 | 1 | Thermal Anomaly(1633), items | CC BY 4.0 | **ZIP_OK** | 일반 thermal anomaly, 건물여부 육안확인 필요 |
| thermal (제외) | solveview/thermal-defects | 9 | PID, Hotspot | CC BY 4.0 | ZIP_OK | 태양광/전기 hotspot → 건물 아님 |
| thermal (제외) | murtazakhan/thermal-anomaly-detection-1 | 2 | violence, human_fall | CC BY 4.0 | ZIP_OK | 감시(surveillance) → 건물 아님 |
| thermal | iit-m-7qnrz/defect-sjree | 1 | Defect(48, seg) | CC BY 4.0 | ZIP_OK (v2 404) | 일반 defect seg, 열화상/건물 불명 |

채택 권장: **없음(확정).** 건물 열화상 단열결함 전용으로 ZIP_OK + 도메인 적합 + 미사용인 신규
프로젝트는 이번 스캔에서 발견 못함. Roboflow 의 양질 건물 thermal(idt/scanx)은 이미 사용 중.
- ottawa thermal-anomaly-test-1: ZIP_OK·CC BY 4.0 이지만 "Thermal Anomaly" 단일 라벨이 건물 단열인지
  타 도메인인지 페이지 차단(403)으로 미확정 → **육안 샘플 확인 후 채택 판단** (조건부 보류).
- TBBR(Thermal Bridges on Building Rooftops, Karlsruhe, FLIR-XT2 drone): 도메인 최적이나
  Roboflow 아님(Zenodo 7022736). 별도 다운로드 경로 필요. CC BY 4.0.

## 채택 요약 (모델별 1개)
- **M4**: x-aqdd1/wall-floor-bjbya v2 (seg) — ZIP_OK, CC BY 4.0
- **furniture**: kitchenobjectdetection/kitchen-object-detection-acyvk v1 — ZIP_OK, CC BY 4.0
- **M3**: maruf-workspace/glass-defect-detection-qjchk v1 — ZIP_OK, CC BY 4.0
- **thermal**: 적합 신규 없음. ottawa thermal-anomaly-test-1(ZIP_OK) 조건부 보류 / TBBR(Zenodo) 별도 검토
