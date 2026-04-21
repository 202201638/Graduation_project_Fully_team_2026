import os

from src.dataset import explore_dataset
from src.preprocessing import convert_dicom_to_png
from src.visualization import show_pneumonia_example
from src.yolo_dataset import build_yolo_dataset
from src.yolo_visualization import show_yolo_samples

from src.detection.train_yolo import train_yolo
from src.detection.train_fasterrcnn import train_fasterrcnn
from src.detection.train_retinanet import train_retinanet

from src.classification.train_resnet import train_resnet
from src.classification.train_densenet import train_densenet
from src.classification.train_efficientnet import train_efficientnet
from src.phase3_baseline import run_phase3_baseline
from src.phase4_optimization import run_phase4_optimization
from src.phase5_retrain import run_phase5_retrain
from src.phase6_explainability import run_phase6_gradcam
from src.phase7_final_evaluation import run_phase7_final_evaluation
from src.phase8_demo import run_phase8_demo
from src.preflight import run_preflight_checks
from src.config import YOLO_DATASET_DIR


# phase 1
RUN_CONVERSION = False
RUN_VISUALIZATION_PNG = False

# phase 2
RUN_BUILD_DATASET = False
RUN_VISUALIZE_YOLO = False

# phase 3
RUN_YOLO = False
RUN_FASTER_RCNN = False
RUN_RETINANET = False
RUN_RESNET = False
RUN_DENSENET = False
RUN_EFFICIENTNET = False

# phases 3 -> 8 end-to-end workflow
RUN_PHASE3_BASELINE_ALL = False
RUN_PHASE4_OPTIMIZATION = False
RUN_PHASE5_RETRAIN = False
RUN_PHASE6_EXPLAINABILITY = False
RUN_PHASE7_FINAL_EVALUATION = False
RUN_PHASE8_DEMO = False
RUN_PREFLIGHT_CHECKS = False
DEMO_IMAGE_PATH = os.path.join(YOLO_DATASET_DIR, "val", "images")  # if folder, first image is used

if __name__ == "__main__":
    
    df = explore_dataset()

    ################# phase 1
    if RUN_CONVERSION:
        convert_dicom_to_png()

    if RUN_VISUALIZATION_PNG:
        show_pneumonia_example(df)
    ################# phase 2
    if RUN_BUILD_DATASET:
        build_yolo_dataset(df)

    if RUN_VISUALIZE_YOLO:
        show_yolo_samples()
    ################# phase 3
    if RUN_YOLO:
        train_yolo()

    if RUN_FASTER_RCNN:
        train_fasterrcnn()

    if RUN_RETINANET:
        train_retinanet()

    if RUN_RESNET:
        train_resnet()

    if RUN_DENSENET:
        train_densenet()

    if RUN_EFFICIENTNET:
        train_efficientnet()

    if RUN_PHASE3_BASELINE_ALL:
        run_phase3_baseline()

    if RUN_PHASE4_OPTIMIZATION:
        run_phase4_optimization()

    if RUN_PHASE5_RETRAIN:
        run_phase5_retrain()

    if RUN_PHASE6_EXPLAINABILITY:
        run_phase6_gradcam()

    if RUN_PHASE7_FINAL_EVALUATION:
        run_phase7_final_evaluation()

    if RUN_PHASE8_DEMO:
        if os.path.isdir(DEMO_IMAGE_PATH):
            files = sorted([f for f in os.listdir(DEMO_IMAGE_PATH) if f.endswith(".png")])
            if not files:
                raise RuntimeError("No demo image found in the provided folder.")
            demo_image = os.path.join(DEMO_IMAGE_PATH, files[0])
        else:
            demo_image = DEMO_IMAGE_PATH
        demo_result = run_phase8_demo(demo_image)
        print("Phase 8 demo result:", demo_result)

    if RUN_PREFLIGHT_CHECKS:
        run_preflight_checks()

