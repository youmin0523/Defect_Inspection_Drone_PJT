# Roboflow Universe Candidates for Weak Detection Models

Research date: 2026-05-30
Scope: commercial drone INDOOR building-inspection product.
License rule: only **CC BY 4.0 / MIT / Public Domain** are commercially usable. **CC BY-NC = NOT usable** (none of the picks below are NC, but verify on-page before download).

> METHOD / RELIABILITY NOTE
> Roboflow Universe project pages are SPAs and returned **HTTP 403** to the WebFetch tool, so per-page DOM scraping was not possible. Instead, metadata below was gathered from **WebSearch result snippets corroborated across multiple independent queries** (image counts, class lists, license, seg-vs-bbox, "Pre-Trained Model" flags). Values confirmed by 2+ consistent snippets are stated plainly; single-snippet or conflicting values are marked **"unconfirmed"** and MUST be re-checked on the dataset page. Roboflow third-party **.pt weights are generally NOT downloadable** even when a "Pre-Trained Model" exists — so the default plan is always **download dataset + self-train**. Note: search-snippet metadata is second-hand; treat license fields as strong-but-not-final until visually confirmed on the License chip.

---

## Target 1 — M4 / Interior context segmentation
Wanted classes: wall, ceiling, floor, window, door (indoor room semantic/instance seg, ADE20K-like).

| Project (workspace/slug) | URL | Trained model? | #images | Classes | License | Seg or bbox |
|---|---|---|---|---|---|---|
| panopticindoor/panoptic-indoor-segmentation | https://universe.roboflow.com/panopticindoor/panoptic-indoor-segmentation | dataset-only | ~922 | 93 cls incl wall, ceiling, floor, door, cabinet-merged, shelf, sink, counter (**window not explicitly seen in snippets — verify**) | CC BY 4.0 | instance seg |
| research-twzom/room-interior | https://universe.roboflow.com/research-twzom/room-interior | dataset-only | ~2,781 | wall, ceiling, window, door | CC BY 4.0 | bbox (object detection) |
| wallceilingfloor/wall-ceiling-floor-m6bao | https://universe.roboflow.com/wallceilingfloor/wall-ceiling-floor-m6bao | yes (Pre-Trained Model, YOLOv11; .pt not downloadable) | ~7,086 | ceiling, floor, wall (no door/window) | CC BY 4.0 | instance seg |
| bytetrooper/room-detection-tfaxd | https://universe.roboflow.com/bytetrooper/room-detection-tfaxd | yes (Pre-Trained Model) | unconfirmed (~1.5k claimed, not confirmed) | door, room, stairs, wall, window | CC BY 4.0 | instance seg |
| genitor-ai/yolov8-wall-detection | https://universe.roboflow.com/genitor-ai/yolov8-wall-detection | dataset-only | ~230 | wall, floor, ceiling, pillar (no door/window) | unconfirmed | instance seg |
| renoai/ade20k-dataset-v4.0.1-fyluw | https://universe.roboflow.com/renoai/ade20k-dataset-v4.0.1-fyluw | yes (Pre-Trained Model) | unconfirmed | only "ceiling" + "other wall" per snippet (narrow — NOT full set) | CC BY 4.0 | instance seg |

**Recommendation:** Best single match = **panopticindoor/panoptic-indoor-segmentation** (CC BY 4.0, 93-class indoor *instance seg*, real photos, wall/ceiling/floor/door + furniture overlap) — confirm `window` is actually present. Strong runner-up with full door+window = **bytetrooper/room-detection-tfaxd** (CC BY 4.0 seg, door/room/stairs/wall/window). Plan: **download dataset + self-train** (.pt not downloadable); CC BY 4.0 confirmed in snippets but verify License chip on-page.

---

## Target 2 — furniture_aware
Wanted classes: wall, ceiling, floor, window, door, cabinet (built-in), kitchen_appliance, countertop/sink, kitchen_island, shelf.

| Project (workspace/slug) | URL | Trained model? | #images | Classes | License | Seg or bbox |
|---|---|---|---|---|---|---|
| panopticindoor/panoptic-indoor-segmentation | https://universe.roboflow.com/panopticindoor/panoptic-indoor-segmentation | dataset-only | ~922 | 93 cls incl cabinet-merged, shelf, sink, counter, microwave, oven, refrigerator, door, wall, floor, ceiling | CC BY 4.0 | instance seg |
| test-3vtzt/mit-indoor-semantic-segmentation | https://universe.roboflow.com/test-3vtzt/mit-indoor-semantic-segmentation | dataset-only | ~2,582 | very large set incl cabinet, ceiling, counter top, cupboards, door, dishwasher, cooker, bath tub (broadest furniture coverage) | unconfirmed (verify before commercial use) | semantic seg |
| countortop/insignia-object-detection | https://universe.roboflow.com/countortop/insignia-object-detection | yes (model exists) | unconfirmed | cabinet, countertop, floor, wall (4 cls, kitchen-focused) | CC BY 4.0 | instance seg |
| kitchenobjectdetection/kitchen-object-detection-acyvk | https://universe.roboflow.com/kitchenobjectdetection/kitchen-object-detection-acyvk | dataset-only | ~389 | 14 cls: countertopstone, countertopwood, sink, microwave, refrigerator, blender, bowl, cup, fork, knife, plate, spoon, wineglass, bottle | CC BY 4.0 | bbox |
| rohan-shaw-lpkr6/furniture-segmentation-lhinz | https://universe.roboflow.com/rohan-shaw-lpkr6/furniture-segmentation-lhinz | dataset-only | very small (~tens) | generic furniture (no published description) | CC BY 4.0 | semantic seg |
| test-ajz5o/kitchen-island | https://universe.roboflow.com/test-ajz5o/kitchen-island | dataset-only | ~295 | kitchen island | unconfirmed | bbox |

