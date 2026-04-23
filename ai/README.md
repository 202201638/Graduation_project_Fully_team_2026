# AI Pipeline

This folder contains the reproducible research pipeline for chest X-ray pneumonia detection.

Current deployment policy:

- `fasterrcnn` is the default web model because local checks showed better pneumonia localization than the available YOLO/RetinaNet assets.
- Detection models can draw pneumonia boxes.
- Classification models cannot localize regions and should be shown as probability-only models.

Useful commands:

```powershell
python -m compileall main.py src
python -c "from src.preflight import run_preflight_checks; run_preflight_checks()"
python -m src.model_promotion --metric recall
python -m src.inference_smoke --backend-url http://localhost:8000 --model-name fasterrcnn --limit 2
```

Use `python -m src.model_promotion --metric recall --apply` only when intentionally promoting artifacts into `../Backend/model_assets`.
