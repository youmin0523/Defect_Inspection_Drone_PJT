"""
services/floorplan_processor.py
역할: 평면도 이미지에서 벽체 라인 + 건물 외곽 윤곽선을 추출하는 OpenCV 파이프라인
      - 벽체(walls): 방향성 모폴로지로 수평/수직 구조 벽만 추출
      - 윤곽(outline): 건물 외곽 경계 다각형 — 창호 갭을 유리 벽으로 채우는 데 사용
      - DB 독립적: 순수 이미지 처리 함수만 제공
"""

import math

import cv2
import numpy as np


def extract_walls_from_bytes(image_bytes: bytes) -> dict:
    """
    이미지 바이트에서 벽체 라인 + 건물 외곽 윤곽선을 추출한다.

    Returns:
        {
            "walls":   [{"x1","y1","x2","y2"}, ...]  — 내·외벽 선분 (정규화 0-1)
            "outline": [{"x","y"}, ...]              — 건물 외곽 다각형 꼭짓점 (정규화 0-1, 닫힘)
            "image_width":  int,
            "image_height": int,
            "wall_count":   int,
        }
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 디코딩할 수 없습니다.")

    h, w = img.shape[:2]

    # ── 1. 전처리: 그레이스케일 + 강한 블러 (텍스처 패턴 제거) ──
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    # ── 2. 엄격한 이진화 — 가장 어두운 요소(벽체)만 ──
    _, binary = cv2.threshold(blurred, 85, 255, cv2.THRESH_BINARY_INV)

    # ── 3. 노이즈 제거 — 텍스트·가구·얇은 선 제거 ──
    noise_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, noise_kernel, iterations=1)

    # ── 4. 방향성 모폴로지: 수평 벽체 구조만 분리 ──
    h_len = max(w // 12, 25)
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_len, 1))
    h_mask = cv2.morphologyEx(clean, cv2.MORPH_OPEN, h_kernel)
    h_mask = cv2.dilate(h_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 5)), iterations=1)

    # ── 5. 방향성 모폴로지: 수직 벽체 구조만 분리 ──
    v_len = max(h // 12, 25)
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_len))
    v_mask = cv2.morphologyEx(clean, cv2.MORPH_OPEN, v_kernel)
    v_mask = cv2.dilate(v_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3)), iterations=1)

    # ── 6. 벽체 마스크 합산 ──
    walls_mask = cv2.bitwise_or(h_mask, v_mask)

    # ── 7. 엣지 + 허프 변환 ──
    edges = cv2.Canny(walls_mask, 50, 150, apertureSize=3)

    min_line_len = int(max(w, h) * 0.07)
    max_line_gap = int(max(w, h) * 0.04)

    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180,
        threshold=80,
        minLineLength=min_line_len,
        maxLineGap=max_line_gap,
    )

    raw_walls = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            raw_walls.append({
                "x1": round(x1 / w, 4), "y1": round(y1 / h, 4),
                "x2": round(x2 / w, 4), "y2": round(y2 / h, 4),
            })

    merged = _merge_nearby_lines(raw_walls, angle_threshold=10, dist_threshold=0.035)

    if len(merged) > 50:
        merged.sort(key=_line_length, reverse=True)
        merged = merged[:50]

    # ── 8. 건물 외곽 윤곽선 (밝은 실내 영역 기반 — 창호 갭 포함 닫힌 경계) ──
    outline = _detect_building_outline(blurred, w, h)

    return {
        "walls": merged,
        "outline": outline,
        "image_width": w,
        "image_height": h,
        "wall_count": len(merged),
    }


def _detect_building_outline(gray_blurred: np.ndarray, w: int, h: int) -> list[dict]:
    """
    밝은 실내 영역을 기반으로 건물 외곽 경계 다각형을 추출한다.
    - 실내 바닥(밝음) vs 외부 배경(어두움)/벽(검정) 을 구분
    - 모폴로지 닫힘으로 방 사이 벽을 메워서 하나의 건물 덩어리 생성
    - 외곽 컨투어 → 단순화 다각형 = 건물 경계 (창호 갭 포함)
    """
    # 실내 영역(밝음) 추출: 어두운 벽/배경과 밝은 바닥 분리
    _, interior = cv2.threshold(gray_blurred, 140, 255, cv2.THRESH_BINARY)

    # 강한 팽창 → 침식: 창문 갭(수십~백 px)을 확실히 닫음
    fill_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    filled = cv2.dilate(interior, fill_kernel, iterations=6)
    filled = cv2.erode(filled, fill_kernel, iterations=6)

    # 추가 닫힘으로 내부 잔여 구멍 채움
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    filled = cv2.morphologyEx(filled, cv2.MORPH_CLOSE, close_kernel, iterations=3)

    # 외곽 컨투어만 추출
    contours, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []

    # 가장 큰 컨투어 = 건물 경계
    outer = max(contours, key=cv2.contourArea)

    # 이미지 면적의 5% 미만이면 노이즈
    if cv2.contourArea(outer) < w * h * 0.05:
        return []

    # 이미지 가장자리와 거의 같은 크기이면(95% 이상) → 배경이 없는 이미지
    if cv2.contourArea(outer) > w * h * 0.95:
        return []

    # 다각형 단순화 — 꼭짓점 최소화
    peri = cv2.arcLength(outer, True)
    epsilon = 0.008 * peri
    approx = cv2.approxPolyDP(outer, epsilon, True)

    return [
        {"x": round(float(pt[0][0]) / w, 4), "y": round(float(pt[0][1]) / h, 4)}
        for pt in approx
    ]


# ── 유틸 함수 ─────────────────────────────────────


def _line_angle(wall: dict) -> float:
    dx = wall["x2"] - wall["x1"]
    dy = wall["y2"] - wall["y1"]
    return math.degrees(math.atan2(dy, dx)) % 180


def _line_length(wall: dict) -> float:
    dx = wall["x2"] - wall["x1"]
    dy = wall["y2"] - wall["y1"]
    return math.sqrt(dx * dx + dy * dy)


def _merge_nearby_lines(
    walls: list,
    angle_threshold: float = 10.0,
    dist_threshold: float = 0.035,
) -> list:
    if not walls:
        return []

    horizontal, vertical, diagonal = [], [], []

    for w in walls:
        angle = _line_angle(w)
        if angle < angle_threshold or angle > (180 - angle_threshold):
            horizontal.append(w)
        elif abs(angle - 90) < angle_threshold:
            vertical.append(w)
        else:
            diagonal.append(w)

    merged = []
    merged.extend(_merge_horizontal(horizontal, dist_threshold))
    merged.extend(_merge_vertical(vertical, dist_threshold))
    merged.extend(diagonal)
    return merged


def _merge_horizontal(lines: list, dist_threshold: float) -> list:
    if not lines:
        return []

    lines.sort(key=lambda l: (l["y1"] + l["y2"]) / 2)
    clusters: list[list] = [[lines[0]]]

    for i in range(1, len(lines)):
        prev_y = sum((l["y1"] + l["y2"]) / 2 for l in clusters[-1]) / len(clusters[-1])
        curr_y = (lines[i]["y1"] + lines[i]["y2"]) / 2
        if abs(curr_y - prev_y) < dist_threshold:
            clusters[-1].append(lines[i])
        else:
            clusters.append([lines[i]])

    result = []
    for cluster in clusters:
        avg_y = round(sum((l["y1"] + l["y2"]) / 2 for l in cluster) / len(cluster), 4)
        segments = _merge_overlapping_segments(
            [(min(l["x1"], l["x2"]), max(l["x1"], l["x2"])) for l in cluster]
        )
        for s_min, s_max in segments:
            result.append({"x1": round(s_min, 4), "y1": avg_y, "x2": round(s_max, 4), "y2": avg_y})
    return result


def _merge_vertical(lines: list, dist_threshold: float) -> list:
    if not lines:
        return []

    lines.sort(key=lambda l: (l["x1"] + l["x2"]) / 2)
    clusters: list[list] = [[lines[0]]]

    for i in range(1, len(lines)):
        prev_x = sum((l["x1"] + l["x2"]) / 2 for l in clusters[-1]) / len(clusters[-1])
        curr_x = (lines[i]["x1"] + lines[i]["x2"]) / 2
        if abs(curr_x - prev_x) < dist_threshold:
            clusters[-1].append(lines[i])
        else:
            clusters.append([lines[i]])

    result = []
    for cluster in clusters:
        avg_x = round(sum((l["x1"] + l["x2"]) / 2 for l in cluster) / len(cluster), 4)
        segments = _merge_overlapping_segments(
            [(min(l["y1"], l["y2"]), max(l["y1"], l["y2"])) for l in cluster]
        )
        for s_min, s_max in segments:
            result.append({"x1": avg_x, "y1": round(s_min, 4), "x2": avg_x, "y2": round(s_max, 4)})
    return result


def _merge_overlapping_segments(segments: list[tuple], gap: float = 0.03) -> list[tuple]:
    if not segments:
        return []
    segments.sort()
    merged = [segments[0]]
    for s_min, s_max in segments[1:]:
        prev_min, prev_max = merged[-1]
        if s_min <= prev_max + gap:
            merged[-1] = (prev_min, max(prev_max, s_max))
        else:
            merged.append((s_min, s_max))
    return merged
