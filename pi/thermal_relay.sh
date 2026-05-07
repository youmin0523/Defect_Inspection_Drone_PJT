#!/usr/bin/env bash
# =============================================
# pi/thermal_relay.sh
# 역할: IRC-256CA USB 열화상 카메라 → 백엔드 RTSP 송출
#       Pi Zero 2 W 단일 ffmpeg 프로세스. CPU 인코딩이 무거우면
#       하드웨어 인코더(h264_v4l2m2m)로 전환.
#
# 환경변수:
#   AEROINSPECT_THERMAL_DEV   /dev/video0
#   AEROINSPECT_RTSP_OUT      rtsp://192.168.1.10:8554/thermal
#   AEROINSPECT_THERMAL_SIZE  256x192 (IRC-256CA 기본)
#   AEROINSPECT_THERMAL_FPS   25
# =============================================
set -euo pipefail

DEV="${AEROINSPECT_THERMAL_DEV:-/dev/video0}"
OUT="${AEROINSPECT_RTSP_OUT:-rtsp://192.168.1.10:8554/thermal}"
SIZE="${AEROINSPECT_THERMAL_SIZE:-256x192}"
FPS="${AEROINSPECT_THERMAL_FPS:-25}"

# h264_v4l2m2m: Pi 의 하드웨어 H.264 인코더. 지원되지 않으면 libx264 ultrafast 로 폴백.
if ffmpeg -encoders 2>/dev/null | grep -q "h264_v4l2m2m"; then
  ENCODER="-c:v h264_v4l2m2m -b:v 1500k"
else
  ENCODER="-c:v libx264 -preset ultrafast -tune zerolatency -b:v 1200k"
fi

exec ffmpeg -hide_banner -loglevel warning \
  -f v4l2 -framerate "$FPS" -video_size "$SIZE" -i "$DEV" \
  $ENCODER -pix_fmt yuv420p -g $((FPS*2)) \
  -f rtsp -rtsp_transport tcp "$OUT"
