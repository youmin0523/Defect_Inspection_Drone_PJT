# =============================================
# app/services/camera.py
# 역할: 카메라 캡처 서비스 (RGB 및 열화상 공통 사용)
#       - cv2.VideoCapture를 asyncio.to_thread로 비동기 래핑
#       - 구독자별 asyncio.Queue를 유지하여 다중 MJPEG 클라이언트 팬아웃
#       - 큐가 꽉 차면 오래된 프레임 드롭 (실시간성 유지)
#       - 열화상 카메라는 ThermalService에서 추가 처리 후 사용
#
# 사용:
#   rgb_camera_service   → RGB USB Capture Card (index=0)
#   thermal_camera_service → IRC-256CA (index=1, 의사색상 처리는 thermal.py에서)
# =============================================

import asyncio
from typing import Optional

import cv2
import numpy as np

from app.config import settings


class CameraService:
    """
    단일 카메라 비동기 캡처 서비스.
    여러 소비자(MJPEG 스트림 클라이언트)에게 프레임을 팬아웃한다.
    """

    def __init__(self, camera_index: int, name: str = "camera"):
        self._index = camera_index
        self._name = name
        self._cap: Optional[cv2.VideoCapture] = None
        self._subscribers: list[asyncio.Queue] = []
        self._capture_task: Optional[asyncio.Task] = None
        self._running = False

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    async def open(self) -> None:
        """카메라 장치 열기 및 캡처 루프 시작"""
        self._cap = await asyncio.to_thread(cv2.VideoCapture, self._index)
        if not self._cap.isOpened():
            print(f"[Camera:{self._name}] 경고: 카메라 index={self._index} 열기 실패. 더미 프레임 사용.")
        self._running = True
        # 백그라운드 캡처 태스크 시작
        self._capture_task = asyncio.create_task(self._capture_loop())

    async def release(self) -> None:
        """카메라 자원 해제"""
        self._running = False
        if self._capture_task:
            self._capture_task.cancel()
        if self._cap:
            await asyncio.to_thread(self._cap.release)
        print(f"[Camera:{self._name}] 자원 해제 완료")

    async def _capture_loop(self) -> None:
        """
        백그라운드 프레임 캡처 루프.
        새 프레임을 모든 구독자 큐에 팬아웃.
        카메라가 없으면 더미 프레임(검정 화면) 사용.
        """
        while self._running:
            if self._cap and self._cap.isOpened():
                ret, frame = await asyncio.to_thread(self._cap.read)
                if not ret:
                    frame = self._dummy_frame()
            else:
                frame = self._dummy_frame()
                await asyncio.sleep(0.033)  # 30fps

            # 모든 구독자에게 팬아웃
            for q in list(self._subscribers):
                if q.full():
                    try:
                        q.get_nowait()  # 오래된 프레임 버리기
                    except asyncio.QueueEmpty:
                        pass
                try:
                    q.put_nowait(frame)
                except asyncio.QueueFull:
                    pass

            await asyncio.sleep(0)  # 이벤트 루프 제어권 반환

    def subscribe(self) -> asyncio.Queue:
        """새 구독자 큐 생성 및 등록"""
        q: asyncio.Queue = asyncio.Queue(maxsize=2)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        """구독자 큐 제거"""
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def get_single_frame(self) -> Optional[np.ndarray]:
        """
        단일 프레임 즉시 획득 (스트리밍이 아닌 스냅샷용).
        구독 없이 직접 캡처.
        """
        if self._cap and self._cap.isOpened():
            ret, frame = await asyncio.to_thread(self._cap.read)
            return frame if ret else self._dummy_frame()
        return self._dummy_frame()

    @staticmethod
    def _dummy_frame(width: int = 640, height: int = 480) -> np.ndarray:
        """
        카메라 미연결 시 표시할 더미 프레임.
        검정 배경에 "No Signal" 텍스트 표시.
        """
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.putText(
            frame, "No Signal",
            (width // 2 - 80, height // 2),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2,
        )
        return frame


# ── 모듈 레벨 싱글톤 ─────────────────────────
# main.py lifespan에서 open/release 호출
rgb_camera_service = CameraService(
    camera_index=settings.RGB_CAMERA_INDEX,
    name="RGB"
)

thermal_camera_service = CameraService(
    camera_index=settings.THERMAL_CAMERA_INDEX,
    name="Thermal"
)
