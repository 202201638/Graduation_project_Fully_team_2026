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
6. **Explainability** - Grad-CAM, Integrated Gradients, and GradientSHAP for classifiers; predicted-box overlays plus Eigen-CAM for detectors.
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

The optimized hyperparameters per model (and the per-algorithm results) are recorded in each
report's `phase4_optimization` and `final_hyperparameters`.

### Search spaces (phase 4)

- **Classification**: lr [1e-5, 1e-3], batch_size [16, 48], dropout [0.1, 0.6], weight_decay [1e-7, 1e-2].
- **YOLOv8n**: lr [1e-4, 5e-3], batch_size [8, 24], weight_decay [1e-5, 5e-3], anchor_size [8, 32].
- **Faster R-CNN**: lr [5e-4, 1e-2], batch_size [2, 6], weight_decay [1e-5, 5e-3].

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

## 8. Results: measured performance and model selection

All five models have been run end-to-end.
All numbers are on the held-out **test** split (20%, patient-wise, seed 42; 4,135 normal / 1,202
pneumonia). "Deployed" marks the checkpoint shipped to the web app.

### 8.1 Classification (whole-image)

| Model | Config | AUC | Accuracy | Precision | Recall (Sens.) | Specificity | F1 | Params | Deployed |
|---|---|---|---|---|---|---|---|---|---|
| ResNet50 | baseline | 0.881 | 0.805 | 0.548 | 0.759 | 0.818 | 0.636 | 23.5M | |
| ResNet50 | optimized | **0.884** | 0.810 | 0.557 | 0.761 | 0.824 | 0.643 | 23.5M | **yes** |
| DenseNet121 | baseline | **0.883** | 0.802 | 0.542 | 0.785 | 0.807 | 0.641 | 7.0M | **yes** |
| DenseNet121 | optimized | 0.880 | 0.752 | 0.472 | 0.851 | 0.723 | 0.607 | 7.0M | |
| EfficientNet-B0 | baseline | **0.886** | 0.815 | 0.566 | 0.765 | 0.830 | 0.651 | 4.0M | **yes** |
| EfficientNet-B0 | optimized | 0.874 | 0.734 | 0.453 | 0.884 | 0.690 | 0.599 | 4.0M | |

### 8.2 Detection (localization)

| Model | Config | mAP@0.5 | mAP@[.5:.95] | Recall@0.5 | Precision | Params | Deployed |
|---|---|---|---|---|---|---|---|
| YOLOv8n | baseline | **0.346** | 0.138 | 0.382 | 0.396 | 3.0M | **yes** |
| YOLOv8n | optimized | 0.340 | 0.137 | 0.377 | 0.404 | 3.0M | |
| Faster R-CNN | baseline | **0.381** | 0.124 | 0.812 | - | 41.3M | **yes** |
| Faster R-CNN | optimized | 0.175 | 0.046 | 0.792 | - | 41.3M | |

### 8.3 Key finding: optimization vs a well-tuned baseline

The phase-4 metaheuristic search ran on a deliberately cheap proxy (1 epoch, 30 eval batches) so
it fits a Kaggle session. That proxy is **too noisy to rank configurations reliably**: it selected
high-learning-rate, high-dropout settings that improved the proxy score but **hurt** the full
retrain for four of the five models. The clearest case is Faster R-CNN, where the optimized
learning rate (~0.0099) destabilized training and halved mAP@0.5 (0.381 -> 0.175); for DenseNet121
and EfficientNet-B0 the optimized models traded precision for recall and lost AUC. Only ResNet50
improved, and only marginally (+0.003 AUC).

We therefore select the **validation-best** checkpoint per model (select on validation, report on
test): ResNet50 keeps its optimized configuration; the others keep the baseline. This is itself a
defensible thesis result: with a strong transfer-learning baseline, lightweight proxy-based
hyperparameter search did not beat careful defaults, and **validation-based model selection** is
what guarantees we never ship a regression.

### 8.4 Best models and deployment decision

