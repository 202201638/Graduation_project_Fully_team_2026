"""Phase 4: nature-inspired hyperparameter optimization for ALL six models.

Each candidate is scored with a fast PROXY (few epochs / capped batches / data
fraction) so the search fits a Kaggle session, then the winning hyperparameters
are used for full retraining in Phase 5. PSO, GWO and SA are all run so the thesis
can compare the algorithms; the best across them is kept.
"""
import json
import os
from typing import Callable, Dict, List, Tuple

from src.classification.train_densenet import train_densenet
from src.classification.train_efficientnet import train_efficientnet
from src.classification.train_resnet import train_resnet
from src.config import ARTIFACT_DIR
from src.detection.train_fasterrcnn import train_fasterrcnn
from src.detection.train_yolo import train_yolo
from src.optimization.algorithms import (
    SearchDimension,
    gwo_optimize,
    pso_optimize,
    sa_optimize,
)

BEST_PARAMS_PATH = os.path.join(ARTIFACT_DIR, "phase4_best_hyperparameters.json")

CLASSIFICATION_MODELS = {"resnet50", "densenet121", "efficientnet_b0"}
DETECTION_MODELS = {"yolo", "yolo11", "fasterrcnn"}
YOLO_MODELS = {"yolo", "yolo11"}
_YOLO_BASE_WEIGHTS = {"yolo": "", "yolo11": "yolo11m.pt"}

# Per-model search spaces
_SEARCH_SPACES: Dict[str, List[SearchDimension]] = {
    "yolo": [
        SearchDimension("lr", 1e-4, 5e-3, "float"),
        SearchDimension("batch_size", 8, 24, "int"),
        SearchDimension("weight_decay", 1e-5, 5e-3, "float"),
        SearchDimension("anchor_size", 8, 32, "int"),
    ],
    "yolo11": [
        SearchDimension("lr", 1e-4, 5e-3, "float"),
        SearchDimension("batch_size", 8, 16, "int"),
        SearchDimension("weight_decay", 1e-5, 5e-3, "float"),
        SearchDimension("anchor_size", 8, 32, "int"),
    ],
    "fasterrcnn": [
        SearchDimension("lr", 5e-4, 1e-2, "float"),
        SearchDimension("batch_size", 2, 6, "int"),
        SearchDimension("weight_decay", 1e-5, 5e-3, "float"),
    ],
}
_CLS_SPACE = [
    SearchDimension("lr", 1e-5, 1e-3, "float"),
    SearchDimension("batch_size", 16, 48, "int"),
    SearchDimension("dropout", 0.1, 0.6, "float"),
    SearchDimension("weight_decay", 1e-7, 1e-2, "float"),
]


