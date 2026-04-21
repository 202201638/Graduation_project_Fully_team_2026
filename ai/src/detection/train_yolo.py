def train_yolo(
    epochs: int = 20,
    lr: float = 1e-3,
    batch_size: int = 8,
    weight_decay: float = 5e-4,
    anchor_size: int = 16,
    run_name: str = "yolov8_baseline",
):
    import os
    from glob import glob
    from ultralytics import YOLO

    from src.config import RUNS_DIR, YOLO_DATA_YAML
    from src.model_utils import resolve_yolo_base_weights

    model = YOLO(resolve_yolo_base_weights())
    # Some checkpoints carry legacy keys (e.g. anchor_t) that newer Ultralytics rejects.
    model.overrides.pop("anchor_t", None)

    train_results = model.train(
        data=YOLO_DATA_YAML,
        epochs=epochs,
        imgsz=640,
        batch=batch_size,
        lr0=lr,
        weight_decay=weight_decay,
        close_mosaic=10,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        project=RUNS_DIR,
        name=run_name,
    )

    metrics = model.val(data=YOLO_DATA_YAML, imgsz=640, batch=batch_size)
    map50 = float(getattr(metrics.box, "map50", 0.0))
    recall = float(getattr(metrics.box, "r", 0.0))
    best_pt = os.path.join(RUNS_DIR, run_name, "weights", "best.pt")
    if not os.path.exists(best_pt):
        candidates = sorted(glob(os.path.join(RUNS_DIR, f"{run_name}*", "weights", "best.pt")))
        if candidates:
            best_pt = candidates[-1]
        else:   
            best_pt = ""

    print("YOLO training finished")
    return {"map50": map50, "recall": recall, "train_results": str(train_results), "model_path": best_pt}
