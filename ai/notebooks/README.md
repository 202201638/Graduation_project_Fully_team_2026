# Kaggle Notebooks - Per-Model Pipelines

Seven notebooks. Run `00` once, then run each model notebook independently. Each model
notebook runs **phases 3 -> 8** for one model and writes `artifacts/<model>_report.json`.

## Run order

1. **`00_prepare_dataset.ipynb`** - run once.
   - Add input: the **RSNA Pneumonia Detection Challenge** competition data.
   - Converts DICOM -> PNG (uniform CLAHE, no label leak) and builds the patient-wise,
     stratified `yolo_dataset/` (train/val/test).
   - Publish `/kaggle/working/yolo_dataset` as a Kaggle Dataset (e.g. `rsna-prepped-yolo-dataset`).

2. **The six model notebooks** - run each on its own (GPU on). Set `PREPPED_INPUT` to the
   dataset you published in step 1.
   - `01_resnet50.ipynb`, `02_densenet121.ipynb`, `03_efficientnet_b0.ipynb` (classification, 224px, Grad-CAM)
   - `04_yolov8.ipynb`, `05_fasterrcnn.ipynb` (detection, 640px, box overlays)
   - `06_ssdlite.ipynb` (detection, **SSDlite320 MobileNetV3**, ~2.2M params, 320px - the fast-to-train detector)

Each notebook is self-contained for training: baseline (phase 3) -> PSO/GWO/SA optimization
(phase 4) -> retrain with best params (phase 5) -> explainability (phase 6) -> final test-set
evaluation (phase 7) -> single-image demo (phase 8).

### Stronger nature-inspired re-run (no Phase 3)

Every model notebook ends with a **"Stronger nature-inspired search + retrain"** section. The
default Phase-4 search is deliberately cheap (`population=3, iterations=2, proxy_epochs=1`) and
its 1-epoch proxy is too noisy, so the "optimized" settings often lose to the baseline. That
section re-runs Phase 4 with a bigger budget and higher proxy fidelity, then fully retrains, and
**reads the committed Phase-3 baseline from `results/<model>_report.json`** for the before/after
comparison - so you only run the setup cell, then that section (no need to retrain the baseline).
It writes `artifacts/<model>_report_rerun.json` and only promotes the new weights if they beat the
baseline.

**One-stop option: `07_rerun_all.ipynb`.** Instead of opening each notebook, this single notebook does
the setup once and runs the stronger re-run for every model in a `MODELS` list (edit it to run a subset
per Kaggle session if you hit the time limit). Same outputs: `artifacts/<model>_report_rerun.json` +
`artifacts/checkpoints/<model>_rerun.pt`.

## Hand-back

After each notebook finishes, download from the **Output** tab:
- `artifacts/<model>_report.json` (architecture, all hyperparameters, full test metrics, confusion matrix, before/after, history)
- the checkpoint (`artifacts/checkpoints/<model>.pt`, or `yolo_best.pt`)

Plus, from the re-run section: `artifacts/<model>_report_rerun.json` and `artifacts/checkpoints/<model>_rerun.pt`.

Send the six `*_report.json` files (and the `*_report_rerun.json` files) back; they get integrated into one comparison table and the thesis discussion.

## What to expect (honest, leak-free numbers)

- **Classification** (ResNet50 / DenseNet121 / EfficientNet-B0): test **AUC ~ 0.82-0.92**.
  The old ~0.99-1.0 was a preprocessing leak (CLAHE applied only to pneumonia images), now fixed.
- **Detection** (YOLOv8n / Faster R-CNN / SSDlite): test **mAP@0.5 ~ 0.20-0.45** - this is the
  realistic range for RSNA pneumonia localization, not a defect. SSDlite is the lightest and
  fastest to train; expect it near the lower end of that range.

## Tuning for the Kaggle time limit

In each model notebook's run cell you can lower `EPOCHS`, `POPULATION`, `ITERATIONS`, or
`PROXY_EPOCHS` if a session approaches 12h. Faster R-CNN is the slowest. The defaults are tuned to fit a single GPU session.

## Backend

The classifier checkpoints train at 224px with ImageNet normalization - exactly what the
FastAPI backend already expects - so the new `*.pt` files drop into `Backend/model_assets/`
with no code change.
