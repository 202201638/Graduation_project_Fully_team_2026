import os
import json
import pandas as pd
from src.config import ARTIFACT_DIR, INPUT_DIR, LABEL_PATH

def explore_dataset():
    files = os.listdir(INPUT_DIR)

    print("Total images:", len(files))
    print("First file:", files[0])

    df = pd.read_csv(LABEL_PATH)

    print(df.head())
    print(df["Target"].value_counts())

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    summary_path = os.path.join(ARTIFACT_DIR, "phase1_dataset_summary.json")
    summary = {
        "input_dir": INPUT_DIR,
        "label_path": LABEL_PATH,
        "total_images": len(files),
        "first_file": files[0] if files else None,
        "target_distribution": df["Target"].value_counts().to_dict(),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Phase 1 dataset summary saved to {summary_path}")

    return df
