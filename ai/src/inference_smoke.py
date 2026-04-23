import argparse
import json
from pathlib import Path
from typing import Any

import requests

from src.config import ARTIFACT_DIR


def _sample_images(samples_dir: Path) -> list[Path]:
    return sorted(path for path in samples_dir.glob("*.png") if path.is_file())


def run_backend_inference_smoke(
    backend_url: str = "http://localhost:8000",
    samples_dir: Path | None = None,
    model_name: str = "fasterrcnn",
    limit: int = 2,
) -> list[dict[str, Any]]:
    sample_root = samples_dir or Path(ARTIFACT_DIR) / "app_test_samples"
    images = _sample_images(sample_root)[:limit]
    if not images:
        raise RuntimeError(f"No PNG smoke-test samples found in {sample_root}")

    results: list[dict[str, Any]] = []
    endpoint = f"{backend_url.rstrip('/')}/api/xray/analyze"
    for image_path in images:
        with image_path.open("rb") as file:
            response = requests.post(
                endpoint,
                files={"file": (image_path.name, file, "image/png")},
                data={
                    "patient_id": "SMOKE_TEST",
                    "scan_type": "Chest X-ray",
                    "model_name": model_name,
                },
                timeout=120,
            )
        response.raise_for_status()
        payload = response.json()
        result = payload["result"]
        results.append(
            {
                "sample": image_path.name,
                "analysis_id": payload["analysis_id"],
                "model_name": payload.get("model_name"),
                "pneumonia_detected": result.get("pneumonia_detected"),
                "confidence_score": result.get("confidence_score"),
                "detections": len(result.get("detections", [])),
                "rendered_image_url": result.get("rendered_image_url"),
            }
        )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run backend inference smoke tests.")
    parser.add_argument("--backend-url", default="http://localhost:8000")
    parser.add_argument("--samples-dir", type=Path, default=None)
    parser.add_argument("--model-name", default="fasterrcnn")
    parser.add_argument("--limit", type=int, default=2)
    args = parser.parse_args()

    results = run_backend_inference_smoke(
        backend_url=args.backend_url,
        samples_dir=args.samples_dir,
        model_name=args.model_name,
        limit=args.limit,
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
