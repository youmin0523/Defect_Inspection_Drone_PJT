"""
일회성 보완 캡쳐 — 2026-04-16 피드백 라운드별 스크린샷을
오늘 Notion 페이지 하단에 "📸 라운드별 스크린샷" 섹션으로 덧붙인다.

sync_notion_logs.py 의 기존 유틸(upload_to_imgbb / _notion_headers / find_daily_page)을 재사용.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_notion_logs import (
    get_notion_key,
    get_database_id,
    get_imgbb_api_key,
    upload_to_imgbb,
    _notion_headers,
    find_daily_page,
    SCREENSHOTS_DIR,
    APP_URL,
)


ROUNDS = [
    {
        "label": "📞 R3+R5 (15:22 / 16:10) · 도입문의 모달 — 사업자 진위확인 + 한 화면 수납 (재캡쳐)",
        "path": "/",
        "prepare": "open_contact_modal_business",
    },
]


def _signup_click_business(page):
    page.wait_for_load_state("networkidle", timeout=8000)
    page.get_by_role("button", name="사업자 (개인/법인)").first.click()
    page.wait_for_timeout(400)


def _open_contact_modal_business(page):
    page.wait_for_load_state("networkidle", timeout=8000)
    page.get_by_role("button", name="도입 문의하기").first.click()
    page.wait_for_timeout(500)
    page.locator('label:has-text("사업자 (개인/법인)")').first.click()
    page.wait_for_timeout(500)


PREPARE_FNS = {
    "click_business_tab": _signup_click_business,
    "open_contact_modal_business": _open_contact_modal_business,
}


def capture_round(playwright, idx, round_def):
    from_page = playwright.chromium.launch(headless=True)
    context = from_page.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    url = APP_URL.rstrip("/") + round_def["path"]
    print(f"  📷 [{idx+1}/{len(ROUNDS)}] {round_def['label']}")
    print(f"     → {url}")
    page.goto(url, wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(1000)

    prep = round_def.get("prepare")
    if prep and prep in PREPARE_FNS:
        try:
            PREPARE_FNS[prep](page)
        except Exception as e:
            print(f"     ⚠️  prepare({prep}) 실패: {e}")

    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = os.path.join(SCREENSHOTS_DIR, f"round{idx+1}_{ts}.png")
    page.screenshot(path=img_path, full_page=False)
    from_page.close()
    print(f"     ✅ 저장: {os.path.basename(img_path)}")
    return img_path


def append_screenshots_section(api_key, page_id, items):
    blocks = [
        {"object": "block", "type": "divider", "divider": {}},
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {"type": "text", "text": {"content": "📸 라운드별 스크린샷 (2026-04-16)"}}
                ],
                "color": "default",
            },
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "상단 세션 로그의 피드백 라운드(R1~R5)에 대응하는 UI 캡쳐 — 각 이미지 위 제목이 해당 라운드 라벨."
                        },
                    }
                ],
                "icon": {"type": "emoji", "emoji": "🗂️"},
                "color": "gray_background",
            },
        },
    ]

    for label, url in items:
        blocks.append(
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": label}}],
                    "color": "default",
                },
            }
        )
        blocks.append(
            {
                "object": "block",
                "type": "image",
                "image": {"type": "external", "external": {"url": url}},
            }
        )

    req = urllib.request.Request(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        data=json.dumps({"children": blocks}).encode("utf-8"),
        headers=_notion_headers(api_key),
        method="PATCH",
    )
    with urllib.request.urlopen(req) as res:
        return res.status == 200


def main():
    api_key = get_notion_key()
    database_id = get_database_id()
    imgbb_key = get_imgbb_api_key()
    if not (api_key and database_id and imgbb_key):
        print("❌ NOTION_API_KEY / NOTION_DATABASE_ID / IMGBB_API_KEY 확인 필요")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    page_id = find_daily_page(api_key, database_id, today)
    if not page_id:
        print(f"❌ {today} 일일 페이지를 찾지 못함 — 먼저 sync_notion_logs.py 실행 필요")
        return
    print(f"▶ 오늘 페이지: {page_id}")

    from playwright.sync_api import sync_playwright

    uploaded = []
    with sync_playwright() as pw:
        for idx, rd in enumerate(ROUNDS):
            try:
                img_path = capture_round(pw, idx, rd)
                url = upload_to_imgbb(img_path, imgbb_key)
                if url:
                    print(f"     📤 imgBB 업로드 완료")
                    uploaded.append((rd["label"], url))
                else:
                    print(f"     ❌ 업로드 실패 — 스킵")
            except Exception as e:
                print(f"     ❌ 캡쳐 실패: {e}")

    if not uploaded:
        print("❌ 업로드된 이미지가 없어 Notion 추가 생략")
        return

    ok = append_screenshots_section(api_key, page_id, uploaded)
    print(f"\n{'✅' if ok else '❌'} Notion 추가 — {len(uploaded)}개 라운드 스크린샷 첨부")


if __name__ == "__main__":
    main()
