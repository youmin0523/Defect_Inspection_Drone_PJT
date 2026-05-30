# Roboflow Universe Trained-Model Candidates — M1 / M2 / M3

Goal: deployable Roboflow Universe **trained models** (usable via the `inference` package as
`model_id = "<workspace-slug>/<project-slug>/<version>"`) to ensemble locally (CPU/GPU) with our own
models for commercial drone building inspection.

How to use a model with the `inference` package (local CPU/GPU):

```python
from inference import get_model
model = get_model(model_id="workspace-slug/project-slug/VERSION", api_key=ROBOFLOW_API_KEY)
results = model.infer("frame.jpg")
```

## Research method + verification caveat (READ FIRST)

Findings below were assembled on **2026-05-30** primarily from **Roboflow Universe web search results**.
Direct page scraping was **blocked**: `universe.roboflow.com` is behind Cloudflare (raw fetch returns a
"Just a moment…" challenge), `WebFetch` returned **HTTP 403**, and the public `api.roboflow.com`
endpoint requires an API key. Therefore:

- **Almost every VERSION number below is `version unconfirmed`.** A search result confirming a project
  has a "pre-trained model and API" (or a `…/model/N` URL) proves a deployable model *exists*, but the
  **exact integer to put after the slug must be read from each project's Versions/Deploy tab in-app**
  (or fetched via the Roboflow API with our key) before it is hard-coded into `model_id`.
- mAP values were **not exposed** to web search for any candidate → all marked **unconfirmed**.
- Image counts / class lists are taken from search snippets and should be re-confirmed in-app.

> Licensing rule applied: **CC BY 4.0 / MIT / Public Domain / CC0 / Apache = commercial OK**.
> **CC BY-NC = NOT usable** (would be flagged). Every candidate whose license surfaced in search was
> **CC BY 4.0 (commercial OK)**; none surfaced as CC BY-NC. Licenses that did not surface are marked
> **unconfirmed** and MUST be checked before commercial use (do not assume).

> model_id note: the trailing `/VERSION` must point at a version that has a **trained model deployed**
> (the `…/model/N` endpoint), not a dataset-only version.

---

## Target M1 — Structural / Waterproofing (crack, waterproofing defect, caulking/sealant defect)

| Project (workspace/slug) | URL | model_id for `inference` | #images | Classes | License | mAP |
|---|---|---|---|---|---|---|
| builddef2 / building-defect-on-walls | https://universe.roboflow.com/builddef2/building-defect-on-walls | `builddef2/building-defect-on-walls/4` (**v4 confirmed** as latest, 2023-05-27; pre-trained model + API — confirm `model/4` is deployed) | 472 | crack, mold, peeling_paint, stairstep_crack, water_seepage | CC BY 4.0 (commercial OK) | unconfirmed |
| university-bswxt / crack-bphdr | https://universe.roboflow.com/university-bswxt/crack-bphdr | `university-bswxt/crack-bphdr/VERSION` (**version unconfirmed**; v1 2022-09-02 + v2 2022-09-29 exist, pre-trained model + API) | ~1551 (concrete) | crack (1 class, instance segmentation) | unconfirmed (verify in-app) | unconfirmed |
| marieam / crack-bphdr-bl00w | https://universe.roboflow.com/marieam/crack-bphdr-bl00w | `marieam/crack-bphdr-bl00w/VERSION` (**version unconfirmed**; "Pre-Trained Model" labeled) | unconfirmed | crack (instance segmentation) | unconfirmed (verify in-app) | unconfirmed |
| wongkinyiu / crack-bphdr-g9koq | https://universe.roboflow.com/wongkinyiu/crack-bphdr-g9koq | `wongkinyiu/crack-bphdr-g9koq/VERSION` (**version unconfirmed**) | unconfirmed | crack (object detection) | unconfirmed (verify in-app) | unconfirmed |

Notes for M1:
- **`water_seepage` (waterproofing)** is covered only by `builddef2/building-defect-on-walls` — the one
  candidate that bundles crack + waterproofing-type + peeling in a single deployable model. No standalone
  **caulking/sealant-defect** trained model was found on Universe — treat sealant defects as a
  **build-our-own gap**.
- `university-bswxt/crack-bphdr` and its forks (marieam, wongkinyiu) are pure-crack and well-known
  (this is the dataset used in the Ultralytics "crack-seg" tutorials) — good for crack recall, but
  contribute nothing to waterproofing/sealant.

