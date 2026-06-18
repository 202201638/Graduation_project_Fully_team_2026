"""Per-model pipeline: run phases 3->8 for a SINGLE model and emit one
thesis-ready report JSON (architecture, baseline + optimized hyperparameters,
full test metrics, confusion matrix, before/after comparison, explainability,
demo). This is what each of the 6 Kaggle notebooks calls.
"""
import json
import os
import shutil
from typing import Dict, Optional

from src.config import ARTIFACT_DIR, CHECKPOINT_DIR, CLS_IMG_SIZE, IMG_SIZE, PROJECT_ROOT, SEED
from src.classification.train_resnet import train_resnet
from src.classification.train_densenet import train_densenet
from src.classification.train_efficientnet import train_efficientnet
from src.detection.train_fasterrcnn import train_fasterrcnn
from src.detection.train_ssdlite import train_ssdlite
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
    "ssdlite": {"family": "detection", "base": "SSDlite320 MobileNetV3-Large (COCO-pretrained)",
                "head": "SSDLiteClassificationHead(2 classes)", "input_size": 320, "primary_metric": "map50"},
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
    "ssdlite": {"lr": 3e-3, "batch_size": 8, "weight_decay": 5e-4},
}

# Epochs used for BOTH baseline and final runs (early stopping cuts these short),
# so before/after isolates the effect of the optimized hyperparameters.
_DEFAULT_EPOCHS: Dict[str, int] = {
    "resnet50": 12, "densenet121": 12, "efficientnet_b0": 12,
    "fasterrcnn": 12, "yolo": 35, "ssdlite": 30,
}

_CLS_TRAINERS = {
    "resnet50": train_resnet,
    "densenet121": train_densenet,
    "efficientnet_b0": train_efficientnet,
}
_DET_TRAINERS = {"fasterrcnn": train_fasterrcnn, "ssdlite": train_ssdlite}


