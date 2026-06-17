"""Per-model pipeline: run phases 3->8 for a SINGLE model and emit one
thesis-ready report JSON (architecture, baseline + optimized hyperparameters,
full test metrics, confusion matrix, before/after comparison, explainability,
demo). This is what each of the 6 Kaggle notebooks calls.
"""
import json
import os
import shutil
from typing import Dict, Optional

from src.config import ARTIFACT_DIR, CHECKPOINT_DIR, CLS_IMG_SIZE, IMG_SIZE, SEED
from src.classification.train_resnet import train_resnet
from src.classification.train_densenet import train_densenet
from src.classification.train_efficientnet import train_efficientnet
from src.detection.train_fasterrcnn import train_fasterrcnn
from src.detection.train_yolo import train_yolo
from src.phase4_optimization import optimize_model, CLASSIFICATION_MODELS
from src.phase6_explainability import run_explainability_for_model
from src.phase8_demo import run_demo_for_model


_ARCH: Dict[str, Dict] = {
    "resnet50": {"family": "classification", "base": "ResNet50 (ImageNet-pretrained)",
                 "head": "Dropout + Linear(2048->2)", "input_size": CLS_IMG_SIZE, "primary_metric": "auc"},
    "densenet121": {"family": "classification", "base": "DenseNet121 (ImageNet-pretrained)",
                    "head": "Dropout + Linear(1024->2)", "input_size": CLS_IMG_SIZE, "primary_metric": "auc"},
    "efficientnet_b0": {"family": "classification", "base": "EfficientNet-B0 (ImageNet-pretrained)",
                        "head": "Dropout + Linear(1280->2)", "input_size": CLS_IMG_SIZE, "primary_metric": "auc"},
    "yolo": {"family": "detection", "base": "YOLOv8n (Ultralytics)",
             "head": "anchor-free detect head", "input_size": IMG_SIZE, "primary_metric": "map50"},
    "fasterrcnn": {"family": "detection", "base": "Faster R-CNN ResNet50-FPN (pretrained)",
                   "head": "FastRCNNPredictor(2 classes)", "input_size": IMG_SIZE, "primary_metric": "map50"},
}

# YOLO-family (Ultralytics) models share one training/checkpoint/explain path.
_YOLO_MODELS = {"yolo"}
# Base weights per YOLO variant ("" => resolve the default YOLOv8n local/yaml).
_YOLO_BASE_WEIGHTS = {"yolo": ""}

# Unoptimized defaults used for the baseline (phase 3) run.
_BASELINE: Dict[str, Dict] = {
    "resnet50": {"lr": 1e-4, "batch_size": 32, "dropout": 0.3, "weight_decay": 1e-4},
    "densenet121": {"lr": 1e-4, "batch_size": 32, "dropout": 0.3, "weight_decay": 1e-4},
    "efficientnet_b0": {"lr": 1e-4, "batch_size": 32, "dropout": 0.3, "weight_decay": 1e-4},
    "yolo": {"lr": 1e-3, "batch_size": 16, "weight_decay": 5e-4, "anchor_size": 16},
    "fasterrcnn": {"lr": 5e-3, "batch_size": 4, "weight_decay": 5e-4},
}

# Epochs used for BOTH baseline and final runs (early stopping cuts these short),
# so before/after isolates the effect of the optimized hyperparameters.
_DEFAULT_EPOCHS: Dict[str, int] = {
    "resnet50": 12, "densenet121": 12, "efficientnet_b0": 12,
    "fasterrcnn": 12, "yolo": 35,
}

_CLS_TRAINERS = {
    "resnet50": train_resnet,
    "densenet121": train_densenet,
    "efficientnet_b0": train_efficientnet,
}
_DET_TRAINERS = {"fasterrcnn": train_fasterrcnn}


def _train_one(model_name: str, params: Dict, epochs: int, checkpoint_path: Optional[str], run_tag: str) -> Dict:
    if model_name in CLASSIFICATION_MODELS:
        return _CLS_TRAINERS[model_name](
            epochs=epochs,
            lr=float(params["lr"]),
            batch_size=int(params["batch_size"]),
            dropout=float(params.get("dropout", 0.3)),
            weight_decay=float(params["weight_decay"]),
            freeze_epochs=2,
            checkpoint_path=checkpoint_path,
        )
    if model_name in _YOLO_MODELS:
        return train_yolo(
            epochs=epochs,
            lr=float(params["lr"]),
            batch_size=int(params["batch_size"]),
            weight_decay=float(params["weight_decay"]),
            anchor_size=int(params.get("anchor_size", 16)),
            base_weights=_YOLO_BASE_WEIGHTS.get(model_name, ""),
            model_label=model_name,
            run_name=f"{run_tag}_{model_name}",
        )
    return _DET_TRAINERS[model_name](
        epochs=epochs,
        lr=float(params["lr"]),
        batch_size=int(params["batch_size"]),
        weight_decay=float(params["weight_decay"]),
        freeze_epochs=1,
        checkpoint_path=checkpoint_path,
    )


