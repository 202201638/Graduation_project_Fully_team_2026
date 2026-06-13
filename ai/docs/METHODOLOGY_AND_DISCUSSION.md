# Methodology and Discussion Notes

Reference material for the thesis. Covers what the pipeline does, the critical correctness
fix, per-model configuration, and how to read the metrics. Each notebook also emits a machine
-readable `artifacts/<model>_report.json` with the exact numbers for its model.

## 1. Problem and dataset

- **Task**: detect pneumonia in chest X-rays, as both whole-image **classification** and
  region **detection** (localization).
- **Dataset**: RSNA Pneumonia Detection Challenge, 26,684 DICOM chest X-rays. Patient-level
  class balance ~ 2.2 : 1 (normal : pneumonia).
- **Split**: patient-wise (no patient in two splits), stratified by label, 60 / 20 / 20
  train / val / test, fixed seed 42. Metrics are reported on the held-out **test** split.

## 2. Critical correctness fix (key discussion point)

The earlier results showed classification AUC of ~0.99-1.0. This was **not** real skill; it was
a **preprocessing data leak**. During dataset construction, an augmentation pipeline that
included CLAHE contrast enhancement (`p=1.0`, always on) was applied **only to pneumonia-positive
images**, while normal images were written raw. The two classes therefore carried a trivial
contrast signature, and the classifiers learned "was CLAHE applied?" rather than any pneumonia
pattern.

**Fix**: preprocessing is now identical for every image regardless of label (CLAHE applied
uniformly to all images at conversion time), and all augmentation is moved to **on-the-fly,
train-split-only** transforms that are class-agnostic. After the fix, classification AUC lands
in the realistic ~0.82-0.92 range - lower headline numbers, but honest and defensible.

This is a textbook example of preprocessing-induced label leakage and is worth presenting in the
discussion: how it was detected (implausibly perfect AUC), the root cause, and the corrected
methodology.

## 3. Pipeline (8 phases)

1. **Convert** DICOM -> PNG with robust percentile normalization + uniform CLAHE.
2. **Build** the YOLO-format dataset (patient-wise stratified split, leak-free).
3. **Baseline** training with default (unoptimized) hyperparameters.
4. **Optimization** of hyperparameters with three nature-inspired algorithms (PSO, GWO, SA).
5. **Retrain** with the best hyperparameters found.
6. **Explainability** - Grad-CAM for classifiers, predicted-box overlays for detectors.
7. **Final evaluation** - before vs after on the test split.
8. **Demo** - single-image inference.

Each of the six models is taken through phases 3-8 independently (one Kaggle notebook each).

## 4. Models, architectures, and hyperparameters

All models use ImageNet-pretrained backbones (transfer learning).

| Model | Family | Input | Backbone / head | Baseline hyperparameters |
|---|---|---|---|---|
| ResNet50 | classification | 224 | ResNet50 + Dropout->Linear(2048->2) | lr 1e-4, bs 32, dropout 0.3, wd 1e-4 |
| DenseNet121 | classification | 224 | DenseNet121 + Dropout->Linear(1024->2) | lr 1e-4, bs 32, dropout 0.3, wd 1e-4 |
| EfficientNet-B0 | classification | 224 | EfficientNet-B0 + Dropout->Linear(1280->2) | lr 1e-4, bs 32, dropout 0.3, wd 1e-4 |
| YOLOv8n | detection | 640 | Ultralytics YOLOv8 nano (anchor-free) | lr 1e-3, bs 16, wd 5e-4 |
| Faster R-CNN | detection | 640 | ResNet50-FPN + FastRCNNPredictor(2) | lr 5e-3, bs 4, wd 5e-4, SGD m=0.9 |
| RetinaNet | detection | 640 | ResNet50-FPN + focal-loss head(2) | lr 5e-3, bs 4, wd 5e-4, SGD m=0.9 |

The optimized hyperparameters per model (and the per-algorithm results) are recorded in each
report's `phase4_optimization` and `final_hyperparameters`.

### Search spaces (phase 4)

- **Classification**: lr [1e-5, 1e-3], batch_size [16, 48], dropout [0.1, 0.6], weight_decay [1e-7, 1e-2].
- **YOLO**: lr [1e-4, 5e-3], batch_size [8, 24], weight_decay [1e-5, 5e-3], anchor_size [8, 32].
- **Faster R-CNN / RetinaNet**: lr [5e-4, 1e-2], batch_size [2, 6], weight_decay [1e-5, 5e-3].

## 5. Training methodology (what prevents over/underfitting)

- **Class imbalance**: class-weighted cross-entropy for classifiers (inverse-frequency weights).
- **Augmentation** (train split only, on-the-fly): classification = horizontal flip, small
  rotation, color jitter; detection = box-aware horizontal flip + photometric jitter; YOLO uses
  its built-in mosaic/HSV/flip pipeline.
- **Normalization**: ImageNet mean/std for classifiers (matches the serving backend).
- **LR schedule**: ReduceLROnPlateau (classification) / linear warmup + cosine decay (detection)
  / cosine (YOLO).
- **Early stopping**: on validation AUC (classification) or mAP@0.5 (detection); the best
  checkpoint is restored before final evaluation.
- **Mixed precision (AMP)** on GPU for speed/memory.
- **Transfer learning**: backbone is frozen for the first 1-2 epochs (head warmup), then unfrozen.
- **RetinaNet stability**: target sanitization + gradient clipping (max-norm 5.0); the previous
  recall = 0.0 was caused by too few epochs and no warmup, both now addressed.

Each report includes the per-epoch `history` (train/val loss and metric) so the train-vs-val
curves can be shown to argue the models are neither over- nor under-fit.

## 6. Optimization methodology (phase 4)

Three nature-inspired metaheuristics are run and the best result across them is kept:
- **PSO** (Particle Swarm Optimization)
- **GWO** (Grey Wolf Optimizer)
- **SA** (Simulated Annealing)

Each candidate is scored with a fast **proxy** (few epochs / capped batches / data fraction) so
the search fits a Kaggle session; the winning hyperparameters are then used for full retraining
in phase 5. Per-algorithm best scores are stored under `phase4_optimization.algorithms`, which
supports a PSO-vs-GWO-vs-SA comparison in the discussion.

## 7. Metrics and how to read them

- **Classification**: Accuracy, Precision, Recall, F1, **AUC** (primary), plus the confusion
  matrix `[[TN, FP], [FN, TP]]`. On an imbalanced test set, prefer AUC and F1 over raw accuracy.
- **Detection**: **mAP@0.5** (primary), mAP@0.5:0.95, Recall@0.5, Precision.

**Honest expected ranges after the fix**: classification AUC ~0.82-0.92; detection mAP@0.5
~0.20-0.45 (RSNA localization is inherently hard - even strong public solutions sit near ~0.25 mAP).

## 8. Limitations and future work

- Binary pneumonia only (no multi-pathology).
- Detection mAP is bounded by dataset difficulty and box-label noise.
- A held-out external dataset would strengthen generalization claims.
- Possible extensions: model ensembling, test-time augmentation, higher-resolution detection,
  calibration of classifier probabilities.
