# =============================================
# app/schemas/detection.py
# 역할: 3-모델 추론 파이프라인 응답 Pydantic 스키마
#       - BBox: xyxy 픽셀 좌표 (API/WS 공통, 프론트 Canvas 렌더용)
#       - YoloDetection: YOLOv8 단건 (thermal / delam 공통 포맷)
#       - WallpaperPrediction: ResNet50 top1 + top3 분류 결과
#       - DetectionResult: detect_defects() 통합 응답
#       - WSStreamMessage: WebSocket 스트림 송수신 메시지
#       - HealthResponse: /health 엔드포인트 응답
# 주의: API 응답은 bbox_xyxy 유지, DB 저장 시에만 xywhn 변환
# =============================================

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Severity = Literal["HIGH", "MED", "LOW"]
DefectSource = Literal["yolo_thermal", "yolo_delam", "wallpaper"]


class BBox(BaseModel):
    """바운딩 박스 — xyxy 픽셀 좌표."""
    x1: float
    y1: float
    x2: float
    y2: float

    def to_list(self) -> List[float]:
        return [self.x1, self.y1, self.x2, self.y2]


class YoloDetection(BaseModel):
    """YOLOv8 탐지 단건 (thermal / delam 동일 포맷)."""
    class_: str = Field(..., alias="class", description="모델 내부 클래스명 (예: 'Crack')")
    class_display_en: str
    class_display_ko: str
    conf: float = Field(..., ge=0.0, le=1.0)
    bbox_xyxy: List[float] = Field(..., min_length=4, max_length=4, description="[x1, y1, x2, y2] 픽셀 좌표")

    model_config = {"populate_by_name": True}


class Top3Prediction(BaseModel):
    """ResNet50 top3 단건."""
    class_: str = Field(..., alias="class")
    class_display_en: str
    class_display_ko: str
    conf: float = Field(..., ge=0.0, le=1.0)

    model_config = {"populate_by_name": True}


class WallpaperPrediction(BaseModel):
    """ResNet50 벽지 분류 결과."""
    top1_class: str = Field(..., description="모델 내부명. ⚠️ 'good'은 실제로 '터짐' 하자임")
    top1_class_display_en: str
    top1_class_display_ko: str
    top1_conf: float = Field(..., ge=0.0, le=1.0)
    is_confident: bool = Field(
        ...,
        description=(
            "(top1_conf >= WALLPAPER_CONF_THRESHOLD) AND "
            "(top1_conf - top2_conf >= WALLPAPER_MARGIN_THRESHOLD). "
            "false면 모호/노이즈로 취급하여 severity 판정 보류."
        )
    )
    top3: List[Top3Prediction] = Field(default_factory=list, max_length=3)


class ImageShape(BaseModel):
    """프레임 크기 (xyxy → xywhn 변환에 필요)."""
    width: int
    height: int


class DetectionResult(BaseModel):
    """
    3-모델 통합 추론 응답.
    inference_pipeline.detect_defects()의 반환 타입과 1:1 매칭.
    """
    yolo_thermal: List[YoloDetection] = Field(default_factory=list)
    yolo_delam: List[YoloDetection] = Field(default_factory=list)
    wallpaper_cls: Optional[WallpaperPrediction] = None
    severity: Optional[Severity] = Field(
        None,
        description="HIGH/MED/LOW. 신뢰도 부족 시 null (판단 보류)"
    )
    has_defect: bool = False
    defect_count: int = 0
    image_shape: ImageShape = Field(
        ...,
        description="프레임 W/H. DB 저장 시 xyxy → xywhn 변환에 사용"
    )


class WSStreamMessage(BaseModel):
    """WebSocket /ws/stream 송신 메시지."""
    type: Literal["detection", "pong", "error"]
    timestamp: float
    frame_id: Optional[int] = None
    result: Optional[DetectionResult] = None
    message: Optional[str] = None


class ModelsLoadedStatus(BaseModel):
    yolo_thermal: bool
    yolo_delam: bool
    wallpaper: bool


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    device: Literal["cuda", "cpu"]
    models_loaded: ModelsLoadedStatus
    wallpaper_classes_count: int
    stream_worker_running: bool
    frame_skip: int
