# =============================================
# app/services/yolo_inference.py
# 역할: YOLOv8 기반 하자 탐지 추론 서비스
#       - 모델을 시작 시 한 번만 로드 (per-request 로드 금지)
#       - asyncio.to_thread로 블로킹 추론을 비동기 래핑
#       - 20종 하자 클래스를 severity_mapper를 통해 심각도 분류
#       - 가중치 파일 없을 시 더미 결과 반환 (개발 편의)
#
# 학습 데이터:
#   CrackForest (균열), DAGM (표면 결함), Roboflow 건설 하자 데이터셋
#   Fine-tuning: COCO 사전학습 → 건설 하자 도메인 Transfer Learning
# =============================================

import asyncio
import os
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from app.config import settings
from app.utils.severity_mapper import get_severity_by_code, DEFECT_CLASS_NAMES


@dataclass
class DetectionResult:
    """YOLOv8 탐지 결과 단건"""
    class_id: int
    class_name: str          # 예: "crack_structural"
    category_code: str       # 예: "A-02"
    defect_type: str         # 예: "균열 (구조 균열)"
    area: str                # 예: "A"
    severity: str            # HIGH / MED / LOW
    confidence: float        # 0.0 ~ 1.0
    bbox_x: float            # 바운딩 박스 중심 X (정규화)
    bbox_y: float            # 바운딩 박스 중심 Y (정규화)
    bbox_w: float            # 바운딩 박스 너비 (정규화)
    bbox_h: float            # 바운딩 박스 높이 (정규화)
    raw: Optional[dict] = None  # 원시 YOLO 출력


class YOLOInferenceService:
    """
    YOLOv8 추론 서비스 싱글톤.
    애플리케이션 시작 시 모델 로드, 이후 비동기 추론 제공.
    """

    def __init__(self):
        self._model = None
        self._conf_threshold = settings.YOLO_CONF_THRESHOLD
        self._weights_path = settings.YOLO_WEIGHTS_PATH

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load_model(self) -> None:
        """
        YOLOv8 모델 로드.
        가중치 파일이 없으면 경고만 출력하고 계속 (더미 추론 사용).
        """
        if not os.path.exists(self._weights_path):
            print(f"[YOLO] 경고: 가중치 파일 없음 ({self._weights_path}). 더미 모드로 실행.")
            return
        try:
            from ultralytics import YOLO
            self._model = YOLO(self._weights_path)
            print(f"[YOLO] 모델 로드 완료: {self._weights_path}")
        except Exception as e:
            print(f"[YOLO] 모델 로드 실패: {e}. 더미 모드로 실행.")

    async def infer(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        단일 프레임에 대한 비동기 하자 탐지 추론.

        Args:
            frame: BGR 형식 numpy 배열

        Returns:
            탐지된 하자 목록 (없으면 빈 리스트)
        """
        if self._model is None:
            return []  # 더미 모드: 빈 결과 반환

        # 블로킹 추론을 스레드 풀에서 실행
        results = await asyncio.to_thread(
            self._model.predict,
            frame,
            conf=self._conf_threshold,
            verbose=False,
        )

        return self._parse_results(results[0] if results else None)

    def _parse_results(self, result) -> List[DetectionResult]:
        """YOLO 결과를 DetectionResult 목록으로 변환"""
        if result is None or result.boxes is None:
            return []

        detections = []
        for box in result.boxes:
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())

            if confidence < self._conf_threshold:
                continue

            # 클래스 ID → 하자 정보 매핑
            class_name = DEFECT_CLASS_NAMES.get(class_id, f"unknown_{class_id}")
            meta = get_severity_by_code(class_name)

            # 바운딩 박스 (xywhn: 정규화 중심 좌표)
            xywhn = box.xywhn[0].tolist()

            detections.append(DetectionResult(
                class_id=class_id,
                class_name=class_name,
                category_code=meta.get("code", "X-00"),
                defect_type=meta.get("name", "알 수 없음"),
                area=meta.get("area", "A"),
                severity=meta.get("severity", "MED"),
                confidence=confidence,
                bbox_x=xywhn[0],
                bbox_y=xywhn[1],
                bbox_w=xywhn[2],
                bbox_h=xywhn[3],
                raw={
                    "class_id": class_id,
                    "conf": confidence,
                    "bbox": xywhn,
                },
            ))

        return detections


# 모듈 레벨 싱글톤
yolo_service = YOLOInferenceService()
