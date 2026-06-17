"""A0 portrait poster for the Chest X-ray Pneumonia Detection System.
Outputs a print-ready PNG and PDF. Run with the ai venv python.
"""
import os, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = "D:/Collage/graduation project"
FIG = ROOT + "/documentation/figures/"
LOGO = ROOT + "/Zewail Logo/11.png"
DEMO = ROOT + "/Backend/model_assets/demo_output.png"
OUTPNG = ROOT + "/documentation/Poster_A0.png"
OUTPDF = ROOT + "/documentation/Poster_A0.pdf"

NAVY = "#1f3b63"; TEAL = "#2a9d8f"; GREY = "#444444"; LIGHT = "#eaf1f8"

# A0 portrait inches
W, H = 33.11, 46.81
fig = plt.figure(figsize=(W, H), facecolor="white")
bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, 1); bg.set_ylim(0, 1); bg.axis("off")
plt.rcParams["font.family"] = "DejaVu Sans"


def band(x, y, w, h, color):
    bg.add_patch(Rectangle((x, y), w, h, color=color, zorder=1))


def card(x, y, w, h):
    bg.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.008",
                                linewidth=1.5, edgecolor="#cdd9e6", facecolor="white", zorder=1))


def sect_title(x, y, w, text):
    band(x, y, w, 0.016, NAVY)
    bg.text(x + 0.008, y + 0.008, text, color="white", fontsize=27, fontweight="bold", va="center", ha="left", zorder=3)


def body(x, y, text, width=58, size=20, color=GREY, lh=0.0118):
    lines = []
    for para in text.split("\n"):
        if para.strip() == "":
            lines.append("")
            continue
        lines += textwrap.wrap(para, width=width) or [""]
    for i, ln in enumerate(lines):
        bg.text(x, y - i * lh, ln, fontsize=size, color=color, va="top", ha="left", zorder=3)
    return y - len(lines) * lh


def img(path, x, y, w, h):
    ax = fig.add_axes([x, y, w, h]); ax.imshow(mpimg.imread(path)); ax.axis("off")


# ---------- Header ----------
band(0, 0.945, 1, 0.055, NAVY)
img(LOGO, 0.035, 0.9515, 0.13, 0.042)
bg.text(0.52, 0.982, "Chest X-ray Pneumonia Detection System", color="white", fontsize=46, fontweight="bold", ha="center", va="center", zorder=3)
bg.text(0.52, 0.958, "An AI-Assisted Web Platform for Pneumonia Screening and Localization from Chest Radiographs",
        color="#cfe0f0", fontsize=23, ha="center", va="center", zorder=3)
bg.text(0.965, 0.982, "Team 19  -  CSAI", color="white", fontsize=22, ha="right", va="center", fontweight="bold", zorder=3)
bg.text(0.965, 0.958, "Supervisor: Prof. Dr. Khaled Mostafa", color="#cfe0f0", fontsize=18, ha="right", va="center", zorder=3)

# team line
band(0, 0.927, 1, 0.018, TEAL)
bg.text(0.52, 0.936, "Moamen Elsayed Elsharkawy (202202015)   .   Habiba Ayman Amin (202202088)   .   Ahmed Gamal Abdelfattah (202201638)   .   Sara Mostafa Ali (202201305)",
        color="white", fontsize=18, ha="center", va="center", fontweight="bold", zorder=3)
bg.text(0.52, 0.918, "School of Computational Sciences and Artificial Intelligence (CSAI), Zewail City of Science and Technology  -  June 2026",
        color=GREY, fontsize=17, ha="center", va="center", zorder=3)

# columns
Lx, Rx, CW = 0.035, 0.515, 0.45

# ---------- LEFT COLUMN ----------
y = 0.905
sect_title(Lx, y, CW, "Problem and Motivation")
y = body(Lx, y - 0.012,
         "Pneumonia is a leading cause of illness and death worldwide, and the chest X-ray is the first-line tool to detect it. In many clinics the number of radiographs far exceeds the radiologists available to read them, which delays diagnosis and raises the risk of missed cases. A missed pneumonia is the most dangerous error. We provide a fast, accessible AI second reader that flags and localizes pneumonia while the doctor stays in control.",
         width=70, size=20)

y -= 0.012
sect_title(Lx, y, CW, "Objectives")
y = body(Lx, y - 0.012,
         "- Train and honestly evaluate models for pneumonia detection and localization.\n"
         "- Deliver a secure, multi-user web app with patient management and history.\n"
         "- Provide visual explainability with every prediction.\n"
         "- Keep the system reproducible, documented, and maintainable.",
         width=70, size=20)