**Recommendation (M1):** `builddef2/building-defect-on-walls` (CC BY 4.0, ~472 imgs, classes
crack/mold/peeling_paint/stairstep_crack/water_seepage) is the single best commercially-licensed
deployable model — it is the only candidate covering both cracking and waterproofing (water_seepage)
in one model. **Action required:** open its Versions tab to confirm the deployable integer for `model_id`.

---

## Target M2 — Surface / Finishing (wall surface defect, baseboard/skirting, peeling, scratch, stain)

| Project (workspace/slug) | URL | model_id for `inference` | #images | Classes | License | mAP |
|---|---|---|---|---|---|---|
| builddef2 / building-defect-on-walls | https://universe.roboflow.com/builddef2/building-defect-on-walls | `builddef2/building-defect-on-walls/4` (**v4 confirmed** latest) | 472 | crack, mold, peeling_paint, stairstep_crack, water_seepage | CC BY 4.0 (commercial OK) | unconfirmed |
| pintura / defects-on-surfaces-paint | https://universe.roboflow.com/pintura/defects-on-surfaces-paint | `pintura/defects-on-surfaces-paint/VERSION` (**version unconfirmed**; trained model exists) | unconfirmed | paint surface defects (verify exact class list in-app) | unconfirmed (verify in-app) | unconfirmed |
| gurudas-patle-lapp1 / sagging-paint-defect-error-free | https://universe.roboflow.com/gurudas-patle-lapp1/sagging-paint-defect-error-free | `gurudas-patle-lapp1/sagging-paint-defect-error-free/VERSION` (**version unconfirmed**; pre-trained model) | unconfirmed | High DFT, Sagging | CC BY 4.0 (commercial OK) | unconfirmed |
| sidharth-dwh8q / paint-defect-detection-hoo99 | https://universe.roboflow.com/sidharth-dwh8q/paint-defect-detection-hoo99 | `sidharth-dwh8q/paint-defect-detection-hoo99/4` (**v4 CONFIRMED** via public `…/model/4` endpoint, 2024-06-26; pre-trained model + API) | 68 | bird-drop, oxidation, swirl-marks | CC BY 4.0 (commercial OK) | unconfirmed |

Notes for M2:
- **No baseboard/skirting-specific** trained model was found — **build-our-own gap**. Closest interior-
  finishing coverage is `builddef2`'s peeling_paint + mold.
- `sidharth-dwh8q/paint-defect-detection-hoo99` is the **only candidate with a confirmed version number**
  (`/4`, from its public `…/model/4` endpoint), BUT its classes (bird-drop, oxidation, swirl-marks) are
  **solar-panel / outdoor-coating oriented, NOT interior wall finishing** — include only if those map to
  your taxonomy; otherwise it is a poor fit for M2.
- The earlier "scratch/stain" leads in search were **metal/industrial** (NEU steel-surface set:
  scratches/inclusion/patches/pitted_surface) — excluded as not interior-wall.

**Recommendation (M2):** `builddef2/building-defect-on-walls` (CC BY 4.0, ~472 imgs) is again the best
commercially-licensed deployable model for wall finishing — covers peeling_paint, mold, crack on actual
building walls. Reinforce with `pintura/defects-on-surfaces-paint` for broader paint-surface defects.
**Action required:** confirm both version integers in-app (only `paint-defect-detection-hoo99/4` is
version-confirmed, and it is off-taxonomy).

---

## Target M3 — Floor / Window (floor defect, glass defect, window/door frame defect)