def _dataset_summary() -> Dict:
    path = os.path.join(ARTIFACT_DIR, "phase2_yolo_dataset_summary.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def run_model_pipeline(
    model_name: str,
    *,
    epochs: Optional[int] = None,
    run_baseline: bool = True,
    optimize: bool = True,
    population: int = 3,
    iterations: int = 2,
    proxy_epochs: int = 1,
) -> Dict:
    if model_name not in _ARCH:
        raise ValueError(f"Unknown model '{model_name}'. Choose from {list(_ARCH)}.")

    epochs = epochs or _DEFAULT_EPOCHS[model_name]
    is_cls = model_name in CLASSIFICATION_MODELS
    canonical_ckpt = (
        os.path.join(CHECKPOINT_DIR, f"{model_name}_best.pt")
        if model_name in _YOLO_MODELS
        else os.path.join(CHECKPOINT_DIR, f"{model_name}.pt")
    )

    report: Dict = {
        "model": model_name,
        "architecture": _ARCH[model_name],
        "dataset": {"name": "RSNA Pneumonia Detection Challenge", "seed": SEED, **_dataset_summary()},
        "config": {"epochs": epochs, "optimized": optimize},
    }

    # ---- Phase 3: baseline (unoptimized defaults) ----
    baseline_metrics = None
    if run_baseline:
        baseline_ckpt = None if model_name in _YOLO_MODELS else os.path.join(CHECKPOINT_DIR, f"{model_name}_baseline.pt")
        baseline_metrics = _train_one(model_name, _BASELINE[model_name], epochs, baseline_ckpt, "phase3")
        report["phase3_baseline"] = {"hyperparameters": _BASELINE[model_name], "metrics": baseline_metrics}

    # ---- Phase 4: optimization ----
    if optimize:
        opt = optimize_model(model_name, population=population, iterations=iterations, quick_epochs=proxy_epochs)
        best_params = {**_BASELINE[model_name], **opt.get("best_hyperparameters", {})}
        report["phase4_optimization"] = opt
    else:
        best_params = dict(_BASELINE[model_name])
    report["final_hyperparameters"] = best_params

    # ---- Phase 5: final retrain with best hyperparameters ----
    final_metrics = _train_one(model_name, best_params, epochs, canonical_ckpt, "phase5")
    report["phase5_final"] = {"hyperparameters": best_params, "metrics": final_metrics}

    # YOLO: copy best.pt to the canonical checkpoint name for backend/explain/demo
    if model_name in _YOLO_MODELS:
        src_pt = final_metrics.get("model_path")
        if src_pt and os.path.exists(src_pt):
            os.makedirs(CHECKPOINT_DIR, exist_ok=True)
            shutil.copy(src_pt, canonical_ckpt)

    # ---- Phase 6: explainability ----
    try:
        report["phase6_explainability"] = run_explainability_for_model(model_name, canonical_ckpt)
    except Exception as exc:
        report["phase6_explainability"] = {"error": str(exc)}

    # ---- Phase 7: before/after comparison ----
    metric_key = _ARCH[model_name]["primary_metric"]
    report["phase7_comparison"] = {
        "metric": metric_key,
        "before_optimization": (baseline_metrics or {}).get(metric_key),
        "after_optimization": final_metrics.get(metric_key),
        "eval_split": final_metrics.get("eval_split"),
    }

    # ---- Phase 8: demo ----
    try:
        report["phase8_demo"] = run_demo_for_model(model_name, canonical_ckpt)
    except Exception as exc:
        report["phase8_demo"] = {"error": str(exc)}

    report_path = os.path.join(ARTIFACT_DIR, f"{model_name}_report.json")
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    report["report_path"] = report_path
    print_report_summary(report)
    print(f"\nSaved {model_name} report to {report_path}", flush=True)
    return report


def print_report_summary(report: Dict) -> None:
    model = report["model"]
    arch = report["architecture"]
    final = report.get("phase5_final", {}).get("metrics", {})
    comp = report.get("phase7_comparison", {})
    print("\n" + "=" * 60)
    print(f"MODEL REPORT: {model}")
    print("=" * 60)
    print(f"Architecture : {arch['base']} | input {arch['input_size']} | {arch['family']}")
    print(f"Parameters   : {final.get('num_parameters', 'NA'):,}" if isinstance(final.get("num_parameters"), int) else f"Parameters   : {final.get('num_parameters', 'NA')}")
    print(f"Best hyperparams: {report.get('final_hyperparameters')}")
    print(f"Eval split   : {final.get('eval_split')}")
    if arch["family"] == "classification":
        print(f"Accuracy={final.get('accuracy')}, Precision={final.get('precision')}, "
              f"Recall={final.get('recall')}, F1={final.get('f1')}, AUC={final.get('auc')}")
        print(f"Confusion matrix [[TN,FP],[FN,TP]]: {final.get('confusion_matrix')}")
    else:
        print(f"mAP@0.5={final.get('map50')}, mAP@0.5:0.95={final.get('map')}, Recall={final.get('recall')}")
    print(f"Before->After ({comp.get('metric')}): {comp.get('before_optimization')} -> {comp.get('after_optimization')}")
    print("=" * 60 + "\n")
