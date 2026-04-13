# =============================================
# tests/test_defects_api.py
# 역할: 하자 탐지 로그 REST API 테스트
#       - GET /defects 목록 조회
#       - POST /defects 하자 저장
#       - GET /defects/{id} 단건 조회
#       - GET /defects/summary 요약 통계
# 실행: pytest tests/test_defects_api.py -v
# =============================================

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    """테스트용 비동기 HTTP 클라이언트"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_defects_empty(client):
    """하자 목록 조회 - 빈 결과"""
    response = await client.get("/api/v1/defects")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_defect(client):
    """신규 하자 저장"""
    payload = {
        "area": "A",
        "category_code": "A-02",
        "defect_type": "균열 (구조 균열)",
        "severity": "HIGH",
        "confidence": 0.87,
        "bbox": {"x": 0.5, "y": 0.5, "w": 0.1, "h": 0.15},
    }
    response = await client.post("/api/v1/defects", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["category_code"] == "A-02"
    assert data["severity"] == "HIGH"
    return data["id"]


@pytest.mark.asyncio
async def test_get_defect_summary(client):
    """요약 통계 조회"""
    response = await client.get("/api/v1/defects/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_severity" in data
    assert "by_area" in data


@pytest.mark.asyncio
async def test_filter_defects_by_severity(client):
    """심각도 필터링"""
    response = await client.get("/api/v1/defects?severity=HIGH")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_filter_defects_by_area(client):
    """영역 필터링"""
    response = await client.get("/api/v1/defects?area=A")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_nonexistent_defect(client):
    """존재하지 않는 하자 조회 → 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/defects/{fake_id}")
    assert response.status_code == 404
