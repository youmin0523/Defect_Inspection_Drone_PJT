# Roboflow Universe Trained Models — furniture_aware + M5 frames

> Purpose: candidate **trained** Roboflow Universe models, deployable locally via the
> `inference` package as `model_id = "<workspace-slug>/<project-slug>/<version>"`, to run
> alongside and ensemble with our own indoor building-inspection drone models.
>
> **Research method / verification status (2026-05-30):** Project/workspace **slugs** below are
> taken from live Roboflow Universe URLs returned by web search and are reliable. **Image
> counts, class lists, licenses, and mAP** come from search-result snippets — most are well
> corroborated and are stated as fact below, but each should still be spot-checked on the page.
> **Version numbers:** where a `/model/N` deploy URL was observed, that `N` is a confirmed
> deployable trained version and appears in the model_id; otherwise the entry is marked
> **"version unconfirmed"** (open the project's Versions tab, pick the latest trained version,
> read the deploy snippet). The model_id format is confirmed by Roboflow docs:
> `get_model(model_id="<workspace>/<project>/<version>")` (Universe models require an API key).
> Project pages are JS-rendered so WebFetch could not open them directly; licenses were read
> from search snippets and the platform default (CC BY 4.0). **Per the safety-critical /
> ONNX-mapping audit rules, confirm slug + version + class list + license on the live page and
> pass the 4-way class-mapping cross-check before wiring anything into the ensemble.**

---

## Target 1 — furniture_aware (false-positive gate)
Indoor + kitchen classes: wall, ceiling, floor, window, door, built-in cabinet, kitchen
appliance, countertop/sink, kitchen island, shelf. Segmentation preferred (bbox OK as a gate).

| # | Project (workspace/slug) | URL | model_id for `inference` | #images | classes (reported) | License | seg/bbox | mAP |
|---|---|---|---|---|---|---|---|---|
| 1 | wallceilingfloor / wall-ceiling-floor-m6bao | https://universe.roboflow.com/wallceilingfloor/wall-ceiling-floor-m6bao | `wallceilingfloor/wall-ceiling-floor-m6bao/1` (model/1 confirmed) | ~18,051 (dataset listing shows ~7.1k) | ceiling, floor, wall (YOLOv11n-seg) | **CC BY 4.0** | seg | **88.7% mAP** |
| 2 | cabinet-detection / floorplan-cabinet-detection | https://universe.roboflow.com/cabinet-detection/floorplan-cabinet-detection | version unconfirmed | ~2,899 | 17 cls: Kitchen_bar, Stairs, armchair, bed, coffee_table, dining_table, door, large_sofa, round_table, **sink**, small_sink, small_sofa, toilet, tub, twin_sink, **wall, window** | CC BY 4.0 (default, unconfirmed) | bbox | unconfirmed |
| 3 | charmie-furniture / furniture-q8v7j | https://universe.roboflow.com/charmie-furniture/furniture-q8v7j | version unconfirmed | ~559 | 8 cls: bed, **cabinet, cabinet_doors, dishwasher**, dishwasher_pod, dishwasher_rack, door, trash_can (YOLOv11n-seg) | **CC BY 4.0** | seg | unconfirmed |
| 4 | indoor-objects / indoor-5iwhq | https://universe.roboflow.com/indoor-objects/indoor-5iwhq | version unconfirmed | ~1,205 (snippet) | 11 cls: bed, chair, door, **door-frame**, shower, **sink**, sofa, stairs, table, toilet (+1) | **CC BY 4.0** | bbox | unconfirmed |
| 5 | andis-tests / room-object-detection | https://universe.roboflow.com/andis-tests/room-object-detection | version unconfirmed | unconfirmed | 12 cls: armchair, bed, coffee_table, dining_table, large_sink, large_sofa, round_table, **sink**, small_sink, small_sofa, tub, twin_sink (roboflow-3-n-seg) | **CC BY 4.0** | seg | unconfirmed |
| 6 | mokhamed-nagy-u69zl / furniture-detection-qiufc | https://universe.roboflow.com/mokhamed-nagy-u69zl/furniture-detection-qiufc | version unconfirmed | ~8,055 | chair, table, door, bed, sofa, window, couch, dining table, **wall, shelf, floor, cabinet**, lamp, monitor | CC BY 4.0 (default, unconfirmed) | bbox | unconfirmed |

**Recommendation (Target 1):** Best commercially-licensed deployable model is **#1
`wallceilingfloor/wall-ceiling-floor-m6bao/1`** — the only Target-1 candidate with a **confirmed
deployable version (`/1`)**, confirmed **CC BY 4.0**, true segmentation, highest mAP (88.7%),
covering the core gate classes wall/ceiling/floor. Pair it with **#3
`charmie-furniture/furniture-q8v7j`** (seg, confirmed CC BY 4.0, adds cabinet/cabinet_doors/
dishwasher) for kitchen-cabinet/appliance coverage. **Only #1 has a confirmed version number;**
#2–#6 are "version unconfirmed" (read each Versions tab). Note: a generic kitchen-appliance
seg model (countertop/refrigerator/stove) was NOT found — `nizarbtk/kitchen-cjfwg` turned out to
be a food-ingredient dataset, not fixtures, so it is excluded.

