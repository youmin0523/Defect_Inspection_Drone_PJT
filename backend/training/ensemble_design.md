# Roboflow 학습모델 × 우리 모델 WBF Ensemble 설계 (2026-05-30)

## 원칙
- **우리 모델이 주력(primary).** Roboflow 학습모델은 second-opinion으로 WBF 가산 → Recall 보강.
- 모든 추론은 **로컬**(rfenv py3.12 + inference, CPU/GPU). 이미지 외부유출 X.
- 채택 전 **라이선스**(CC BY 4.0/MIT/PD = OK) + **클래스 매핑 정합성**([[feedback_onnx_class_mapping_audit]]) 확인.
- Recall 우선([[feedback_recall_priority_paid_service]]) — 보조모델은 conf 낮게(0.05~0.10) 운용, CONFIRMED 등급은 우리 모델+합의 시에만.

## 검증 결과 기반 채택/제외 (CPU, conf 0.05)

### ✅ 채택 (검출 작동 + 클래스 정합)
| 대상 | model_id | 검출률 | 클래스 | 비고 |
|---|---|---|---|---|
| thermal | thermal-images-in-building-inspection/3 | 80% | moisture/delamination/insulation/air leakage 등 6 | 단열(B-01/B-02) 보강 핵심. mAP 미상 |
| M1 균열 | crack-bphdr/2 | 100% | crack (seg) | mAP 22.49(낮음)지만 검출 활발, 미탐보강용 |
| M1 균열 보조 | crack-bphdr-g9koq/1 | 100% | crack_detection (bbox) | 2차 보조(선택) |
| M3 유리 | glass-defect-detection-fvbcu/**2** | 26% | defect | ⚠️ v3아닌 **v2가 배포본**(mAP 87.85). 진짜 유리결함 |
| M4 context | wall-ceiling-floor-m6bao/1 | 100% | wall/ceiling/floor (seg) | 게이팅 보조 |
| M5 창호 | windows-instance-segmentation/5 | 100% | Window (seg) | 창호 영역 보조 |

### ⚠️ 보류 (검출되나 클래스 부적합/불일치)
| 모델 | 사유 |
|---|---|
| glass-xqjx8/1 | misaligned/open = 설치불량, 유리'하자' 아님 |
| walls-door-detection/1 | 클래스명 `-`,`undefined` 깨짐 → 매핑 불가 |
| room-detection-tfaxd/1 | 클래스 `0`,`2` 익명, 50%로 약함 |
| window-segmentation/1 | Window 909건/6장 = 과검출 의심 |
| crack-bphdr-bl00w/1 | 클래스에 메타문자열 혼입(라벨 오염) |

### ❌ 제외 (배포모델 없음 = 데이터셋 전용)
| 모델 | 사유 |
|---|---|
| building-defect-on-walls/4 | 전 버전 model={} → 추론 불가. **데이터로만** 활용 가능(water_seepage 등) |
| glass-defect-detection-fvbcu/3 | v3 미배포(v2만 배포) |
| glass-defect-detection-qjchk/1 | LOAD FAIL |
| defects-on-surfaces-paint/1, window-detection-tzxgz/1 | 0% 검출 |

## 통합 방식 (구현 계획)
1. **추론 어댑터**: `inference.get_model`(rfenv)로 채택모델 추론 → 우리 detection 포맷(bbox normalized + score + class)으로 변환하는 `roboflow_adapter.py`.
2. **클래스 매핑 테이블**: Roboflow 클래스 → 우리 taxonomy(B-01/B-02, crack, glass_defect 등) 명시. 매핑 불가 클래스는 drop.
3. **WBF 결합**: 기존 eval WBF 인프라(backend/training/eval) 재사용 — 우리 모델 가중치↑(예 2.0), Roboflow 보조 가중치↓(예 0.5~1.0). [[feedback_postprocess_strength_policy]] 따라 강한 우리 모델엔 약하게.
4. **운영 통합**: production은 ONNX 파이프라인이라, 상시 Roboflow 런타임 의존은 부담. → 1차는 **오프라인 검증/평가 단계 ensemble**로 효과 측정 후, 효과 크면 해당 데이터로 우리 모델 재학습(증류)하는 경로 권장.

## 라이선스 TODO (상업 출시 전 필수)
- 채택 6모델의 License 칩 육안 확인. 스니펫상 CC BY 4.0 다수지만 thermal idt·glass fvbcu·windows-inst 미확정 → 확인 후 확정.

## 데이터로만 활용 (배포모델 없는 양질 데이터셋)
- building-defect-on-walls (crack/mold/peeling_paint/stairstep_crack/water_seepage, CC BY 4.0) → M1/M2 **재학습 데이터** 보강에 사용.

관련: [[project_roboflow_inference_ensemble]] [[project_roboflow_finetune_program]]

## Recall 최우선 Ensemble 정책 (2026-06-01 사용자 지시: "놓치는거 없이 정확한 검출")

목표 우선순위 (feedback_recall_priority_paid_service):
1. **Recall ≥99%** — 놓치면 사용자 사후 발견 = 망한 서비스. 절대 1순위.
2. **CONFIRMED Precision ≥90%** — 오탐 시 출장비 분쟁. 2순위.

### 설계 (양날 관리 — Recall↑ 하되 Precision 방어)
1. **검출 단계 = Recall 최대화**:
   - WBF skip_box_thr=0.0001 (약한 검출도 살림, 이미 세팅됨)
   - 우리 모델 + Roboflow 보조모델(채택6) 모두 낮은 conf(0.05~0.10)로 추론 → 합집합
   - 보조모델은 "second opinion"으로 우리가 놓친 것 보강
2. **등급 단계 = Precision 방어** (confidence_grader 활용):
   - 합쳐진 검출을 CONFIRMED/REVIEW/REFERENCE 3등급으로 분리
   - **우리 모델 + 보조모델 합의(둘 다 검출)** → CONFIRMED (Precision 높음)
   - 한쪽만 검출 → REVIEW (놓치지 않되 사용자 확인 유도)
   - 이렇게 하면 Recall(전부 보고) + Precision(CONFIRMED만 신뢰) 둘 다 확보
3. **WBF 가중치**: 우리 모델 2.0 / Roboflow 보조 0.5~1.0 (feedback_postprocess_strength_policy — 강한 모델 우대)
4. **thermal 예외**: v11(mAP50-95 0.263) < v1(0.808) → ensemble 전 v1 vs v11 test 비교 후 더 나은 쪽 채택. 단순 합산 금지.

### 검증 (ensemble 채택 가/부 판단 = 실측)
- test_external 7카테고리로 before(우리 단일) vs after(ensemble) 측정:
  - 검출률(Recall proxy): 놓친 GT 수 비교
  - 오탐(Precision proxy): 가짜 검출 수 비교
- **Recall 오르고 Precision 안 떨어지면 채택. Precision 크게 떨어지면 해당 보조모델 제외 또는 가중치↓.**
- 모델별 개별 판단 (전부 일괄 채택 금지).
