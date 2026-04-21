from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ModelResult:
    name: str
    task: str  # "detection" or "classification"
    accuracy: Optional[float] = None
    map50: Optional[float] = None
    recall: Optional[float] = None


def print_results_table(results: List[ModelResult]) -> None:
    header = "| Model | Task | Accuracy | mAP@0.5 | Recall |\n"
    header += "|-------|------|----------|---------|--------|\n"
    rows = []
    for r in results:
        acc = f"{r.accuracy:.4f}" if r.accuracy is not None else "-"
        map50 = f"{r.map50:.4f}" if r.map50 is not None else "-"
        recall = f"{r.recall:.4f}" if r.recall is not None else "-"
        rows.append(f"| {r.name} | {r.task} | {acc} | {map50} | {recall} |")

    print(header + "\n".join(rows))


if __name__ == "__main__":
    # Example: fill in after running your experiments
    example_results = [
        ModelResult(name="YOLOv8", task="detection", map50=0.0, recall=0.0),
        ModelResult(name="Faster R-CNN", task="detection", recall=0.0),
        ModelResult(name="RetinaNet", task="detection", recall=0.0),
        ModelResult(name="ResNet50", task="classification", accuracy=0.0),
        ModelResult(name="DenseNet121", task="classification", accuracy=0.0),
        ModelResult(name="EfficientNet-B0", task="classification", accuracy=0.0),
    ]
    print_results_table(example_results)

