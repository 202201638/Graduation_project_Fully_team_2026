def train_yolo(
    epochs: int = 40,
    lr: float = 1e-3,
    batch_size: int = 16,
    weight_decay: float = 5e-4,
    anchor_size: int = 16,  # accepted for signature/optimizer compatibility (YOLOv8 is anchor-free)
    patience: int = 10,
    fraction: float = 1.0,   # <1.0 trains on a data subset (used by Phase 4 proxy search)
    eval_test: bool = True,  # False = skip test-split eval (Phase 4 proxy)
    run_name: str = "yolov8_baseline",
):
    import os
    from glob import glob
    from ultralytics import YOLO

    from src.config import RUNS_DIR, YOLO_DATA_YAML, IMG_SIZE
    from src.model_utils import resolve_yolo_base_weights

    model = YOLO(resolve_yolo_base_weights())
    # Some checkpoints carry legacy keys (e.g. anchor_t) that newer Ultralytics rejects.
    model.overrides.pop("anchor_t", None)

    train_results = model.train(
        data=YOLO_DATA_YAML,
        epochs=epochs,
        imgsz=IMG_SIZE,
        batch=batch_size,
        lr0=lr,
        weight_decay=weight_decay,
        patience=patience,        # built-in early stopping
        fraction=fraction,
        cos_lr=True,              # cosine LR schedule
        close_mosaic=10,
        # explicit augmentation (defaults are sensible, set them so nothing silently disables)
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        project=RUNS_DIR,
        name=run_name,
        exist_ok=True,
        verbose=True,
    )

    def _extract(m):
        return {
            "map50": float(getattr(m.box, "map50", 0.0)),
            "map": float(getattr(m.box, "map", 0.0)),  # mAP@0.5:0.95
            "recall": float(getattr(m.box, "mr", getattr(m.box, "r", 0.0)) or 0.0),
            "precision": float(getattr(m.box, "mp", getattr(m.box, "p", 0.0)) or 0.0),
        }

    # Validate on val (always) and test (skipped during Phase 4 proxy search)
    val_metrics = model.val(data=YOLO_DATA_YAML, imgsz=IMG_SIZE, batch=batch_size, split="val")
    val_scores = _extract(val_metrics)
    if eval_test:
        test_metrics = model.val(data=YOLO_DATA_YAML, imgsz=IMG_SIZE, batch=batch_size, split="test")
        test_scores = _extract(test_metrics)
        eval_split = "test"
    else:
        test_scores = val_scores
        eval_split = "val"

    best_pt = os.path.join(RUNS_DIR, run_name, "weights", "best.pt")
    if not os.path.exists(best_pt):
        candidates = sorted(glob(os.path.join(RUNS_DIR, f"{run_name}*", "weights", "best.pt")))
        best_pt = candidates[-1] if candidates else ""

    try:
        num_params = int(sum(p.numel() for p in model.model.parameters()))
    except Exception:
        num_params = None

    print("YOLO training finished", flush=True)
    return {
        "model": "yolo",
        "task": "detection",
        # headline metrics reported on the held-out TEST split
        "map50": test_scores["map50"],
        "map": test_scores["map"],
        "recall": test_scores["recall"],
        "precision": test_scores["precision"],
        "eval_split": eval_split,
        "val_metrics": val_scores,
        "model_path": best_pt,
        "results_csv": os.path.join(RUNS_DIR, run_name, "results.csv"),
        "num_parameters": num_params,
        "hyperparameters": {
            "epochs": epochs,
            "lr0": lr,
            "batch_size": batch_size,
            "weight_decay": weight_decay,
            "img_size": IMG_SIZE,
            "patience": patience,
            "optimizer": "SGD (ultralytics auto)",
            "lr_scheduler": "cosine (cos_lr=True)",
            "augmentation": "mosaic, hsv, translate, scale, fliplr (close_mosaic=10)",
            "box": 7.5,
            "cls": 0.5,
            "dfl": 1.5,
        },
    }
