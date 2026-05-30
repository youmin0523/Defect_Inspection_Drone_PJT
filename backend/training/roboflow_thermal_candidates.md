# Roboflow Universe — Thermal Building-Defect Model Candidates

Research date: 2026-05-30. Target use: commercial drone building-inspection (FLIR/thermal pseudocolor) detecting insulation defects, moisture/water leaks, thermal anomalies, delamination, cracks.

Verification note: Roboflow Universe project pages are JS-rendered and returned HTTP 403 to direct fetch, so image counts / classes below come from Roboflow Universe search-index snippets (reliable for counts + class lists) rather than the live page DOM. Exact license and mAP are shown on each project's page and are marked "unconfirmed" where the snippet did not expose them — open each shortlisted project in a browser to confirm license + mAP before adoption.

## A) Candidate Models

| Project (workspace/slug) | URL | Trained model? | #images | Classes | License | mAP-if-shown |
|---|---|---|---|---|---|---|
| idt/thermal-images-in-building-inspection | https://universe.roboflow.com/idt/thermal-images-in-building-inspection | yes (pre-trained model + hosted API) | ~58 | air infiltration, air leakage, delamination, hollow, insulation, moisture (6) | unconfirmed | unconfirmed |
| scanx-datasets/thermal-imaging-in-building-inspection-nmh6j | https://universe.roboflow.com/scanx-datasets/thermal-imaging-in-building-inspection-nmh6j | yes ("Dataset and Pre-Trained Model", YOLOv8) | ~137 | Moisture / moisture-detection (2) — building thermal, but moisture-only | CC BY 4.0 | unconfirmed |
| solveview/thermal-defects | https://universe.roboflow.com/solveview/thermal-defects | yes ("Dataset and Pre-Trained Model" + API) | ~2,121 | SOLAR-CELL thermal defects (NOT building — PV cell inspection) | unconfirmed | unconfirmed |
| cerejo/thermal-defects-e1irw | https://universe.roboflow.com/cerejo/thermal-defects-e1irw | yes (pre-trained model + API) | ~2,121 | SOLAR-CELL thermal defects (NOT building — PV cell inspection) | unconfirmed | unconfirmed |
| solar-panel-data-set/thermal-anomalies-jev7w | https://universe.roboflow.com/solar-panel-data-set/thermal-anomalies-jev7w | yes (pre-trained model + API) | ~1,013 | thermal anomalies/hotspots (PV-panel domain, true FLIR pseudocolor — transfer source, not building) | unconfirmed | unconfirmed |
| murtazakhan/thermal-anomaly-detection-1 | https://universe.roboflow.com/murtazakhan/thermal-anomaly-detection-1 | yes ("Dataset and Pre-Trained Model") | ~751 | thermal anomaly (class list unconfirmed) | unconfirmed | unconfirmed |
| builddef2/building-defect-on-walls | https://universe.roboflow.com/builddef2/building-defect-on-walls | unconfirmed (dataset; model unconfirmed) | ~472 | wall building defects incl. cracks/moisture (likely VISIBLE-light, not thermal) | unconfirmed | unconfirmed |
| university-of-ottawa-thermal-anomaly/thermal-anomaly-test-1 | https://universe.roboflow.com/university-of-ottawa-thermal-anomaly/thermal-anomaly-test-1 | dataset-only (model unconfirmed) | unconfirmed | thermal anomaly (building-envelope research; class list unconfirmed) | unconfirmed | unconfirmed |
| thermal-imaging-0hwfw/flir-data-set | https://universe.roboflow.com/thermal-imaging-0hwfw/flir-data-set | yes (pre-trained model, e.g. v10/v14) | ~11,492 | FLIR generic thermal classes (person/vehicle etc — NOT building defects; useful only as FLIR pretrain/backbone) | unconfirmed | unconfirmed |

Most directly on-target for BUILDING thermal defects: **idt/thermal-images-in-building-inspection** — its 6 classes (air infiltration, air leakage, delamination, hollow, insulation, moisture) map almost 1:1 onto our target defect taxonomy. Downside: only ~58 images (very small). **scanx-datasets/...-nmh6j** (~137, CC BY 4.0) is also genuine building-thermal but moisture-only (2 classes). IMPORTANT: the two "thermal-defects" projects (solveview, cerejo) are SOLAR-CELL inspection (~2,121 images each), NOT building — do not mistake them for building detectors. The solar-anomaly / generic-FLIR / Ottawa sets are best treated as transfer/pretraining sources for FLIR pseudocolor only.