y -= 0.012
sect_title(Lx, y, CW, "Proposed Solution")
y = body(Lx, y - 0.012,
         "A doctor signs in, manages patients, uploads a chest X-ray, and receives an automated reading: a pneumonia decision, a bounding box, a confidence score, and an explainability heatmap. Five models are served behind one registry; Faster R-CNN is the deployed default. Every analysis is stored per patient, and the physician confirms every result.",
         width=70, size=20)

y -= 0.014
sect_title(Lx, y, CW, "System Architecture")
img(FIG + "architecture.png", Lx, y - 0.135, CW, 0.125)
y = y - 0.150

sect_title(Lx, y, CW, "Technologies Used")
y = body(Lx, y - 0.012,
         "Frontend: Angular 21 (SSR).   Backend: FastAPI (async), Uvicorn.\n"
         "Database: MongoDB (Motor).   AI/ML: PyTorch, torchvision, Ultralytics.\n"
         "Security: JWT, bcrypt, CORS.   Model storage: Git LFS.",
         width=72, size=20)

y -= 0.018
sect_title(Lx, y, CW, "Key Numbers")
card(Lx, y - 0.088, CW, 0.080)
stats = [("0.886", "Best AUC (EfficientNet-B0)"), ("0.812", "Recall (Faster R-CNN)"),
         ("5", "Deep-learning models served"), ("26,684", "RSNA radiographs")]
for i, (num, lab) in enumerate(stats):
    cx = Lx + 0.022 + (i % 2) * (CW / 2)
    cy = y - 0.030 - (i // 2) * 0.038
    bg.text(cx, cy, num, fontsize=40, fontweight="bold", color=TEAL, va="center", ha="left", zorder=3)
    bg.text(cx, cy - 0.020, lab, fontsize=15, color=GREY, va="center", ha="left", zorder=3)

# ---------- RIGHT COLUMN ----------
y = 0.905
sect_title(Rx, y, CW, "Methodology")
img(FIG + "ai_pipeline.png", Rx, y - 0.085, CW, 0.075)
y = body(Rx, y - 0.092,
         "RSNA Pneumonia Detection Challenge (~26,684 radiographs), DICOM to PNG, leak-free patient-wise split (20% held-out test: 4,135 normal / 1,202 pneumonia). Transfer learning, mixed-precision training, augmentation, and early stopping; PSO/GWO/SA hyperparameter search.",
         width=70, size=20)

y -= 0.012
sect_title(Rx, y, CW, "Results (held-out test set)")
img(FIG + "classification_metrics.png", Rx, y - 0.105, CW * 0.5 - 0.004, 0.095)
img(FIG + "detection_metrics.png", Rx + CW * 0.5 + 0.004, y - 0.105, CW * 0.5 - 0.004, 0.095)
y = body(Rx, y - 0.118,
         "Best classifier EfficientNet-B0: AUC 0.886. Deployed detector Faster R-CNN: recall 0.812 (mAP@0.5 0.381). Recall is prioritized because a missed pneumonia is the costly error. Numbers are honest and competitive with the literature (RSNA detection mAP typically 0.32-0.39).",
         width=70, size=20)

y -= 0.012
sect_title(Rx, y, CW, "Sample Output and Explainability")
img(DEMO, Rx, y - 0.150, 0.16, 0.145)
body(Rx + 0.175, y - 0.02,
     "Every prediction is accompanied by a bounding box and a heatmap (Grad-CAM and related methods) so the clinician can verify that the model is looking at the lungs, not an artifact.",
     width=36, size=20)
y = y - 0.160

sect_title(Rx, y, CW, "Conclusion")
y = body(Rx, y - 0.012,
         "A complete, working, explainable full-stack pneumonia screening system: five models rigorously evaluated, secure and reproducible, demonstrating the full path from research model to usable clinical product.",
         width=70, size=20)

# ---------- Footer with QR ----------
band(0, 0, 1, 0.055, NAVY)
img(FIG + "github_qr.png", 0.035, 0.006, 0.042, 0.042)
bg.text(0.092, 0.040, "Project Repository", color="white", fontsize=20, fontweight="bold", va="center", ha="left", zorder=3)
bg.text(0.092, 0.018, "github.com/202201638/Graduation_project_Fully_team_2026", color="#cfe0f0", fontsize=16, va="center", ha="left", zorder=3)
bg.text(0.965, 0.0275, "Graduation Project  -  Bachelor of Science in CSAI  -  Zewail City, June 2026",
        color="#cfe0f0", fontsize=17, ha="right", va="center", zorder=3)

fig.savefig(OUTPNG, dpi=110, facecolor="white")
fig.savefig(OUTPDF, facecolor="white")
print("WROTE", OUTPNG, "and", OUTPDF)
