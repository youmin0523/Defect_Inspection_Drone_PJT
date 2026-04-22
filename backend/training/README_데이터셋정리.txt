========================================
  건물 하자 검출 AI 학습용 데이터셋 정리
  정리일: 2026-04-16
========================================

[폴더 구조]

pjdron 파일들/
├── 하자 관련/
│   ├── Wallpaper_v2_Folder_Classification/   ← 벽지 하자 폴더 분류 (18클래스)
│   └── Papering_Problems_Multiclass/         ← 벽지 하자 멀티라벨 CSV (19클래스)
├── 열화상/
│   ├── Building_Thermal_Inspection_v11/      ← 열화상 박리 탐지 (YOLOv8)
│   └── Thermal_Imaging_in_Building_v1/       ← 열화상 균열+습기 탐지 (YOLOv8)
├── 균열데이터/
│   ├── train/images, labels/                 ← 열화상에서 Crack만 분리 (YOLOv8)
│   ├── test/images, labels/
│   └── data.yaml
├── _원본zip/                                 ← 원본 zip 파일 보관
└── README_데이터셋정리.txt                    ← 이 파일


========================================
하자 관련 (벽지 도배 하자)
========================================

[1] Wallpaper_v2_Folder_Classification
- 출처: Roboflow (CC BY 4.0)
- 포맷: 폴더 기반 이미지 분류 (ImageFolder)
- 이미지: 약 3,462장 (train/valid/test)
- 클래스: 18개
  · Baseboard (걸레받이)     · Crying (울음)
  · Damage (훼손)            · Defective_Joint (이음부불량)
  · Exploded (들뜸)          · Furniture (가구수정)
  · Gypsum (석고)            · Kink (꼬임)
  · Many_niches (틈새과다)   · Mold (곰팡이)
  · Molding (몰딩)           · Piece (조각)
  · Plane (면불량)           · Pollution (오염)
  · Rust (녹오염)            · Spot (반점)
  · W.F_D.F (창틀/문틀)      · Wrong_punch (오타공)
- 참고: PyTorch ImageFolder, tf.keras.utils.image_dataset_from_directory 등으로 바로 로딩 가능

[2] Papering_Problems_Multiclass
- 출처: Roboflow
- 포맷: 멀티클래스 분류 (CSV 라벨)
- 이미지: 3,897장 (train 2,727 / valid 779 / test 391)
- 라벨 파일: 각 폴더의 _classes.csv
- 클래스: 19개 (한국어)
  · 가구수정, 걸레받이수정, 곰팡이, 꼬임, 녹오염
  · 들뜸, 면불량, 몰딩수정, 반점, 석고수정
  · 오염, 오타공, 울음, 이음부불량, 창틀/문틀수정
  · 터짐, 틈새과다, 피스, 훼손
- 참고: _classes.csv에서 원-핫 인코딩 형태로 라벨 제공


========================================
열화상 (건물 열화상 검사)
========================================

[3] Building_Thermal_Inspection_v11
- 출처: Roboflow (CC BY 4.0)
- 포맷: YOLOv8 객체탐지
- 이미지: 약 403장 (train/valid/test)
- 클래스: 1개 — delamination (박리)
- 설명: 열화상 카메라로 촬영한 건물 외벽의 박리 결함 탐지

[4] Thermal_Imaging_in_Building_v1
- 출처: Roboflow (CC BY 4.0)
- 포맷: YOLOv8 객체탐지
- 이미지: 약 615장 (train/valid/test)
- 클래스: 2개 — Crack (균열), Moisture (습기)
- 설명: FLIR 열화상 카메라로 촬영한 건물 내부/외부 결함 탐지


========================================
균열데이터 (열화상에서 Crack 분리)
========================================

[5] 균열데이터 (Thermal_Imaging_in_Building에서 추출)
- 포맷: YOLOv8 객체탐지
- 이미지: 26장 (train 24 / test 2)
- 클래스: 1개 — Crack (균열)
- 설명: 열화상 데이터셋 [4]에서 Crack 라벨이 있는 이미지만 분리
- 참고: 원본 데이터는 열화상 폴더에도 그대로 남아있음 (복사본)


========================================
학습 시 참고사항
========================================
- 데이터셋 [1]과 [2]는 거의 동일한 하자 유형을 다루지만 포맷이 다름
  · [1] = 폴더 분류 (단일 라벨) → ImageFolder 로딩에 적합
  · [2] = CSV 멀티라벨 → 멀티라벨 분류에 적합
- 데이터셋 [3], [4], [5]는 YOLOv8 포맷 → Ultralytics로 바로 학습 가능
  · 예: yolo train model=yolov8n.pt data=data.yaml
- 모든 데이터셋은 CC BY 4.0 라이선스 (출처 표기 시 자유 사용 가능)
