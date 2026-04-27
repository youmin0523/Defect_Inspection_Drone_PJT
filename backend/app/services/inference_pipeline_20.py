# =============================================
# app/services/inference_pipeline_20.py
# 역할: 20종 하자 6-Model + Geometric 통합 추론 파이프라인
#       - M1: YOLO(구조·방수) + ResNet(균열 분류)     → ONNX
#       - M2: YOLO(마감·표면) + ResNet(표면 분류)     → ONNX
#       - M3: YOLO(바닥·창호) + ResNet(유형 분류)     → ONNX
#       - M4: U-Net(열화상 세그멘테이션) + RGB Context → ONNX
#       - M5+G1: YOLO-seg(프레임) + 기하학 분석       → ONNX
#       - M6: PatchCore(앙상블 폴백)                   → ONNX
#
# 기존 inference_pipeline.py(3-모델)와 병존.
# config.USE_20DEFECT_PIPELINE=True 시 이 파이프라인 활성화.
# =============================================

from __future__ import annotations

import asyncio
import os
from typing import List, Optional

import numpy as np

from app.config import settings
from app.schemas.detection import (
    AlignmentDetection,
    DefectDetection,
    DetectionResult20,
    ImageShape,
    InsulationDetection,
    ModelsLoadedStatus20,
)
from app.services.alignment_detector import alignment_detector
from app.services.defect_taxonomy import get_20defect_info
from app.services.ensemble import cross_model_nms, ensemble_with_patchcore
from app.services.insulation_detector import insulation_detector
from app.services.onnx_inference import (
    ONNXPatchCoreDetector,
    ONNXResNetClassifier,
    ONNXYoloDetector,
    crop_roi,
)


