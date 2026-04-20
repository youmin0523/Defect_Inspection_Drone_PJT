# =============================================
# app/core/stream_inference.py
# 역할: WebSocket 실시간 스트림 추론 워커 (드롭 큐 + 프레임 스킵)
#       - asyncio.Queue(maxsize=1) — 최신 프레임 1개만 유지
#       - put_nowait 실패 시 그냥 드롭 (추론 워커가 바쁠 때)
#       - FRAME_SKIP: N프레임 중 1프레임만 추론
#       - 추론은 asyncio.to_thread(pipeline.detect) — 이벤트 루프 블로킹 방지
#       - 결과는 "stream" + "defects" 두 채널에 broadcast
#       - 별도 태스크로 영구 실행 (main.py lifespan에서 start/stop)
#
# 드론 IRC-256CA 스트림(15~30fps) + T4 GPU 추론(80~150ms/frame) 환경에서
# 모든 프레임을 처리 못 하므로 드롭 큐 패턴이 필수.
# =============================================

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from app.config import settings
from app.core.ws_manager import ws_manager
from app.services.defect_taxonomy import map_to_legacy, xyxy_to_xywhn
from app.services.inference_pipeline import pipeline


@dataclass
class QueuedFrame:
    """큐에 들어갈 단일 프레임."""
    frame_bgr: np.ndarray
    frame_id: int
    submitted_at: float  # epoch seconds