Broader pools to mine for more rows: https://universe.roboflow.com/browse/infrared and https://universe.roboflow.com/search?q=class%3Athermal-imaging

## B) Weight download policy and the `inference` package

### (1) Can raw .pt weights be downloaded to convert to ONNX ourselves?

**Restricted, but possible on paid plans.** Per Roboflow docs (https://docs.roboflow.com/deploy/download-roboflow-model-weights):
- Raw `.pt` download is gated: "Manual weights download is only available for paid users on Core plans and certain Enterprise customers."
- The model must have been **trained on the Roboflow platform**, and availability also depends on **model architecture**.
- Mechanism: the "Download Weights" button on the platform, or the Python SDK `model.download()` function; the file is a `.pt` you can then convert (e.g., to ONNX).
- Roboflow explicitly "does not provide technical support for model weights used outside of the Roboflow Inference ecosystem" — so self-hosting an extracted `.pt` is officially unsupported.
- The `.deploy()` flow (https://blog.roboflow.com/upload-model-weights-yolov8/ , https://docs.roboflow.com/deploy/upload-custom-weights) is the REVERSE direction — uploading your own weights TO Roboflow — not a way to extract someone else's.

So, conditions where you get a convertible `.pt`:
1. **Paid Core/Enterprise** + the model was Roboflow-trained + supported architecture → `model.download()` / Download Weights button yields a `.pt`. (Note: for an arbitrary third-party Universe author's model you generally still cannot pull THEIR weights unless they made them downloadable; this path reliably applies to models YOU trained in your own Roboflow workspace.)
2. **Download the dataset** (YOLOv5/v8 PyTorch, COCO, VOC export via "Download this Dataset") and **train it yourself** locally → you own the `.pt` and export ONNX freely. Universal, plan-independent, and the only fully self-owned route for a third-party Universe project.

Bottom line: for a free-tier or third-party Universe project, assume you CANNOT extract a `.pt`; plan on **dataset-download + self-train** unless the author explicitly attached downloadable weights.

### (2) Does `inference` (`get_model`) run locally? API key? First-load download?

Sources: https://inference.roboflow.com/quickstart/run_a_model/ , https://inference.roboflow.com/quickstart/configure_api_key/ , https://inference.roboflow.com/using_inference/offline_weights_download/ , https://blog.roboflow.com/deploy-computer-vision-models-offline/

- **Runs locally:** Yes. Docs state `get_model()` "downloads model weights and runs inference locally" — for the native Python `inference` path, images are processed **on-device and are NOT sent to Roboflow's cloud**.
- **API key:** Yes for our case. "Fine-tuned models and Universe models require an API key." (Pre-trained alias models like `rfdetr-small` do not.) Pass via `get_model(model_id=..., api_key="...")` or the `ROBOFLOW_API_KEY` env var.
- **First-load download:** Yes. On first load the weights are downloaded from Roboflow and **cached locally** (default `/tmp/cache`, cleared on reboot — set `MODEL_CACHE_DIR` for persistence). After that initial fetch (which needs internet + the API key for the auth/license check) you can run **fully offline**.

Caveat for commercial deployment: the cached artifact is Roboflow's served runtime format, not a raw `.pt` you can re-train or freely re-export, and production still carries an API-key dependency for first fetch/auth.

## C) Recommendation (3 lines)

1. Best fit for a COMMERCIAL building thermal-defect model: **idt/thermal-images-in-building-inspection** (its 6 classes match our taxonomy exactly) supplemented by **scanx-datasets/thermal-imaging-in-building-inspection-nmh6j** to grow the very small image pool; verify both carry a commercial-permitting license (e.g., CC BY 4.0 / MIT) in-browser before use — treat license as unconfirmed = not clearable.
2. Use **solar-panel-data-set/thermal-anomalies-jev7w** (~1,013 FLIR images) and the generic **flir-data-set** (~11,492) only as FLIR pseudocolor PRETRAIN/transfer sources, not as building detectors.
3. Go the **download-dataset-and-train-ourselves** route, NOT download-weights: raw `.pt` extraction is gated behind paid Growth/Enterprise plans, and self-training from the exported dataset gives us a clean ONNX, full control of class mapping/taxonomy, and no API-key runtime dependency in the commercial product.