- **Best classifier: EfficientNet-B0** (AUC 0.886, F1 0.651, only 4.0M parameters - the smallest
  and fastest, ideal for serving).
- **Best detector: Faster R-CNN** (mAP@0.5 0.381, recall 0.812) - chosen as the web app's
  **default** because bounding boxes give the clearest localization for a clinician. Grad-CAM,
  Integrated Gradients, and GradientSHAP heatmaps are generated for the classifier options, and
  Eigen-CAM for the detectors, to add soft localization (see 8.6).

### 8.5 Calibration against published work (defensibility)

- **Classification AUC ~0.88 is honest and competitive.** The well-known CheXNet (DenseNet121)
  reported AUC 0.768 for pneumonia on ChestX-ray14. Papers reporting ~0.98 on RSNA typically use
  the easier two-class split (lung-opacity vs normal) that drops the hard "abnormal but no opacity"
  negatives; our binary `Target` task keeps them, so ~0.88 is the harder, honest number.
- **Detection mAP@0.5 ~0.34-0.38 matches the literature.** Published RSNA detectors land ~0.32
  (YOLOv3) to ~0.39 (a heavily engineered Faster R-CNN with custom backbone + CLAHE + Soft-NMS);
  GeminiNet reports AP@0.5 0.4575. Our Faster R-CNN at 0.381 is on par with engineered results for
  this architecture. The often-quoted challenge "top score 0.25" is on the stricter averaged-IoU
  (0.4-0.75) metric, which corresponds to our mAP@[.5:.95] ~0.12-0.14.

Conclusion: the models sit at the realistic published ceiling for this dataset; the remaining gap
to "perfect" reflects dataset difficulty and label noise, not a training defect. A further
hyperparameter re-run is not expected to move the headline metrics materially.

### 8.6 Explainability (XAI)

Every model exposes visual evidence for its output, generated in phase 6 and surfaced live in the
web app on each upload. All methods are implemented natively (torch / numpy / cv2), so they add no
heavy dependencies and run in a few seconds on CPU (instant on GPU).

- **Classifiers (ResNet50, DenseNet121, EfficientNet-B0)** - four saliency maps, each targeting the
  pneumonia class (index 1):
  - **Grad-CAM** - gradient-weighted activations of the last conv block; coarse "where the model looked".
  - **Integrated Gradients** - per-pixel attribution accumulated along a path from a black baseline to
    the image (axiomatic, sharper than Grad-CAM).
  - **GradientSHAP** - the gradient-based SHAP estimator; (input - baseline) * gradient averaged over
    several noisy, randomly interpolated samples.
  - **Score-CAM** - gradient-free, class-discriminative CAM: each activation channel is upsampled,
    used to mask the input, and weighted by the resulting pneumonia score (top-K channels for speed).
    A different paradigm (perturbation/activation-masking) from the three gradient methods above.
- **Detectors (YOLOv8n, Faster R-CNN)** - the predicted bounding boxes are the primary
  explanation, complemented by two gradient-free maps:
  - **Eigen-CAM** - the first principal component of a backbone feature map (activation-based,
    target-free, one forward pass).
  - **Occlusion sensitivity** - blank each cell of a coarse grid and measure the drop in the top
    detection confidence; larger drops mark regions the detection depended on. Uniform across YOLO
    and Faster R-CNN.
  IG and GradientSHAP are not used on detectors because they require a single differentiable class
  score that the detection heads (NMS, ultralytics wrapper) do not expose cleanly; Eigen-CAM and
  Occlusion are the standard fast analogues.

Caveat for the defense: these are saliency methods (where the network responded), not causal or
clinical segmentations of disease. They are decision support, not a diagnosis.

## 9. Limitations and future work

- Binary pneumonia only (no multi-pathology).
- Detection mAP is bounded by dataset difficulty and box-label noise.
- A held-out external dataset would strengthen generalization claims.
- Possible extensions: model ensembling, test-time augmentation, higher-resolution detection,
  calibration of classifier probabilities.