**Recommendation:** Best single source = **panopticindoor/panoptic-indoor-segmentation** (CC BY 4.0 *instance seg*, covers cabinet/shelf/sink/counter/appliances + wall/floor/ceiling/door in one set). For dedicated kitchen seg with wall/floor context use **countortop/insignia-object-detection** (CC BY 4.0, cabinet/countertop/floor/wall). Plan: **download dataset + self-train**; still budget **self-annotation** for `kitchen_island` and `built-in cabinet` (no clean CC-BY *seg* source covers all 10 wanted classes; mit-indoor has the names but its license is unverified).

---

## Target 3 — M5 / frames (window/door FRAME geometry segmentation)
Wanted classes: window frame, door frame, architectural opening boundaries.

| Project (workspace/slug) | URL | Trained model? | #images | Classes | License | Seg or bbox |
|---|---|---|---|---|---|---|
| walls-and-door-detection/walls-door-detection | https://universe.roboflow.com/walls-and-door-detection/walls-door-detection | yes (Pre-Trained Model) | ~4,674 | doors, walls, windows (whole objects, not frames) | CC BY 4.0 | instance seg |
| facade-elements/facade-elements-for-yolov8-instance-segmentation | https://universe.roboflow.com/facade-elements/facade-elements-for-yolov8-instance-segmentation | dataset-only | unconfirmed | door, window (whole openings, not frame rings) | CC BY 4.0 | instance seg |
| nicolai-hoirup-nielsen/window-segmentation | https://universe.roboflow.com/nicolai-hoirup-nielsen/window-segmentation | yes (Pre-Trained Model) | unconfirmed | window | **Public Domain** | instance seg |
| roboflow-universe-projects/windows-instance-segmentation | https://universe.roboflow.com/roboflow-universe-projects/windows-instance-segmentation | yes (Pre-Trained Model) | ~1,345 | window (whole window mask) | unconfirmed (verify) | instance seg |
| pamz3ddesigns6-is4mp/window-and-door-detection | https://universe.roboflow.com/pamz3ddesigns6-is4mp/window-and-door-detection | yes (Pre-Trained Model) | ~64 (small) | Door, Entrance, Windows | CC BY 4.0 | instance seg |
| mzworkspace-segj7/window-segment-main | https://universe.roboflow.com/mzworkspace-segj7/window-segment-main | yes (Pre-Trained Model, YOLOv11) | ~203 | window (2 cls) | CC BY 4.0 | instance seg |
| ir-2znee/facade_test | https://universe.roboflow.com/ir-2znee/facade_test | yes (Pre-Trained Model) | ~382 | window/door facade regions (frame-level unconfirmed) | unconfirmed | semantic seg |

**Recommendation:** No dataset provides true **frame-boundary** polygon masks (window-frame / door-frame ring distinct from the glazing/leaf). Closest usable seg base = **walls-and-door-detection/walls-door-detection** (4.6k imgs, CC BY 4.0, instance seg of door+window+wall); for window-only with the cleanest license use **nicolai-hoirup-nielsen/window-segmentation** (Public Domain). Plan: **download dataset + self-train a seg model**; the `window_frame`/`door_frame` frame-ring classes will require **self-annotation** (derive from whole window/door masks) since no source carries them.

---

## Required manual verification (tools could not DOM-scrape; 403)
1. Open each URL and read the License chip — reject any **CC BY-NC**. Snippet-confirmed CC BY 4.0 items still warrant a quick visual check; the genuinely unverified ones (mit-indoor-semantic-segmentation, facade_test, genitor-ai/yolov8-wall-detection, test-ajz5o/kitchen-island, windows-instance-segmentation) are the priority checks.
2. Confirm seg-vs-bbox, image count, and the exact class list on the Classes / Health Check panel.
3. Confirm `window` is actually present in panoptic-indoor (snippet listed door but not window explicitly).
4. Plan for all three: **download dataset (YOLO/COCO seg export) + self-train**; do NOT rely on third-party .pt (not downloadable).
5. Targets 2 and 3 will likely need **self-annotation** (kitchen_island/built-in cabinet for T2; window_frame/door_frame for T3) — no clean source covers them.