---

## Target 2 — M5 frames (window frame / door frame / opening geometry)
Window frame / door frame / architectural opening segmentation, or whole window+door instance
segmentation as the closest available proxy. No frame-only ("window_frame"/"door_frame")
geometry seg model was found; whole-opening instance seg is the proxy (indoor-5iwhq does expose
a `door-frame` bbox class — see Target 1 #4).

| # | Project (workspace/slug) | URL | model_id for `inference` | #images | classes (reported) | License | seg/bbox | mAP |
|---|---|---|---|---|---|---|---|---|
| 1 | cubicasa-qa / door-window-cwazm | https://universe.roboflow.com/cubicasa-qa/door-window-cwazm | `cubicasa-qa/door-window-cwazm/2` (model/2 confirmed) | ~852 | door, window (YOLOv11 instance seg, Accurate) | CC BY 4.0 (default, unconfirmed) | seg | **96.0% mAP@50** (mAP 95.6) |
| 2 | roboflow-universe-projects / windows-instance-segmentation | https://universe.roboflow.com/roboflow-universe-projects/windows-instance-segmentation | `roboflow-universe-projects/windows-instance-segmentation/3` (model/3 confirmed) | ~1,345 | window (v3 resize512_aug3x) | **CC BY 4.0** | seg | unconfirmed |
| 3 | walls-and-door-detection / walls-door-detection | https://universe.roboflow.com/walls-and-door-detection/walls-door-detection | version unconfirmed | ~4,674 | Doors, walls, windows (roboflow-3-n-seg) | **CC BY 4.0** | seg | unconfirmed |
| 4 | pamz3ddesigns6-is4mp / window-and-door-detection | https://universe.roboflow.com/pamz3ddesigns6-is4mp/window-and-door-detection | version unconfirmed | ~64 | Door, Entrance, Windows (roboflow-3-n-seg) | **CC BY 4.0** | seg | unconfirmed |
| 5 | building-facade / building-facade-segmentation-instance | https://universe.roboflow.com/building-facade/building-facade-segmentation-instance | version unconfirmed | ~598 | 10 cls incl. **window**, facade, balcony-fence, shop, vegetation, street… (NOTE: no `door` class) | **CC BY 4.0** | seg | unconfirmed |

**Recommendation (Target 2):** Best commercially-licensed deployable model is **#1
`cubicasa-qa/door-window-cwazm/2`** — **confirmed deployable version (`/2`)**, YOLOv11 instance
segmentation of door+window (the best available opening-geometry proxy), highest mAP
(96.0%@50), ~852 images; license is platform-default CC BY 4.0 but should be verified on the
page. Back it up with **#2 `roboflow-universe-projects/windows-instance-segmentation/3`**
(confirmed `/3`, ~1,345 imgs, window-only seg, **confirmed CC BY 4.0**) for window recall.
**#1 and #2 have confirmed version numbers;** #3–#5 are "version unconfirmed". No true
frame-only seg model exists on Universe — whole window+door instance seg is the proxy.

---

### Confirmed-version summary (usable directly in model_id)
- **CONFIRMED** version in model_id (deploy `/model/N` URL observed):
  - `wallceilingfloor/wall-ceiling-floor-m6bao/1` — Target 1 (CC BY 4.0, 88.7% mAP, seg)
  - `cubicasa-qa/door-window-cwazm/2` — Target 2 (96.0% mAP@50, seg)
  - `roboflow-universe-projects/windows-instance-segmentation/3` — Target 2 (CC BY 4.0, seg)
- **UNCONFIRMED** version (slug known; pick latest trained version from the Versions tab):
  cabinet-detection/floorplan-cabinet-detection · charmie-furniture/furniture-q8v7j ·
  indoor-objects/indoor-5iwhq · andis-tests/room-object-detection ·
  mokhamed-nagy-u69zl/furniture-detection-qiufc · walls-and-door-detection/walls-door-detection ·
  pamz3ddesigns6-is4mp/window-and-door-detection · building-facade/building-facade-segmentation-instance
- **Licenses:** Confirmed **CC BY 4.0** (commercially usable w/ attribution): wall-ceiling-floor,
  charmie-furniture, indoor-5iwhq, room-object-detection, windows-instance-segmentation,
  walls-door-detection, window-and-door-detection, building-facade-segmentation-instance. Others
  default to CC BY 4.0 (verify). **No CC BY-NC candidate was identified** — but confirm on each page.

### Before any ensemble integration
1. Open each project page, confirm a **trained version** exists (model/health-check, not dataset-only).
2. Record exact `workspace-slug/project-slug/version`, image count, class list, seg-vs-bbox, mAP, **license** (accept CC BY 4.0 / MIT / Public Domain; reject CC BY-NC).
3. Run the 4-way ONNX class-mapping cross-check (model dims ↔ data.yaml/CLASS_NAMES ↔ inference mapping ↔ taxonomy) before wiring into furniture_aware / M5.
