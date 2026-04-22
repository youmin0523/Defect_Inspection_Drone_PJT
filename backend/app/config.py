# =============================================
# app/config.py
# 역할: 애플리케이션 환경변수 설정 관리
#       pydantic-settings를 사용해 .env 파일에서 값을 로드하고
#       타입 검증 후 전역 settings 객체로 제공한다.
# 사용: from app.config import settings
# =============================================

from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
import json
from typing import List


class Settings(BaseSettings):
    # ── Database (개별 변수 → DATABASE_URL 자동 조립) ──
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "aeroinspect"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "aeroinspect_db"
    DATABASE_URL: str = ""

    @model_validator(mode="after")
    def assemble_database_url(self):
        """개별 DB 환경변수로부터 DATABASE_URL을 자동 조립한다."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        return self

    # ── Camera ───────────────────────────────
    RGB_CAMERA_INDEX: int = 0
    THERMAL_CAMERA_INDEX: int = 1

    # ── LiDAR ────────────────────────────────
    LIDAR_SERIAL_PORT: str = "COM3"
    LIDAR_BAUD_RATE: int = 115200

    # ── AI Model (3-모델 파이프라인) ──────────
    # 가중치 디렉토리 + 개별 파일명 분리 → 배포 환경별로 경로만 바꾸면 됨
    AEROINSPECT_WEIGHTS_DIR: str = "./models_weights"
    YOLO_THERMAL_WEIGHTS: str = "yolov8s_crack_moisture_best.pt"
    YOLO_DELAM_WEIGHTS: str = "yolov8s_delamination_best.pt"
    WALLPAPER_WEIGHTS: str = "resnet50_wallpaper_best.pt"

    # YOLO 공통 신뢰도 임계값 (crack_moisture + delamination)
    YOLO_CONF_THRESHOLD: float = 0.25
    # ResNet50 벽지 분류 신뢰도 임계값 (val_acc 54% 감안, top1 최소 신뢰도)
    WALLPAPER_CONF_THRESHOLD: float = 0.35
    # top1 - top2 최소 마진. 모호한 예측(top1/top2 근소차) 차단용
    WALLPAPER_MARGIN_THRESHOLD: float = 0.15

    # WebSocket 스트림 추론 — N프레임 중 1프레임만 추론 (GPU 부하 분산)
    FRAME_SKIP: int = 3

    # 추론 디바이스: 'auto' | 'cuda' | 'cpu'
    DEVICE: str = "auto"

    # 로깅 — JSON 출력은 운영 권장, 개발은 컬러 콘솔
    LOG_JSON: bool = False
    LOG_LEVEL: str = "INFO"

    # ── 20종 하자 검출 ONNX 파이프라인 (6-Model + Geometric) ──
    # M1: 구조·방수 (2-Stage YOLO→ResNet)
    M1_YOLO_ONNX: str = "m1_yolo_structural.onnx"
    M1_RESNET_ONNX: str = "m1_resnet_crack_classifier.onnx"
    M1_CONF_THRESHOLD: float = 0.15          # 높은 재현율 (구조 하자 놓치면 안 됨)

    # M2: 마감·표면 (2-Stage YOLO→ResNet)
    M2_YOLO_ONNX: str = "m2_yolo_surface.onnx"
    M2_RESNET_ONNX: str = "m2_resnet_surface_classifier.onnx"
    M2_CONF_THRESHOLD: float = 0.20

    # M3: 바닥·창호 (2-Stage YOLO→ResNet)
    M3_YOLO_ONNX: str = "m3_yolo_floor_window.onnx"
    M3_RESNET_ONNX: str = "m3_resnet_floor_window_classifier.onnx"
    M3_CONF_THRESHOLD: float = 0.20

    # M4: 열화상 단열 (U-Net + RGB Context)
    M4_UNET_ONNX: str = "m4_unet_thermal_insulation.onnx"
    M4_CONTEXT_ONNX: str = "m4_yolo_context_elements.onnx"
    M4_INSULATION_WALL_DELTA: float = 3.5    # 벽체 단열 온도차 임계값 (°C)
    M4_INSULATION_WINDOW_DELTA: float = 2.0  # 창호 단열 온도차 임계값 (°C)
    M4_AIRTIGHT_DELTA: float = 1.5           # 기밀 불량 온도차 임계값 (°C)
    M4_FLOOR_HEATING_DELTA: float = 2.0      # 바닥 난방 편차 임계값 (°C)

    # M5+G1: 기하학 (YOLOv8m-seg + Hough/RANSAC)
    M5_SEG_ONNX: str = "m5_yolo_seg_frames.onnx"
    ALIGNMENT_ANGLE_THRESHOLD: float = 0.2   # 수직수평 편차 임계값 (도)
    SQUARENESS_ANGLE_THRESHOLD: float = 0.3  # 직각도 편차 임계값 (도)

    # M6: PatchCore 앙상블 폴백
    M6_PATCHCORE_ONNX: str = "m6_patchcore_surface.onnx"
    PATCHCORE_THRESHOLD: float = 0.5         # 이상 점수 임계값
    PATCHCORE_ENSEMBLE_BOOST: float = 0.15   # 앙상블 신뢰도 승격 값

    # 열화상-RGB 공간 정렬 Homography (3x3 JSON)
    THERMAL_RGB_HOMOGRAPHY: str = "thermal_rgb_homography.json"

    # 계층적 실행 설정
    TIER1_FRAME_SKIP: int = 3                # M1+M2 실행 주기
    TIER2_FRAME_SKIP: int = 6                # M3+M5 실행 주기
    TIER3_FRAME_SKIP: int = 9                # M4+M6 실행 주기

    # 시간 일관성 필터
    TEMPORAL_FILTER_WINDOW: int = 5          # 프레임 윈도우 크기
    TEMPORAL_FILTER_MIN_DETECTIONS: int = 2  # 최소 검출 횟수
    TEMPORAL_INSTANT_THRESHOLD: float = 0.85 # 즉시 보고 임계값

    # 신규 파이프라인 활성화 플래그 (기존 파이프라인과 전환용)
    USE_20DEFECT_PIPELINE: bool = False

    # ── Legacy (하위 호환용, 신규 코드에선 사용 금지) ──
    YOLO_WEIGHTS_PATH: str = "./models_weights/aeroinspect_yolov8.pt"

    # ── LLM ──────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # ── JWT ──────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_MINUTES: int = 120
    # Refresh token: 장기 유효 (기본 14일). /auth/refresh 엔드포인트로 access token 재발급용.
    JWT_REFRESH_EXPIRE_DAYS: int = 14

    # 푸시 알림 프로바이더: "noop" | "fcm" | "apns"
    # 운영 배포 시 firebase-admin 설치 후 "fcm" 으로 전환.
    PUSH_PROVIDER: str = "noop"

    # WebSocket 브로드캐스트 백엔드: "memory" (단일 워커) | "redis" (수평 확장)
    # redis 선택 시 REDIS_URL 필수.
    WS_BACKEND: str = "memory"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── OAuth (SNS 로그인) ────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    KAKAO_CLIENT_ID: str = ""
    KAKAO_CLIENT_SECRET: str = ""
    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_BASE: str = "http://localhost:5173"

    # ── WebSocket ────────────────────────────
    WS_HEARTBEAT_INTERVAL: int = 30

    # ── Streaming ────────────────────────────
    MJPEG_JPEG_QUALITY: int = 80
    THERMAL_BLEND_ALPHA: float = 0.5

    # ── Recording ────────────────────────────
    RECORDING_OUTPUT_DIR: str = "./recordings"
    RECORDING_FPS: float = 30.0
    RECORDING_CODEC: str = "mp4v"

    # ── Email (SMTP) ─────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@droneinspect.com"
    SMTP_FROM_NAME: str = "DRONE INSPECT"

    # ── CORS ─────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 전역 싱글톤: 애플리케이션 전체에서 공유
settings = Settings()
