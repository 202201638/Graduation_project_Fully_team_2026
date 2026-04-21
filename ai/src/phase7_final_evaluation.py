import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

from src.config import ARTIFACT_DIR

BASELINE_RESULTS_PATH = os.path.join(ARTIFACT_DIR, "phase3_baseline_results.json")
RETRAIN_RESULTS_PATH = os.path.join(ARTIFACT_DIR, "phase5_retrain_results.json")
EVALUATION_RESULTS_PATH = os.path.join(ARTIFACT_DIR, "phase7_final_evaluation.json")


@dataclass
class Row:
    model: str
    before: Optional[float]
    after: Optional[float]
    metric: str


def _safe_load(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _metric_for(model_name: str, record: Dict) -> Optional[float]:
    if not record:
        return None
    if isinstance(record, dict) and "metrics" in record and isinstance(record["metrics"], dict):
        record = record["metrics"]
    if isinstance(record, dict) and record.get("status") == "failed":
        return None
    try:
        if model_name == "yolo":
            raw = record.get("map50")
            return float(raw) if raw is not None else None
        if model_name in {"fasterrcnn", "retinanet"}:
            raw = record.get("recall")
            return float(raw) if raw is not None else None
        raw = record.get("auc")
        return float(raw) if raw is not None else None
    except Exception:
        return None


def run_phase7_final_evaluation():
    print("Phase 7: Final evaluation")
    baseline = _safe_load(BASELINE_RESULTS_PATH)
    retrain = _safe_load(RETRAIN_RESULTS_PATH)

    models = sorted(set(list(baseline.keys()) + list(retrain.keys())))
    if not models:
        models = ["yolo", "resnet50", "efficientnet_b0"]
    rows = []
    for m in models:
        before = _metric_for(m, baseline.get(m, {}))
        after = _metric_for(m, retrain.get(m, {}))
        metric = "mAP@0.5" if m == "yolo" else ("Recall" if m in {"fasterrcnn", "retinanet"} else "AUC")
        rows.append(Row(model=m, before=before, after=after, metric=metric))

    print("| Model | Metric | Before Optimization | After Optimization |")
    print("|-------|--------|---------------------|--------------------|")
    for r in rows:
        b = f"{r.before:.4f}" if r.before is not None else "-"
        a = f"{r.after:.4f}" if r.after is not None else "-"
        print(f"| {r.model} | {r.metric} | {b} | {a} |")

    det_rows = [r for r in rows if r.model in {"yolo", "fasterrcnn", "retinanet"}]
    cls_rows = [r for r in rows if r.model not in {"yolo", "fasterrcnn", "retinanet"}]

    best_det = max(det_rows, key=lambda x: x.after or -1e9) if det_rows else None
    best_cls = max(cls_rows, key=lambda x: x.after or -1e9) if cls_rows else None

    if best_det is not None:
        print(f"Best detection model: {best_det.model} ({best_det.metric}={best_det.after})")
    if best_cls is not None:
        print(f"Best classification model: {best_cls.model} ({best_cls.metric}={best_cls.after})")

    payload = {
        "rows": [r.__dict__ for r in rows],
        "best_detection": best_det.model if best_det is not None else None,
        "best_classification": best_cls.model if best_cls is not None else None,
    }
    with open(EVALUATION_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Phase 7 results saved to {EVALUATION_RESULTS_PATH}")
    return payload
