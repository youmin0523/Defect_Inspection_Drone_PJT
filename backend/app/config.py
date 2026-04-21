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

    # ── Legacy (하위 호환용, 신규 코드에선 사용 금지) ──
    YOLO_WEIGHTS_PATH: str = "./models_weights/aeroinspect_yolov8.pt"

    # ── LLM ──────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # ── JWT ──────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_MINUTES: int = 120

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
