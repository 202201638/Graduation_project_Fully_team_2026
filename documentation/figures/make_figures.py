"""
Generate thesis / slide / poster figures for the Chest X-ray Pneumonia Detection System.
Reads the real held-out test metrics from Backend/model_assets/model_metrics.json
and draws charts + architecture/data-flow/AI-pipeline/ERD diagrams.

Run with the ai venv python:
    ai/venv/Scripts/python.exe documentation/figures/make_figures.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "documentation", "figures")
os.makedirs(OUT, exist_ok=True)
METRICS = os.path.join(ROOT, "Backend", "model_assets", "model_metrics.json")

with open(METRICS, "r", encoding="utf-8") as f:
    M = json.load(f)

# Palette
NAVY = "#1f3b63"
BLUE = "#2f6fb0"
TEAL = "#2a9d8f"
RED = "#d1495b"
AMBER = "#e9a13b"
LIGHT = "#eaf1f8"
GREY = "#5a5a5a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

CLS = ["resnet50", "densenet121", "efficientnet_b0"]
CLS_LABEL = {"resnet50": "ResNet50", "densenet121": "DenseNet121", "efficientnet_b0": "EfficientNet-B0"}
DET = ["yolo", "fasterrcnn"]
DET_LABEL = {"yolo": "YOLOv8n", "fasterrcnn": "Faster R-CNN"}


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", p)


# ---------- 1. Classification metrics ----------
def classification_metrics():
    metrics = ["auc", "accuracy", "recall", "specificity", "f1"]
    labels = ["AUC", "Accuracy", "Recall (Sens.)", "Specificity", "F1"]
    x = np.arange(len(metrics))
    w = 0.25
    colors = [BLUE, TEAL, AMBER]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for i, m in enumerate(CLS):
        vals = [M[m][k] for k in metrics]
        bars = ax.bar(x + (i - 1) * w, vals, w, label=CLS_LABEL[m], color=colors[i])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.3f}",
                    ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score")
    ax.set_title("Classification Models - Held-out Test Performance", fontweight="bold", color=NAVY)
    ax.legend(loc="lower right", framealpha=0.95)
    ax.grid(axis="y", alpha=0.25)
    save(fig, "classification_metrics.png")


# ---------- 2. Detection metrics ----------
def detection_metrics():
    metrics = ["map50", "map", "recall"]
    labels = ["mAP@0.5", "mAP@[.5:.95]", "Recall@0.5"]
    x = np.arange(len(metrics))
    w = 0.34
    fig, ax = plt.subplots(figsize=(8, 4.8))
    colors = {"yolo": AMBER, "fasterrcnn": RED}
    for i, d in enumerate(DET):
        vals = [M[d].get(k, 0.0) for k in metrics]
        bars = ax.bar(x + (i - 0.5) * w, vals, w, label=DET_LABEL[d], color=colors[d])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.3f}",
                    ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score")
    ax.set_title("Detection Models - Held-out Test Performance", fontweight="bold", color=NAVY)
    ax.legend(loc="upper right", framealpha=0.95)
    ax.grid(axis="y", alpha=0.25)
    ax.annotate("Faster R-CNN recall is ~2x YOLO:\nfewer missed pneumonia cases",
                xy=(2 - 0.17, M["fasterrcnn"]["recall"]), xytext=(-0.1, 0.60),
                fontsize=8.5, color=GREY, ha="left",
                arrowprops=dict(arrowstyle="->", color=GREY))
    save(fig, "detection_metrics.png")


# ---------- 3. Confusion matrices ----------
def confusion_matrices():
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    classes = ["Normal", "Pneumonia"]
    for ax, m in zip(axes, CLS):
        cm = np.array(M[m]["confusion_matrix"])
        im = ax.imshow(cm, cmap="Blues")
        ax.set_title(f"{CLS_LABEL[m]}\nAUC {M[m]['auc']:.3f}", fontsize=10, color=NAVY)
        ax.set_xticks([0, 1]); ax.set_xticklabels(classes)
        ax.set_yticks([0, 1]); ax.set_yticklabels(classes)
        ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
        thr = cm.max() / 2
        labels = [["TN", "FP"], ["FN", "TP"]]
        for r in range(2):
            for c in range(2):
                ax.text(c, r, f"{labels[r][c]}\n{cm[r][c]}", ha="center", va="center",
                        color="white" if cm[r][c] > thr else NAVY, fontsize=10, fontweight="bold")
    fig.suptitle("Confusion Matrices (held-out test: 4,135 Normal / 1,202 Pneumonia)",
                 fontweight="bold", color=NAVY, y=1.02)
    save(fig, "confusion_matrices.png")


# ---------- helpers for diagrams ----------
def box(ax, x, y, w, h, text, fc=LIGHT, ec=NAVY, fs=10, bold=True, tc=NAVY):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                       linewidth=1.6, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x1, y1, x2, y2, color=GREY, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=16, lw=1.6, color=color))


def blank_ax(figsize, xlim, ylim):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.axis("off")
    return fig, ax


# ---------- 4. Architecture ----------
def architecture():
    fig, ax = blank_ax((11, 6.4), (0, 12), (0, 9))
    ax.text(6, 8.6, "System Architecture", ha="center", fontsize=15, fontweight="bold", color=NAVY)
    box(ax, 0.4, 5.6, 2.7, 1.8, "Frontend\nAngular 21 (SSR)\nDashboard / Upload /\nResult / Records", fc="#dbe9f6")
    box(ax, 4.6, 5.6, 3.0, 1.8, "FastAPI Backend\n(async, Uvicorn)\nAuth / Patients / X-ray\nrouters", fc="#dbe9f6")
    box(ax, 9.0, 5.6, 2.6, 1.8, "MongoDB\nusers / patients /\nxray_analyses\n(Motor async)", fc="#e3f0ec", ec=TEAL, tc="#1d6b5f")
    box(ax, 4.3, 2.2, 3.6, 2.2, "Inference Service\nmodel registry +\nsingleton warmup\nNMS + Explainability", fc="#fdeede", ec=RED, tc="#8a2f3b")
    box(ax, 9.0, 2.4, 2.6, 1.9, "Model Assets\nFaster R-CNN, YOLOv8\nResNet/DenseNet/EffNet\n(.pt via Git LFS)", fc="#f6efe0", ec=AMBER, tc="#7a5611")
    box(ax, 0.4, 2.6, 2.7, 1.5, "Doctor\n(browser)", fc="#eeeeee", ec=GREY, tc=GREY)
    arrow(ax, 3.1, 6.5, 4.6, 6.5); ax.text(3.85, 6.75, "HTTPS + JWT", ha="center", fontsize=8, color=GREY)
    arrow(ax, 7.6, 6.5, 9.0, 6.5); ax.text(8.3, 6.75, "CRUD", ha="center", fontsize=8, color=GREY)
    arrow(ax, 6.1, 5.6, 6.1, 4.4); ax.text(6.5, 5.0, "predict", ha="center", fontsize=8, color=GREY)
    arrow(ax, 7.9, 3.3, 9.0, 3.3); ax.text(8.45, 3.5, "load weights", ha="center", fontsize=8, color=GREY)
    arrow(ax, 1.75, 4.1, 1.75, 5.6); ax.text(2.15, 4.85, "uses", ha="center", fontsize=8, color=GREY)
    save(fig, "architecture.png")


# ---------- 5. Data flow ----------
def dataflow():
    steps = ["Upload\nX-ray", "Validate\n(type/size/\ndecode)", "Inference\n(deep model)",
             "NMS\n(dedup boxes)", "Render\nboxes + heatmap", "Persist\n(Mongo + files)", "Display\nresult"]
    fig, ax = blank_ax((13.5, 3.2), (0, 14), (0, 3))
    ax.text(7, 2.8, "Prediction Data Flow", ha="center", fontsize=14, fontweight="bold", color=NAVY)
    w, h, gap = 1.7, 1.2, 0.25
    x = 0.2
    cols = ["#dbe9f6", "#dbe9f6", "#fdeede", "#fdeede", "#fdeede", "#e3f0ec", "#dbe9f6"]
    ecs = [NAVY, NAVY, RED, RED, RED, TEAL, NAVY]
    for i, s in enumerate(steps):
        box(ax, x, 0.8, w, h, s, fc=cols[i], ec=ecs[i], fs=9, tc=NAVY)
        if i < len(steps) - 1:
            arrow(ax, x + w, 1.4, x + w + gap, 1.4)
        x += w + gap
    save(fig, "dataflow.png")


# ---------- 6. AI pipeline ----------
def ai_pipeline():
    steps = ["1. Data prep\nDICOM->PNG\nCLAHE, splits", "2. Baseline\ntraining", "3. Optimize\nPSO / GWO / SA",
             "4. Retrain\nbest params", "5. Explainability\nGrad-CAM, etc.", "6. Evaluation\nheld-out test",
             "7. Demo\nsingle image", "8. Promotion\n-> backend"]
    fig, ax = blank_ax((14, 3.4), (0, 14.4), (0, 3))
    ax.text(7.2, 2.85, "AI / ML Pipeline (8 phases)", ha="center", fontsize=14, fontweight="bold", color=NAVY)
    w, h, gap = 1.55, 1.4, 0.18
    x = 0.15
    for i, s in enumerate(steps):
        box(ax, x, 0.7, w, h, s, fc="#eef4fb", ec=BLUE, fs=8, tc=NAVY)
        if i < len(steps) - 1:
            arrow(ax, x + w, 1.4, x + w + gap, 1.4)
        x += w + gap
    save(fig, "ai_pipeline.png")


# ---------- 7. ERD ----------
def erd():
    fig, ax = blank_ax((11, 5.2), (0, 12), (0, 7))
    ax.text(6, 6.6, "Database Schema (MongoDB collections)", ha="center", fontsize=13, fontweight="bold", color=NAVY)
    def entity(x, y, title, fields, ec=NAVY, fc=LIGHT):
        h = 0.55 + 0.42 * len(fields)
        box(ax, x, y, 3.2, 0.55, title, fc=ec, ec=ec, tc="white", fs=11)
        body = FancyBboxPatch((x, y - (h - 0.55)), 3.2, h - 0.55,
                              boxstyle="round,pad=0.01", linewidth=1.4, edgecolor=ec, facecolor=fc)
        ax.add_patch(body)
        for i, fld in enumerate(fields):
            ax.text(x + 0.15, y - 0.28 - i * 0.42, fld, ha="left", va="center", fontsize=8.5, color=GREY)
        return h
    entity(0.4, 6.0, "User", ["_id (PK)", "email (unique)", "password_hash", "full_name", "created_at"], ec=NAVY)
    entity(4.4, 6.0, "Patient", ["patient_id (PK)", "user_id (FK)", "name, dob, gender", "phone, address", "created_at"], ec=BLUE)
    entity(8.4, 6.0, "XrayAnalysis", ["analysis_id (PK)", "patient_id (FK)", "user_id (FK)", "model_name, status", "confidence, boxes", "heatmaps, created_at"], ec=TEAL)
    arrow(ax, 3.6, 5.0, 4.4, 5.0); ax.text(4.0, 5.2, "1..*", ha="center", fontsize=8, color=GREY)
    arrow(ax, 7.6, 5.0, 8.4, 5.0); ax.text(8.0, 5.2, "1..*", ha="center", fontsize=8, color=GREY)
    save(fig, "erd.png")


# ---------- 8. GitHub QR ----------
def github_qr():
    url = "https://github.com/202201638/Graduation_project_Fully_team_2026"
    try:
        import qrcode
    except Exception:
        print("qrcode not installed; skipping QR (install qrcode[pil])")
        return
    img = qrcode.make(url)
    p = os.path.join(OUT, "github_qr.png")
    img.save(p)
    print("wrote", p)


if __name__ == "__main__":
    classification_metrics()
    detection_metrics()
    confusion_matrices()
    architecture()
    dataflow()
    ai_pipeline()
    erd()
    github_qr()
    print("DONE")