def _save_json(path: str, data: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _load_json(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _proxy_score_classification(model_name: str, params: Dict[str, float], quick_epochs: int, eval_batches: int) -> float:
    trainers = {
        "resnet50": train_resnet,
        "densenet121": train_densenet,
        "efficientnet_b0": train_efficientnet,
    }
    try:
        metrics = trainers[model_name](
            epochs=quick_epochs,
            lr=float(params["lr"]),
            batch_size=int(params["batch_size"]),
            dropout=float(params["dropout"]),
            weight_decay=float(params["weight_decay"]),
            checkpoint_path=None,        # proxy: do not overwrite real checkpoint
            eval_on_test=False,          # proxy: score on val
            max_eval_batches=eval_batches,
        )
        return float(metrics.get("auc", 0.0))
    except Exception as exc:
        print(f"[Phase4] {model_name} candidate failed {params}: {exc}", flush=True)
        return 0.0


def _proxy_score_detection(
    model_name: str, params: Dict[str, float], quick_epochs: int, train_batches: int, eval_batches: int, fraction: float
) -> float:
    try:
        if model_name in YOLO_MODELS:
            metrics = train_yolo(
                epochs=max(2, quick_epochs + 1),
                lr=float(params["lr"]),
                batch_size=int(params["batch_size"]),
                weight_decay=float(params["weight_decay"]),
                anchor_size=int(params["anchor_size"]),
                patience=max(2, quick_epochs + 1),
                fraction=fraction,
                eval_test=False,
                base_weights=_YOLO_BASE_WEIGHTS.get(model_name, ""),
                model_label=model_name,
                run_name=f"phase4_{model_name}",
            )
            return float(metrics.get("map50", 0.0))

        metrics = train_fasterrcnn(
            epochs=quick_epochs,
            lr=float(params["lr"]),
            batch_size=int(params["batch_size"]),
            weight_decay=float(params["weight_decay"]),
            checkpoint_path=None,        # proxy: no checkpoint
            freeze_epochs=0,             # proxy: let everything move quickly
            eval_on_test=False,
            max_train_batches=train_batches,
            max_eval_batches=eval_batches,
        )
        score = float(metrics.get("map50", 0.0))
        return score if score > 0 else float(metrics.get("recall", 0.0))
    except Exception as exc:
        print(f"[Phase4] {model_name} candidate failed {params}: {exc}", flush=True)
        return 0.0


def _run_all_algorithms(
    objective: Callable[[Dict[str, float]], float],
    dims: List[SearchDimension],
    population: int,
    iterations: int,
) -> Tuple[Dict[str, float], float, Dict[str, Dict]]:
    algo_results: Dict[str, Dict] = {}

    best_params, best_score = pso_optimize(objective, dims, population=population, iterations=iterations)
    algo_results["PSO"] = {"best_params": best_params, "best_score": best_score}

    params, score = gwo_optimize(objective, dims, population=population, iterations=iterations)
    algo_results["GWO"] = {"best_params": params, "best_score": score}
    if score > best_score:
        best_params, best_score = params, score

    params, score = sa_optimize(objective, dims, iterations=max(8, population * iterations))
    algo_results["SA"] = {"best_params": params, "best_score": score}
    if score > best_score:
        best_params, best_score = params, score

    return best_params, best_score, algo_results


def optimize_model(
    model_name: str,
    population: int = 3,
    iterations: int = 2,
    quick_epochs: int = 1,
    train_batches: int = 60,
    eval_batches: int = 30,
    yolo_fraction: float = 0.15,
) -> Dict:
    """Run PSO/GWO/SA for a single model and persist the best hyperparameters.
    Returns the result record for this model."""
    print(f"Phase 4: optimizing {model_name} (population={population}, iterations={iterations}, proxy_epochs={quick_epochs})", flush=True)

    is_classification = model_name in CLASSIFICATION_MODELS
    dims = _CLS_SPACE if is_classification else _SEARCH_SPACES[model_name]

    if is_classification:
        objective = lambda p, m=model_name: _proxy_score_classification(m, p, quick_epochs, eval_batches)
        score_name = "auc"
        task = "classification"
    else:
        objective = lambda p, m=model_name: _proxy_score_detection(
            m, p, quick_epochs, train_batches, eval_batches, yolo_fraction
        )
        score_name = "map50"
        task = "detection"

    best_params, best_score, algo_results = _run_all_algorithms(objective, dims, population, iterations)
    record = {
        "task": task,
        "score_name": score_name,
        "best_score": best_score,
        "best_hyperparameters": best_params,
        "algorithms": algo_results,
        "search_budget": {
            "population": population,
            "iterations": iterations,
            "proxy_epochs": quick_epochs,
            "proxy_train_batches": None if is_classification else train_batches,
            "proxy_eval_batches": eval_batches,
            "yolo_fraction": yolo_fraction if model_name in YOLO_MODELS else None,
        },
    }

    all_results = _load_json(BEST_PARAMS_PATH)
    if "_errors" not in all_results:
        all_results["_errors"] = {}
    all_results[model_name] = record
    _save_json(BEST_PARAMS_PATH, all_results)
    print(f"[Phase4] {model_name} best {score_name}={best_score:.4f} with {best_params}", flush=True)
    return record


def run_phase4_optimization(
    models: List[str] = None,
    population: int = 3,
    iterations: int = 2,
    quick_epochs: int = 1,
) -> Dict:
    """Optimize the given models (default: all six)."""
    if models is None:
        models = ["yolo", "yolo11", "fasterrcnn", "resnet50", "densenet121", "efficientnet_b0"]

    for model_name in models:
        try:
            optimize_model(model_name, population=population, iterations=iterations, quick_epochs=quick_epochs)
        except Exception as exc:
            all_results = _load_json(BEST_PARAMS_PATH)
            all_results.setdefault("_errors", {})[model_name] = str(exc)
            _save_json(BEST_PARAMS_PATH, all_results)
            print(f"[Phase4] {model_name} optimization failed: {exc}", flush=True)

    print(f"Phase 4 results saved to {BEST_PARAMS_PATH}")
    return _load_json(BEST_PARAMS_PATH)
