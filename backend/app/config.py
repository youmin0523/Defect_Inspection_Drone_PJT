# =============================================
# app/config.py
# 역할: 애플리케이션 환경변수 설정 관리
#       pydantic-settings를 사용해 .env 파일에서 값을 로드하고
#       타입 검증 후 전역 settings 객체로 제공한다.
# 사용: from app.config import settings
# =============================================

from pydantic_settings import BaseSettings
from pydantic import field_validator
import json
from typing import List


class Settings(BaseSettings):
    # ── Database ─────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://aeroinspect:password@localhost:5432/aeroinspect_db"

    # ── Camera ───────────────────────────────
    RGB_CAMERA_INDEX: int = 0
    THERMAL_CAMERA_INDEX: int = 1

    # ── LiDAR ────────────────────────────────
    LIDAR_SERIAL_PORT: str = "COM3"
    LIDAR_BAUD_RATE: int = 115200

    # ── AI Model ─────────────────────────────
    YOLO_WEIGHTS_PATH: str = "./models_weights/aeroinspect_yolov8.pt"
    YOLO_CONF_THRESHOLD: float = 0.45

    # ── LLM ──────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # ── WebSocket ────────────────────────────
    WS_HEARTBEAT_INTERVAL: int = 30

    # ── Streaming ────────────────────────────
    MJPEG_JPEG_QUALITY: int = 80
    THERMAL_BLEND_ALPHA: float = 0.5

    # ── Recording ────────────────────────────
    RECORDING_OUTPUT_DIR: str = "./recordings"
    RECORDING_FPS: float = 30.0
    RECORDING_CODEC: str = "mp4v"

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