def _train_one(
    model_name: str,
    params: Dict,
    epochs: int,
    checkpoint_path: Optional[str],
    run_tag: str,
    train_fraction: float = 1.0,
) -> Dict:
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
            fraction=train_fraction,
            base_weights=_YOLO_BASE_WEIGHTS.get(model_name, ""),
            model_label=model_name,
            run_name=f"{run_tag}_{model_name}",
        )
    # TorchVision detectors (Faster R-CNN, SSDlite): subsample train data via fraction.
    return _DET_TRAINERS[model_name](
        epochs=epochs,
        lr=float(params["lr"]),
        batch_size=int(params["batch_size"]),
        weight_decay=float(params["weight_decay"]),
        freeze_epochs=1,
        fraction=train_fraction,
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


def _load_baseline_metrics(model_name: str) -> Optional[Dict]:
    """Read the Phase-3 baseline metrics from a previously saved report so a re-run can
    compare before/after WITHOUT retraining the baseline. Checks the committed
    `results/` reports (shipped in the repo) and the working `artifacts/` reports."""
    candidates = [
        os.path.join(str(PROJECT_ROOT), "results", f"{model_name}_report.json"),
        os.path.join(ARTIFACT_DIR, f"{model_name}_report.json"),
        os.path.join(ARTIFACT_DIR, f"{model_name}_report_rerun.json"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                rep = json.load(f)
            base = (rep.get("phase3_baseline") or {}).get("metrics")
            if base:
                return base
        except Exception:
            continue
    return None


def rerun_optimization_and_retrain(
    model_name: str,
    *,
    population: int = 6,
    iterations: int = 3,
    proxy_epochs: int = 3,
    final_epochs: Optional[int] = None,
    proxy_train_batches: int = 120,
    proxy_eval_batches: int = 60,
    yolo_fraction: float = 0.3,
    final_fraction: float = 1.0,
) -> Dict:
    """Stronger nature-inspired search (Phase 4) + full retrain (Phase 5) for ONE model,
    WITHOUT retraining the Phase-3 baseline.

    The baseline metrics are loaded from the existing report JSON for the before/after
    comparison. The retrained model only replaces the deployed (canonical) checkpoint if
    it beats the baseline on the primary metric; otherwise the deployed model is left
    untouched (the honest "search did not help" outcome) while the re-run weights are
    still saved under `{model}_rerun.pt`. Writes `artifacts/{model}_report_rerun.json`.

    The stronger defaults raise the search budget AND the proxy fidelity (more epochs /
    more data per candidate) so the chosen hyperparameters actually transfer to a full
    retrain - the real fix for the weak Phase-4 results.
    """
    if model_name not in _ARCH:
        raise ValueError(f"Unknown model '{model_name}'. Choose from {list(_ARCH)}.")

    final_epochs = final_epochs or _DEFAULT_EPOCHS[model_name]
    metric_key = _ARCH[model_name]["primary_metric"]
    is_yolo = model_name in _YOLO_MODELS
    canonical_ckpt = (
        os.path.join(CHECKPOINT_DIR, f"{model_name}_best.pt")
        if is_yolo
        else os.path.join(CHECKPOINT_DIR, f"{model_name}.pt")
    )
    # Non-YOLO detectors/classifiers retrain to a dedicated re-run checkpoint first; YOLO
    # writes to runs/ and we read its model_path.
    rerun_ckpt = canonical_ckpt if is_yolo else os.path.join(CHECKPOINT_DIR, f"{model_name}_rerun.pt")

    baseline_metrics = _load_baseline_metrics(model_name)
    baseline_score = (baseline_metrics or {}).get(metric_key)

    report: Dict = {
        "model": model_name,
        "architecture": _ARCH[model_name],
        "dataset": {"name": "RSNA Pneumonia Detection Challenge", "seed": SEED, **_dataset_summary()},
        "config": {"epochs": final_epochs, "rerun": True, "phase3_retrained": False,
                   "final_fraction": final_fraction},
        "phase3_baseline": {"metrics": baseline_metrics,
                            "source": "loaded from existing report (NOT retrained)"},
    }

    # ---- Phase 4: stronger search (bigger budget + higher proxy fidelity) ----
    opt = optimize_model(
        model_name,
        population=population,
        iterations=iterations,
        quick_epochs=proxy_epochs,
        train_batches=proxy_train_batches,
        eval_batches=proxy_eval_batches,
        yolo_fraction=yolo_fraction,
    )
    best_params = {**_BASELINE[model_name], **opt.get("best_hyperparameters", {})}
    report["phase4_optimization"] = opt
    report["final_hyperparameters"] = best_params

    # ---- Phase 5: full retrain with the best hyperparameters ----
    final_metrics = _train_one(
        model_name, best_params, final_epochs, rerun_ckpt, "phase5_rerun", train_fraction=final_fraction
    )
    report["phase5_final"] = {"hyperparameters": best_params, "metrics": final_metrics}
    new_score = final_metrics.get(metric_key)

    # ---- Promote to the deployed checkpoint only if it beat (or matched) baseline ----
    beats_baseline = baseline_score is None or (new_score is not None and new_score >= baseline_score)
    promoted = False
    if is_yolo:
        src_pt = final_metrics.get("model_path")
        if beats_baseline and src_pt and os.path.exists(src_pt):
            os.makedirs(CHECKPOINT_DIR, exist_ok=True)
            shutil.copy(src_pt, canonical_ckpt)
            promoted = True
    elif beats_baseline and os.path.exists(rerun_ckpt):
        shutil.copy(rerun_ckpt, canonical_ckpt)
        promoted = True

    report["promotion"] = {
        "metric": metric_key,
        "baseline_score": baseline_score,
        "rerun_score": new_score,
        "promoted_to_canonical": promoted,
        "canonical_checkpoint": canonical_ckpt,
        "rerun_checkpoint": final_metrics.get("model_path") if is_yolo else rerun_ckpt,
        "note": (
            "Re-run model promoted (beat or matched baseline)." if promoted
            else "Re-run did NOT beat baseline; deployed checkpoint left unchanged - keep the baseline model."
        ),
    }

    explain_ckpt = canonical_ckpt if os.path.exists(canonical_ckpt) else rerun_ckpt

    # ---- Phase 6: explainability ----
    try:
        report["phase6_explainability"] = run_explainability_for_model(model_name, explain_ckpt)
    except Exception as exc:
        report["phase6_explainability"] = {"error": str(exc)}

    # ---- Phase 7: before/after (baseline loaded, not retrained) ----
    report["phase7_comparison"] = {
        "metric": metric_key,
        "before_optimization": baseline_score,
        "after_optimization": new_score,
        "eval_split": final_metrics.get("eval_split"),
        "phase3_retrained": False,
    }

    # ---- Phase 8: demo ----
    try:
        report["phase8_demo"] = run_demo_for_model(model_name, explain_ckpt)
    except Exception as exc:
        report["phase8_demo"] = {"error": str(exc)}

    report_path = os.path.join(ARTIFACT_DIR, f"{model_name}_report_rerun.json")
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    report["report_path"] = report_path
    print_report_summary(report)
    print(f"\nSaved {model_name} RE-RUN report to {report_path}", flush=True)
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
