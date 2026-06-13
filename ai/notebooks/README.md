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
   - `04_yolov8.ipynb`, `05_fasterrcnn.ipynb`, `06_retinanet.ipynb` (detection, 640px, box overlays)

Each notebook is self-contained for training: baseline (phase 3) -> PSO/GWO/SA optimization
(phase 4) -> retrain with best params (phase 5) -> explainability (phase 6) -> final test-set
evaluation (phase 7) -> single-image demo (phase 8).

## Hand-back

After each notebook finishes, download from the **Output** tab:
- `artifacts/<model>_report.json` (architecture, all hyperparameters, full test metrics, confusion matrix, before/after, history)
- the checkpoint (`artifacts/checkpoints/<model>.pt`, or `yolo_best.pt`)

Send the six `*_report.json` files back; they get integrated into one comparison table and the thesis discussion.

## What to expect (honest, leak-free numbers)

- **Classification** (ResNet50 / DenseNet121 / EfficientNet-B0): test **AUC ~ 0.82-0.92**.
  The old ~0.99-1.0 was a preprocessing leak (CLAHE applied only to pneumonia images), now fixed.
- **Detection** (YOLO / Faster R-CNN / RetinaNet): test **mAP@0.5 ~ 0.20-0.45** - this is the
  realistic range for RSNA pneumonia localization, not a defect.

## Tuning for the Kaggle time limit

In each model notebook's run cell you can lower `EPOCHS`, `POPULATION`, `ITERATIONS`, or
`PROXY_EPOCHS` if a session approaches 12h. Detection (especially Faster R-CNN / RetinaNet)
is the slowest; the defaults are tuned to fit a single GPU session.

## Backend

The classifier checkpoints train at 224px with ImageNet normalization - exactly what the
FastAPI backend already expects - so the new `*.pt` files drop into `Backend/model_assets/`
with no code change.