class StreamInferenceWorker:
    """
    WebSocket 프레임 → 추론 → 브로드캐스트 파이프라인.
    싱글톤. main.py lifespan에서 start()/stop() 호출.
    """

    def __init__(self):
        # 최신 프레임 1개만 유지 (maxsize=1)
        self._queue: asyncio.Queue[QueuedFrame] = asyncio.Queue(maxsize=1)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._submitted_count = 0
        self._processed_count = 0
        self._dropped_count = 0
        # FRAME_SKIP은 submit 단계에서 적용 (워커는 큐에서 꺼낸 건 무조건 처리)
        self._frame_skip: int = 3

    # ── 상태 조회 ────────────────────────────────
    @property
    def is_running(self) -> bool:
        return self._running and self._worker_task is not None and not self._worker_task.done()

    @property
    def stats(self) -> dict:
        return {
            "submitted": self._submitted_count,
            "processed": self._processed_count,
            "dropped": self._dropped_count,
            "queue_size": self._queue.qsize(),
            "frame_skip": self._frame_skip,
        }

    # ── 생명주기 ─────────────────────────────────
    async def start(self) -> None:
        """워커 태스크 시작 (이벤트 루프 내에서 호출)."""
        if self.is_running:
            return
        self._frame_skip = max(1, int(settings.FRAME_SKIP))
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop(), name="stream_inference_worker")
        print(f"[StreamInfer] 워커 시작 (frame_skip={self._frame_skip})")

    async def stop(self) -> None:
        """워커 태스크 종료."""
        self._running = False
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except (asyncio.CancelledError, Exception):
                pass
            self._worker_task = None
        print("[StreamInfer] 워커 종료")

    # ── 프레임 제출 ─────────────────────────────
    def submit(self, frame_bgr: np.ndarray) -> bool:
        """
        수신자(ws_stream.py)가 호출. 프레임 스킵 적용 + 드롭 큐에 put.

        Returns:
            True: 큐에 enqueue됨 (추론 예정)
            False: 스킵됐거나 드롭됨
        """
        self._submitted_count += 1

        # 프레임 스킵 — N프레임 중 1프레임만 추론
        if self._submitted_count % self._frame_skip != 0:
            return False

        item = QueuedFrame(
            frame_bgr=frame_bgr,
            frame_id=self._submitted_count,
            submitted_at=time.time(),
        )
        try:
            self._queue.put_nowait(item)
            return True
        except asyncio.QueueFull:
            # 워커가 바쁨 — 그냥 드롭
            self._dropped_count += 1
            return False

    # ── 워커 루프 ───────────────────────────────
    async def _worker_loop(self) -> None:
        """큐에서 하나 꺼내 추론 → 브로드캐스트 반복."""
        while self._running:
            try:
                item = await self._queue.get()
            except asyncio.CancelledError:
                break

            try:
                await self._process(item)
            except Exception as e:
                print(f"[StreamInfer] 추론 오류 (frame_id={item.frame_id}): {e}")
            finally:
                self._processed_count += 1

    async def _process(self, item: QueuedFrame) -> None:
        """단일 프레임 추론 + 양방향 브로드캐스트."""
        if not pipeline.is_loaded:
            return

        # 블로킹 추론은 스레드 풀로
        result = await asyncio.to_thread(
            pipeline.detect, item.frame_bgr, None, False
        )

        now = time.time()
        payload = {
            "type": "detection",
            "timestamp": now,
            "frame_id": item.frame_id,
            "result": json.loads(result.model_dump_json()),
        }

        # 1) /ws/stream 구독자에게 전송 (stream 채널)
        await ws_manager.broadcast("stream", payload)

        # 2) 기존 /ws?channel=defects 구독자에게도 전송 (호환)
        #    레거시 포맷 최소 필드로 변환
        legacy_events = self._to_legacy_events(result, item)
        for ev in legacy_events:
            await ws_manager.broadcast("defects", ev)

    @staticmethod
    def _to_legacy_events(result, item: QueuedFrame) -> list:
        """신규 DetectionResult → 기존 'defect.new' 이벤트 리스트."""
        events = []
        img_w = result.image_shape.width
        img_h = result.image_shape.height

        def _legacy_bbox(xyxy):
            cx, cy, bw, bh = xyxy_to_xywhn(xyxy, img_w, img_h)
            return {"x": cx, "y": cy, "w": bw, "h": bh}

        for det in result.yolo_thermal:
            area, code, dtype = map_to_legacy("yolo_thermal", det.class_)
            events.append({
                "type": "defect.new",
                "data": {
                    "area": area,
                    "category_code": code,
                    "defect_type": dtype or det.class_display_ko,
                    "severity": "HIGH",
                    "confidence": round(det.conf, 3),
                    "bbox": _legacy_bbox(det.bbox_xyxy),
                    "defect_source": "yolo_thermal",
                    "defect_class": det.class_,
                    "defect_class_display_en": det.class_display_en,
                    "defect_class_display_ko": det.class_display_ko,
                    "frame_id": item.frame_id,
                },
            })
        for det in result.yolo_delam:
            area, code, dtype = map_to_legacy("yolo_delam", det.class_)
            events.append({
                "type": "defect.new",
                "data": {
                    "area": area,
                    "category_code": code,
                    "defect_type": dtype or det.class_display_ko,
                    "severity": "HIGH",
                    "confidence": round(det.conf, 3),
                    "bbox": _legacy_bbox(det.bbox_xyxy),
                    "defect_source": "yolo_delam",
                    "defect_class": det.class_,
                    "defect_class_display_en": det.class_display_en,
                    "defect_class_display_ko": det.class_display_ko,
                    "frame_id": item.frame_id,
                },
            })
        # 벽지는 신뢰 높을 때만 이벤트화
        if result.wallpaper_cls and result.wallpaper_cls.is_confident:
            wc = result.wallpaper_cls
            area, code, dtype = map_to_legacy("wallpaper", wc.top1_class)
            events.append({
                "type": "defect.new",
                "data": {
                    "area": area,
                    "category_code": code,
                    "defect_type": dtype or wc.top1_class_display_ko,
                    "severity": "MED" if result.severity == "MED" else (result.severity or "LOW"),
                    "confidence": round(wc.top1_conf, 3),
                    "bbox": None,
                    "defect_source": "wallpaper",
                    "defect_class": wc.top1_class,
                    "defect_class_display_en": wc.top1_class_display_en,
                    "defect_class_display_ko": wc.top1_class_display_ko,
                    "frame_id": item.frame_id,
                },
            })
        return events


# ── 모듈 레벨 싱글톤 ─────────────────────────
stream_inference_worker = StreamInferenceWorker()


__all__ = ["StreamInferenceWorker", "stream_inference_worker"]
