# Roboflow Universe — M2 Interior Wall Surface / Finishing Defect Candidate Models

> Target M2 classes: wall surface defect, wallpaper(벽지) defect, peeling paint, scratch, stain,
> baseboard/skirting defect, blistering, mold on interior wall.
> Excluded scope: solar panel, metal/industrial surface, exterior-facade-only datasets.
> Usage: run locally via the `inference` package and ensemble with our own M2 model.
> Qualifies only if a **DEPLOYED model version** exists, loadable as
> `model_id = "project-slug/VERSION"` via `inference.get_model(...)`.
>
> Researched 2026-06-01. WebSearch worked; direct WebFetch of Universe project pages returned
> HTTP 403, so license fields that could not be read off the page are marked **unconfirmed**.
> The presence of a `/model/N` "How to Use the ... API" page in search results is a reliable
> signal that a deployed model version N exists.

## Candidate Table

| # | workspace / project-slug | Full URL | Classes | #images | License | Deployed model version? |
|---|--------------------------|----------|---------|---------|---------|--------------------------|
| 1 | peumalab / wall-defects | https://universe.roboflow.com/peumalab/wall-defects | corrosion, crack, deterioration, moisture, mold, stain | 376 | **CC BY 4.0 (commercial OK)** — user-confirmed | Yes — v2 (`wall-defects/2`), `/model/2` API page exists |
| 2 | builddef2 / building-defect-on-walls | https://universe.roboflow.com/builddef2/building-defect-on-walls | crack, mold, peeling_paint, stairstep_crack, water_seepage | 472 | **CC BY 4.0 (commercial OK)** — confirmed in search snippets | Yes — v4 (`building-defect-on-walls/4`), `/model/4` API page exists |
| 3 | dissertationproject / mould-detection-aaron | https://universe.roboflow.com/dissertationproject/mould-detection-aaron | mould (interior wall mould; property/facility inspection use case) | 988 | **CC BY 4.0 (commercial OK)** — confirmed in search snippets | Yes — v2 (`mould-detection-aaron/2`), `/model/2` API page exists |
| 4 | main-zxmvk / paint-defects-dfbjj | https://universe.roboflow.com/main-zxmvk/paint-defects-dfbjj | paint defects (peeling/crack/dirt etc.; full list unconfirmed) | 743 | unconfirmed | Yes — v2 (`paint-defects-dfbjj/2`), `/model/2` API page exists |
| 5 | sidharth-dwh8q / paint-defect-detection-hoo99 | https://universe.roboflow.com/sidharth-dwh8q/paint-defect-detection-hoo99 | paint defect (peeling/paint damage; full list unconfirmed) | 68 | unconfirmed | Yes — v4 (`paint-defect-detection-hoo99/4`), `/model/4` API page exists |
| 6 | university-of-salford-d3dwy / mold-detection-project | https://universe.roboflow.com/university-of-salford-d3dwy/mold-detection-project | mold | 475 | unconfirmed | Yes — v1 (`mold-detection-project/1`), `/model/1` API page exists |

### Also found (kept as backup, narrower fit)
- **sainitincnn / stain-defect-detection** — https://universe.roboflow.com/sainitincnn/stain-defect-detection — stain; 97 images; **Public Domain (commercial OK)** — confirmed; deployed v1 (`/model/1` exists). Small dataset.
- **joe-i4soa / building-defect** — https://universe.roboflow.com/joe-i4soa/building-defect — building defects (mold/tile crack/tile delamination per search); license unconfirmed; deployed v1 (`/model/1` exists).

## Recommendation (2 lines)

- **Single best commercially-licensed deployable candidate:** `peumalab/wall-defects` (v2) — it is the
  only candidate with a **confirmed commercial license (CC BY 4.0)** AND a deployed model version, and
  its classes (crack, mold, moisture, stain, deterioration, corrosion) map directly onto our interior
  M2 surface/finishing scope. Use `model_id = "wall-defects/2"`.
- **Needs version/license confirmation:** rows 4 (`paint-defects-dfbjj`) and 5
  (`paint-defect-detection-hoo99`) and 6 (`mold-detection-project`) have a deployed model version but
  their licenses are **unconfirmed** (Universe page WebFetch returned 403). Confirm each reads
  CC BY 4.0 / MIT / Public Domain / Apache before commercial use — any CC BY-NC = NOT usable. Best
  class-complement to peumalab is `builddef2/building-defect-on-walls/4` (CC BY 4.0, adds `peeling_paint`),
  and `mould-detection-aaron/2` (CC BY 4.0) for a dedicated interior-mould booster.

## Verify-before-use checklist (per ONNX class-mapping audit rule)
1. Confirm license on the dataset/version page: CC BY 4.0 / MIT / Public Domain / Apache = OK; CC BY-NC = NOT usable; unknown = treat as NOT usable until confirmed.
2. Smoke-test load: `inference.get_model("project-slug/VERSION", api_key=...)` must succeed.
3. Cross-check the model's class list ↔ our M2 class mapping ↔ taxonomy before ensembling.
4. Re-confirm the project targets interior wall surface/finishing (not metal/solar/exterior-only).