| Project (workspace/slug) | URL | model_id for `inference` | #images | Classes | License | mAP |
|---|---|---|---|---|---|---|
| capjamesg / glass-defect-detection-fvbcu | https://universe.roboflow.com/capjamesg/glass-defect-detection-fvbcu | `capjamesg/glass-defect-detection-fvbcu/VERSION` (**version unconfirmed**; pre-trained model + API, pub. Aug 2025) | ~1728 | glass defect (verify exact class list in-app) | unconfirmed (verify in-app) | unconfirmed |
| maruf-workspace / glass-defect-detection-qjchk | https://universe.roboflow.com/maruf-workspace/glass-defect-detection-qjchk | `maruf-workspace/glass-defect-detection-qjchk/VERSION` (**version unconfirmed**) | ~86 | scratches, bubbles, chipping, broke, dipz | unconfirmed (verify in-app) | unconfirmed |
| airlab-fqoff / glass-xqjx8 | https://universe.roboflow.com/airlab-fqoff/glass-xqjx8 | `airlab-fqoff/glass-xqjx8/VERSION` (**version unconfirmed**; pre-trained model + API) | ~85 | glass defect (verify in-app) | unconfirmed (verify in-app) | unconfirmed |
| dylan-vaca-aovsf / door-window-detection-pipvh | https://universe.roboflow.com/dylan-vaca-aovsf/door-window-detection-pipvh | `dylan-vaca-aovsf/door-window-detection-pipvh/VERSION` (**version unconfirmed**; pre-trained model + API, ~1355 imgs — largest window/door set found) | ~1355 | doors, windows (detects the objects, **NOT frame *defects***) | unconfirmed (verify in-app) | unconfirmed |
| smart-buildings / window-detection-tzxgz | https://universe.roboflow.com/smart-buildings/window-detection-tzxgz | `smart-buildings/window-detection-tzxgz/VERSION` (**version unconfirmed**; pre-trained model) | unconfirmed | window (detects the window object, **NOT frame *defects***) | unconfirmed (verify in-app) | unconfirmed |

Notes for M3:
- **Floor-defect:** no clearly-verifiable interior **floor-defect** trained model surfaced to search
  (results were dominated by floor-*plan* detection, which is unrelated). Treat floor-defect as a
  **build-our-own / further-search gap** — re-search in-app where the Cloudflare block does not apply.
- **Glass:** good coverage. `capjamesg/glass-defect-detection-fvbcu` (~1728 imgs) is the largest and
  most recent; `maruf-workspace/…-qjchk` has the most descriptive class list (scratches/bubbles/
  chipping/broke). Confirm classes + license in-app (capjamesg's license did not surface).
- **Window/door frame *defect*** is a gap: `smart-buildings/window-detection-tzxgz` detects the window
  object, not defects (warping, seal failure, corrosion) on the frame — **build-our-own gap**.

**Recommendation (M3):** `capjamesg/glass-defect-detection-fvbcu` (~1728 imgs, recent, pre-trained
model + API) is the best deployable glass model — **pending an in-app license check** (its license did
not surface in search; do not deploy commercially until confirmed CC BY 4.0 / MIT / Public Domain). If
its license is non-commercial, fall back to `maruf-workspace/glass-defect-detection-qjchk`. **Floor and
window-frame defect have no usable trained model found — flag both as build-our-own.**

---

## Version-confirmation summary (for direct use in `model_id`)

**Version number CONFIRMED (latest version / deployable `…/model/N` endpoint seen in search):**
- `builddef2/building-defect-on-walls/4`           (M1 + M2 top pick — v4 is latest, 2023-05-27; confirm `model/4` is the deployed trained model)
- `sidharth-dwh8q/paint-defect-detection-hoo99/4`  (v4 via public `…/model/4` endpoint — but classes off-taxonomy for M2, see notes)

**Pre-trained model CONFIRMED to exist, but VERSION integer UNCONFIRMED** (must read Versions/Deploy
tab in-app or query the Roboflow API with our key before building `model_id`):
- `university-bswxt/crack-bphdr/?`                  (v1 + v2 exist)
- `marieam/crack-bphdr-bl00w/?`
- `wongkinyiu/crack-bphdr-g9koq/?`
- `pintura/defects-on-surfaces-paint/?`
- `gurudas-patle-lapp1/sagging-paint-defect-error-free/?`
- `capjamesg/glass-defect-detection-fvbcu/?`       (M3 glass top pick — license also unconfirmed)
- `maruf-workspace/glass-defect-detection-qjchk/?`
- `airlab-fqoff/glass-xqjx8/?`
- `smart-buildings/window-detection-tzxgz/?`        (window object only, not frame defects)

## Gaps to fill with our own data (no usable Universe model found)
- M1: caulking / sealant defect (waterproofing partially covered by builddef2 `water_seepage`)
- M2: baseboard / skirting defect
- M3: interior **floor** defect; window/door **frame** defect

## Why so many "unconfirmed"
`universe.roboflow.com` is Cloudflare-protected and `WebFetch` was blocked (HTTP 403); the public API
needs a key. All version integers, mAP values, and several licenses therefore could not be machine-
verified here. The fastest reliable confirmation is to run, with our Roboflow API key:

```python
from roboflow import Roboflow
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
proj = rf.workspace("builddef2").project("building-defect-on-walls")
print(proj.versions())   # -> exact deployable version integers + model metadata
```