class InferencePipeline20:
    """
    20종 하자 6-Model + Geometric 통합 추론 오케스트레이터.
    서버 전역 단 하나의 싱글톤.
    """

    def __init__(self):
        # M1: 구조·방수 (2-Stage)
        self._m1_yolo: Optional[ONNXYoloDetector] = None
        self._m1_resnet: Optional[ONNXResNetClassifier] = None

        # M2: 마감·표면 (2-Stage)
        self._m2_yolo: Optional[ONNXYoloDetector] = None
        self._m2_resnet: Optional[ONNXResNetClassifier] = None

        # M3: 바닥·창호 (2-Stage)
        self._m3_yolo: Optional[ONNXYoloDetector] = None
        self._m3_resnet: Optional[ONNXResNetClassifier] = None

        # M6: PatchCore
        self._m6_patchcore: Optional[ONNXPatchCoreDetector] = None

        self._loaded = False

    # ── 상태 조회 ────────────────────────────
    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def models_loaded(self) -> ModelsLoadedStatus20:
        return ModelsLoadedStatus20(
            m1_yolo=self._m1_yolo is not None,
            m1_resnet=self._m1_resnet is not None,
            m2_yolo=self._m2_yolo is not None,
            m2_resnet=self._m2_resnet is not None,
            m3_yolo=self._m3_yolo is not None,
            m3_resnet=self._m3_resnet is not None,
            m4_unet=insulation_detector.is_loaded,
            m4_context=False,
            m5_seg=alignment_detector.is_loaded,
            m6_patchcore=self._m6_patchcore is not None,
        )

    # ── 모델 로드 ────────────────────────────
    def load_models(self) -> None:
        """전체 모델 로드. 가용한 모델만 로드 (graceful degradation)."""
        if self._loaded:
            print("[Pipeline20] 이미 로드됨 — 스킵")
            return

        wd = settings.AEROINSPECT_WEIGHTS_DIR

        # M1: 구조·방수
        self._m1_yolo = self._try_load_yolo(
            wd, settings.M1_YOLO_ONNX, ["crack", "caulking_defect", "waterproof_defect"], "M1-YOLO",
        )
        self._m1_resnet = self._try_load_resnet(
            wd, settings.M1_RESNET_ONNX, ["crack_structural", "crack_finishing"], "M1-ResNet",
        )

        # M2: 마감·표면
        self._m2_yolo = self._try_load_yolo(
            wd, settings.M2_YOLO_ONNX, ["surface_defect_wall", "baseboard_defect"], "M2-YOLO",
        )
        self._m2_resnet = self._try_load_resnet(
            wd, settings.M2_RESNET_ONNX,
            ["wallpaper_seam", "wallpaper_bubble", "paint_stain", "scratch", "baseboard_damage"],
            "M2-ResNet",
        )

        # M3: 바닥·창호
        self._m3_yolo = self._try_load_yolo(
            wd, settings.M3_YOLO_ONNX, ["floor_defect", "glass_defect", "frame_defect"], "M3-YOLO",
        )
        self._m3_resnet = self._try_load_resnet(
            wd, settings.M3_RESNET_ONNX,
            ["floor_stain", "grout_defect", "glass_scratch", "frame_paint_defect"],
            "M3-ResNet",
        )

        # M4: 열화상
        insulation_detector.load_models()

        # M5+G1: 기하학
        alignment_detector.load_models()

        # M6: PatchCore
        pc_path = os.path.join(wd, settings.M6_PATCHCORE_ONNX)
        if os.path.exists(pc_path):
            self._m6_patchcore = ONNXPatchCoreDetector(pc_path, settings.PATCHCORE_THRESHOLD)
            print(f"[M6-PatchCore] 로드 완료: {pc_path}")

        self._loaded = True
        loaded_count = sum([
            self._m1_yolo is not None, self._m1_resnet is not None,
            self._m2_yolo is not None, self._m2_resnet is not None,
            self._m3_yolo is not None, self._m3_resnet is not None,
            insulation_detector.is_loaded, alignment_detector.is_loaded,
            self._m6_patchcore is not None,
        ])
        print(f"[Pipeline20] 모델 로드 완료: {loaded_count}/9 가용")

    # ── 메인 추론 ────────────────────────────
    def detect(
        self,
        frame_bgr: np.ndarray,
        thermal_map: Optional[np.ndarray] = None,
        imu_data: Optional[dict] = None,
        tier: int = 1,
    ) -> DetectionResult20:
        """
        통합 추론. tier로 계층적 실행 제어.

        Args:
            frame_bgr: RGB 카메라 프레임 (BGR)
            thermal_map: 열화상 온도맵 float32 [H,W] °C (선택)
            imu_data: 드론 IMU {roll, pitch, yaw} (선택)
            tier: 실행 계층 (1=M1+M2, 2=+M3+M5, 3=+M4+M6)
        """
        h, w = frame_bgr.shape[:2]
        all_dets: List[dict] = []
        insulation_results: List[InsulationDetection] = []
        alignment_results: List[AlignmentDetection] = []
        anomaly_score: Optional[float] = None

        # ── Tier 1: 구조·방수 + 마감·표면 ──
        if tier >= 1:
            all_dets.extend(self._run_m1(frame_bgr))
            all_dets.extend(self._run_m2(frame_bgr))

        # ── Tier 2: 바닥·창호 + 기하학 ──
        if tier >= 2:
            all_dets.extend(self._run_m3(frame_bgr))
            if alignment_detector.is_loaded:
                raw = alignment_detector.detect(frame_bgr, imu_data)
                for r in raw:
                    alignment_results.append(AlignmentDetection(**{
                        "class": r["class"], "code": r["code"],
                        "display_ko": r["display_ko"], "conf": r["conf"],
                        "bbox_xyxy": r["bbox_xyxy"],
                        "deviation_degrees": r["deviation_degrees"],
                        "deviation_mm_per_m": r["deviation_mm_per_m"],
                        "direction": r["direction"], "severity": r["severity"],
                    }))

        # ── Tier 3: 열화상 + PatchCore ──
        if tier >= 3:
            if insulation_detector.is_loaded and thermal_map is not None:
                raw = insulation_detector.detect(frame_bgr, thermal_map)
                for r in raw:
                    insulation_results.append(InsulationDetection(**{
                        "class": r["class"], "code": r["code"],
                        "display_ko": r["display_ko"], "conf": r["conf"],
                        "bbox_xyxy": r["bbox_xyxy"],
                        "delta_temperature": r["delta_temperature"],
                        "max_temperature": r["max_temperature"],
                        "min_temperature": r["min_temperature"],
                        "severity": r["severity"],
                    }))

            if self._m6_patchcore:
                mask, score = self._m6_patchcore.detect(frame_bgr)
                anomaly_score = score
                all_dets = ensemble_with_patchcore(all_dets, mask, score)

        # ── Cross-Model NMS ──
        all_dets = cross_model_nms(all_dets)

        # ── severity_mapper 매핑 ──
        defect_detections: List[DefectDetection] = []
        for det in all_dets:
            code, display_ko, severity, area = get_20defect_info(det["class"])
            defect_detections.append(DefectDetection(**{
                "class": det["class"],
                "class_display_en": det["class"].replace("_", " ").title(),
                "class_display_ko": display_ko,
                "code": code,
                "conf": det["conf"],
                "bbox_xyxy": det.get("bbox_xyxy", []),
                "severity": det.get("severity") or severity,
                "defect_source": det.get("defect_source", ""),
                "ensemble_boosted": det.get("ensemble_boosted", False),
            }))

        defect_count = len(defect_detections) + len(insulation_results) + len(alignment_results)
        has_defect = defect_count > 0

        return DetectionResult20(
            detections=defect_detections,
            insulation=insulation_results,
            alignment=alignment_results,
            anomaly_score=anomaly_score,
            has_defect=has_defect,
            defect_count=defect_count,
            image_shape=ImageShape(width=w, height=h),
            tier_executed=tier,
        )

    async def detect_async(
        self,
        frame_bgr: np.ndarray,
        thermal_map: Optional[np.ndarray] = None,
        imu_data: Optional[dict] = None,
        tier: int = 1,
    ) -> DetectionResult20:
        """비동기 래퍼."""
        return await asyncio.to_thread(self.detect, frame_bgr, thermal_map, imu_data, tier)

    # ── 2-Stage 실행 (YOLO → ResNet) ─────────
    def _run_m1(self, frame_bgr: np.ndarray) -> List[dict]:
        """M1: 구조·방수 — crack→ResNet 분류."""
        if self._m1_yolo is None:
            return []

        dets = self._m1_yolo.predict(frame_bgr, conf=settings.M1_CONF_THRESHOLD)
        for det in dets:
            det["defect_source"] = "yolo_structural"
            if det["class"] == "crack" and self._m1_resnet:
                roi = crop_roi(frame_bgr, det["bbox_xyxy"])
                crack_type, crack_conf, _ = self._m1_resnet.classify(roi)
                det["class"] = crack_type
                det["conf"] = det["conf"] * crack_conf
        return dets

    def _run_m2(self, frame_bgr: np.ndarray) -> List[dict]:
        """M2: 마감·표면 — surface_defect→ResNet 분류."""
        if self._m2_yolo is None:
            return []

        dets = self._m2_yolo.predict(frame_bgr, conf=settings.M2_CONF_THRESHOLD)
        for det in dets:
            det["defect_source"] = "yolo_surface"
            if det["class"] == "surface_defect_wall" and self._m2_resnet:
                roi = crop_roi(frame_bgr, det["bbox_xyxy"])
                surface_type, surface_conf, _ = self._m2_resnet.classify(roi)
                det["class"] = surface_type
                det["conf"] = det["conf"] * surface_conf
            elif det["class"] == "baseboard_defect":
                det["class"] = "baseboard_damage"
        return dets

    def _run_m3(self, frame_bgr: np.ndarray) -> List[dict]:
        """M3: 바닥·창호 — floor/glass/frame→ResNet 분류."""
        if self._m3_yolo is None:
            return []

        dets = self._m3_yolo.predict(frame_bgr, conf=settings.M3_CONF_THRESHOLD)
        for det in dets:
            det["defect_source"] = "yolo_floor_window"
            if self._m3_resnet and det["class"] in ("floor_defect", "glass_defect", "frame_defect"):
                roi = crop_roi(frame_bgr, det["bbox_xyxy"])
                sub_type, sub_conf, _ = self._m3_resnet.classify(roi)
                det["class"] = sub_type
                det["conf"] = det["conf"] * sub_conf
        return dets

    # ── 모델 로드 헬퍼 ────────────────────────
    @staticmethod
    def _try_load_yolo(
        weights_dir: str, filename: str, class_names: List[str], label: str,
    ) -> Optional[ONNXYoloDetector]:
        path = os.path.join(weights_dir, filename)
        if not os.path.exists(path):
            print(f"[{label}] 경고: {path} 없음 — 스킵")
            return None
        detector = ONNXYoloDetector(path, class_names)
        print(f"[{label}] 로드 완료: {path}")
        return detector

    @staticmethod
    def _try_load_resnet(
        weights_dir: str, filename: str, class_names: List[str], label: str,
    ) -> Optional[ONNXResNetClassifier]:
        path = os.path.join(weights_dir, filename)
        if not os.path.exists(path):
            print(f"[{label}] 경고: {path} 없음 — 스킵")
            return None
        classifier = ONNXResNetClassifier(path, class_names)
        print(f"[{label}] 로드 완료: {path}")
        return classifier


# ── 모듈 레벨 싱글톤 ─────────────────────────
pipeline20 = InferencePipeline20()


# ── 공개 API ────────────────────────────────��
def load_models_20() -> None:
    pipeline20.load_models()


def detect_20(
    frame_bgr: np.ndarray,
    thermal_map: Optional[np.ndarray] = None,
    imu_data: Optional[dict] = None,
    tier: int = 1,
) -> DetectionResult20:
    return pipeline20.detect(frame_bgr, thermal_map, imu_data, tier)


async def detect_20_async(
    frame_bgr: np.ndarray,
    thermal_map: Optional[np.ndarray] = None,
    imu_data: Optional[dict] = None,
    tier: int = 1,
) -> DetectionResult20:
    return await pipeline20.detect_async(frame_bgr, thermal_map, imu_data, tier)
