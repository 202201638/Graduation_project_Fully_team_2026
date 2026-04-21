import json
import os
from typing import Callable, Dict, List, Tuple

from src.classification.train_densenet import train_densenet
from src.classification.train_efficientnet import train_efficientnet
from src.classification.train_resnet import train_resnet
from src.config import ARTIFACT_DIR
from src.detection.train_fasterrcnn import train_fasterrcnn
from src.detection.train_retinanet import train_retinanet
from src.detection.train_yolo import train_yolo
from src.optimization.algorithms import (
    SearchDimension,
    gwo_optimize,
    pso_optimize,
    sa_optimize,
)

BEST_PARAMS_PATH = os.path.join(ARTIFACT_DIR, "phase4_best_hyperparameters.json")


def _save_json(path: str, data: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _evaluate_detection_model(model_name: str, params: Dict[str, float], quick_epochs: int) -> float:
    try:
        if model_name == "yolo":
            metrics = train_yolo(
                epochs=quick_epochs,
                lr=float(params["lr"]),
                batch_size=int(params["batch_size"]),
                weight_decay=float(params["weight_decay"]),
                anchor_size=int(params["anchor_size"]),
                run_name=f"phase4_{model_name}",
            )
            return float(metrics.get("map50", 0.0))
        if model_name == "fasterrcnn":
            metrics = train_fasterrcnn(
                epochs=quick_epochs,
                lr=float(params["lr"]),
                batch_size=int(params["batch_size"]),
                weight_decay=float(params["weight_decay"]),
            )
            return float(metrics.get("recall", 0.0))
        if model_name == "retinanet":
            metrics = train_retinanet(
                epochs=quick_epochs,
                lr=float(params["lr"]),
                batch_size=int(params["batch_size"]),
                weight_decay=float(params["weight_decay"]),
            )
            return float(metrics.get("recall", 0.0))
        raise ValueError(f"Unknown detection model {model_name}")
    except Exception as exc:
        print(f"[Phase4] detection eval failed for {model_name} with {params}: {exc}")
        return 0.0


def _evaluate_classification_model(model_name: str, params: Dict[str, float], quick_epochs: int) -> float:
    try:
        if model_name == "resnet50":
            metrics = train_resnet(
                epochs=quick_epochs,
                lr=float(params["lr"]),
                batch_size=int(params["batch_size"]),
                dropout=float(params["dropout"]),
                weight_decay=float(params["weight_decay"]),
            )
        elif model_name == "densenet121":
            metrics = train_densenet(
                epochs=quick_epochs,
                lr=float(params["lr"]),
                batch_size=int(params["batch_size"]),
                dropout=float(params["dropout"]),
                weight_decay=float(params["weight_decay"]),
            )
        elif model_name == "efficientnet_b0":
            metrics = train_efficientnet(
                epochs=quick_epochs,
                lr=float(params["lr"]),
                batch_size=int(params["batch_size"]),
                dropout=float(params["dropout"]),
                weight_decay=float(params["weight_decay"]),
            )
        else:
            raise ValueError(f"Unknown classification model {model_name}")
        return float(metrics.get("auc", 0.0))
    except Exception as exc:
        print(f"[Phase4] classification eval failed for {model_name} with {params}: {exc}")
        return 0.0


def _run_all_algorithms(
    objective: Callable[[Dict[str, float]], float],
    dims: List[SearchDimension],
    population: int,
    iterations: int,
) -> Tuple[Dict[str, float], float, Dict[str, Dict[str, float]]]:
    """
    Fast optimization set:
    - PSO
    - GWO
    - SA
    """
    algo_results = {}

    best_params, best_score = pso_optimize(objective, dims, population=population, iterations=iterations)
    algo_results["PSO"] = {"best_params": best_params, "best_score": best_score}

    params, score = gwo_optimize(objective, dims, population=population, iterations=iterations)
    algo_results["GWO"] = {"best_params": params, "best_score": score}
    if score > best_score:
        best_params, best_score = params, score

    params, score = sa_optimize(objective, dims, iterations=max(10, population * iterations))
    algo_results["SA"] = {"best_params": params, "best_score": score}
    if score > best_score:
        best_params, best_score = params, score

    return best_params, best_score, algo_results


def run_phase4_optimization(quick_epochs: int = 1, population: int = 4, iterations: int = 2):
    print("Phase 4: Nature-Inspired Hyperparameter Optimization")
    all_results: Dict[str, Dict] = {"_errors": {}}

    # Optimized models (fast runtime set, 3 models only):
    # 1) YOLO (for final demo + detection)
    # 2) ResNet50
    # 3) EfficientNet-B0
    # Detection model (include anchor_size tuning for YOLO)
    detection_dims_yolo = [
        SearchDimension("lr", 1e-5, 5e-3, "float"),
        SearchDimension("batch_size", 2, 16, "int"),
        SearchDimension("weight_decay", 1e-6, 1e-2, "float"),
        SearchDimension("anchor_size", 8, 64, "int"),
    ]
    yolo_objective = lambda p: _evaluate_detection_model("yolo", p, quick_epochs=quick_epochs)
    try:
        best_params, best_score, algo_results = _run_all_algorithms(
            objective=yolo_objective,
            dims=detection_dims_yolo,
            population=population,
            iterations=iterations,
        )
        all_results["yolo"] = {
            "task": "detection",
            "score_name": "map50",
            "best_score": best_score,
            "best_hyperparameters": best_params,
            "algorithms": algo_results,
        }
        print(f"[Phase4] yolo best score={best_score:.4f} with {best_params}")
    except Exception as exc:
        all_results["_errors"]["yolo"] = str(exc)
        print(f"[Phase4] yolo optimization failed: {exc}")
    _save_json(BEST_PARAMS_PATH, all_results)

    # Classification models (optimize dropout too)
    cls_dims = [
        SearchDimension("lr", 1e-5, 1e-3, "float"),
        SearchDimension("batch_size", 4, 32, "int"),
        SearchDimension("dropout", 0.1, 0.6, "float"),
        SearchDimension("weight_decay", 1e-7, 1e-2, "float"),
    ]
    for cls_model in ["resnet50", "efficientnet_b0"]:
        objective = lambda p, m=cls_model: _evaluate_classification_model(m, p, quick_epochs=quick_epochs)
        try:
            best_params, best_score, algo_results = _run_all_algorithms(
                objective=objective,
                dims=cls_dims,
                population=population,
                iterations=iterations,
            )
            all_results[cls_model] = {
                "task": "classification",
                "score_name": "auc",
                "best_score": best_score,
                "best_hyperparameters": best_params,
                "algorithms": algo_results,
            }
            print(f"[Phase4] {cls_model} best score={best_score:.4f} with {best_params}")
        except Exception as exc:
            all_results["_errors"][cls_model] = str(exc)
            print(f"[Phase4] {cls_model} optimization failed: {exc}")
        _save_json(BEST_PARAMS_PATH, all_results)

    _save_json(BEST_PARAMS_PATH, all_results)
    print(f"Phase 4 results saved to {BEST_PARAMS_PATH}")
    return all_results
