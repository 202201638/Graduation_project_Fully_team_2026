"""15-slide defense deck for the Chest X-ray Pneumonia Detection System.
Run: ai/venv/Scripts/python.exe documentation/_generators/deck.py
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = "D:/Collage/graduation project"
FIG = ROOT + "/documentation/figures/"
LOGO = ROOT + "/Zewail Logo/11.png"
DEMO = ROOT + "/Backend/model_assets/demo_output.png"
OUT = ROOT + "/documentation/Defense_Presentation.pptx"

NAVY = RGBColor(0x1F, 0x3B, 0x63)
TEAL = RGBColor(0x2A, 0x9D, 0x8F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x33, 0x33, 0x33)
GREY = RGBColor(0x66, 0x66, 0x66)
LIGHT = RGBColor(0xEA, 0xF1, 0xF8)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


def slide():
    return prs.slides.add_slide(BLANK)


def rect(s, l, t, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    sp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    sp.fill.solid(); sp.fill.fore_color.rgb = color
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def textbox(s, l, t, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(l, t, w, h); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    for i, (text, size, color, bold) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = text
        r.font.size = Pt(size); r.font.color.rgb = color; r.font.bold = bold
        r.font.name = "Calibri"
        p.space_after = Pt(6)
    return tb


def bullets(s, l, t, w, h, items, size=18, color=DARK):
    tb = s.shapes.add_textbox(l, t, w, h); tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = "•  " + it
        r.font.size = Pt(size); r.font.color.rgb = color; r.font.name = "Calibri"
        p.space_after = Pt(10)
    return tb


def header(s, title, n):
    rect(s, 0, 0, SW, Inches(1.15), NAVY)
    textbox(s, Inches(0.55), Inches(0.12), Inches(10.5), Inches(0.9),
            [(title, 30, WHITE, True)], anchor=MSO_ANCHOR.MIDDLE)
    # brand logo top-right
    s.shapes.add_picture(LOGO, SW - Inches(1.7), Inches(0.18), height=Inches(0.78))
    # footer
    textbox(s, Inches(0.4), SH - Inches(0.45), Inches(9), Inches(0.4),
            [("Chest X-ray Pneumonia Detection System  |  Team 19  |  CSAI, Zewail City", 10, GREY, False)])
    textbox(s, SW - Inches(1.6), SH - Inches(0.45), Inches(1.2), Inches(0.4),
            [(str(n) + " / 15", 10, GREY, False)], align=PP_ALIGN.RIGHT)


def img_fit(s, path, l, t, max_w, max_h):
    from PIL import Image
    iw, ih = Image.open(path).size
    r = min(max_w / iw, max_h / ih)
    w, h = int(iw * r), int(ih * r)
    left = l + int((max_w - w) / 2)
    s.shapes.add_picture(path, left, t, width=w, height=h)


# ---------- Slide 1: Title ----------
s = slide()
rect(s, 0, 0, SW, SH, WHITE)
rect(s, 0, 0, SW, Inches(0.25), NAVY)
rect(s, 0, SH - Inches(0.25), SW, Inches(0.25), TEAL)
s.shapes.add_picture(LOGO, int((SW - Inches(2.8)) / 2), Inches(0.5), width=Inches(2.8))
textbox(s, Inches(1), Inches(2.35), Inches(11.33), Inches(0.5),
        [("Zewail City of Science and Technology", 18, GREY, False)], align=PP_ALIGN.CENTER)
textbox(s, Inches(0.8), Inches(2.8), Inches(11.73), Inches(1.0),
        [("Chest X-ray Pneumonia Detection System", 40, NAVY, True)], align=PP_ALIGN.CENTER)
textbox(s, Inches(1), Inches(3.85), Inches(11.33), Inches(0.5),
        [("Graduation Project Defense  -  School of CSAI  -  June 2026", 16, TEAL, True)], align=PP_ALIGN.CENTER)
team = [
    ("Submitted by", 14, GREY, True),
    ("Moamen Elsayed Elsharkawy (202202015)      Habiba Ayman Amin (202202088)", 15, DARK, False),
    ("Ahmed Gamal Abdelfattah (202201638)      Sara Mostafa Ali (202201305)", 15, DARK, False),
]
textbox(s, Inches(1), Inches(4.6), Inches(11.33), Inches(1.3), team, align=PP_ALIGN.CENTER)
textbox(s, Inches(1), Inches(5.95), Inches(11.33), Inches(0.6),
        [("Supervisor: Prof. Dr. Khaled Mostafa      |      Team Number: 19", 16, NAVY, True)], align=PP_ALIGN.CENTER)

# ---------- Slide 2: Problem ----------
s = slide(); header(s, "Problem Statement", 2)
bullets(s, Inches(0.7), Inches(1.5), Inches(11.9), Inches(5),
        ["Pneumonia is a leading cause of illness and death worldwide; the chest X-ray is the first-line tool to detect it.",
         "Radiograph volume far exceeds the number of radiologists available to read them.",
         "Manual reading is slow, depends on scarce expertise, and is vulnerable to fatigue and missed cases.",
         "A missed pneumonia (false negative) is the most dangerous error.",
         "Need: a fast, accessible screening aid that flags and localizes pneumonia while keeping the doctor in control."], size=20)

# ---------- Slide 3: Motivation & Objectives ----------
s = slide(); header(s, "Motivation and Objectives", 3)
textbox(s, Inches(0.7), Inches(1.35), Inches(11.9), Inches(0.5), [("Motivation", 20, TEAL, True)])
bullets(s, Inches(0.7), Inches(1.85), Inches(11.9), Inches(1.6),
        ["Shorten time-to-diagnosis and reduce missed cases with an AI second reader.",
         "Take research-grade models all the way to a usable, secure clinical product."], size=18)
textbox(s, Inches(0.7), Inches(3.5), Inches(11.9), Inches(0.5), [("Objectives", 20, TEAL, True)])
bullets(s, Inches(0.7), Inches(4.0), Inches(11.9), Inches(3),
        ["Train and rigorously evaluate models for pneumonia detection and localization.",
         "Deliver a secure, multi-user web app with patient management and history.",
         "Provide visual explainability with every prediction.",
         "Keep the work reproducible, documented, and maintainable."], size=18)

# ---------- Slide 4: Literature / Existing Solutions ----------
s = slide(); header(s, "Literature and Existing Solutions", 4)
bullets(s, Inches(0.7), Inches(1.45), Inches(11.9), Inches(3),
        ["CNNs (CheXNet/DenseNet) reach near radiologist-level pneumonia classification on chest X-rays.",
         "Detection adds localization: two-stage Faster R-CNN (accurate) vs one-stage YOLO (fast).",
         "RSNA Pneumonia Detection Challenge is the standard benchmark (~26,684 labeled radiographs).",
         "Commercial tools (Lunit, Aidoc, qure.ai) exist but are closed and expensive; academic prototypes rarely ship."], size=18)
textbox(s, Inches(0.7), Inches(4.7), Inches(11.9), Inches(1.5),
        [("Our gap: a transparent, explainable, end-to-end, self-hostable screening tool, evaluated honestly and leak-free.", 18, NAVY, True)])

# ---------- Slide 5: Proposed Solution ----------
s = slide(); header(s, "Proposed Solution", 5)
bullets(s, Inches(0.7), Inches(1.45), Inches(7.2), Inches(5),
        ["A doctor-facing web app: sign in, manage patients, upload an X-ray, get a reading.",
         "Returns: pneumonia decision, bounding box, confidence, and an explainability heatmap.",
         "Five models behind one registry; Faster R-CNN is the deployed default.",
         "Every analysis is stored per patient for later review.",
         "The physician confirms every result (decision support, not autonomous)."], size=18)
img_fit(s, DEMO, Inches(8.2), Inches(1.5), Inches(4.6), Inches(4.6))
textbox(s, Inches(8.2), Inches(6.1), Inches(4.6), Inches(0.4),
        [("Sample detector output", 12, GREY, False)], align=PP_ALIGN.CENTER)

# ---------- Slide 6: Architecture ----------
s = slide(); header(s, "System Architecture", 6)
img_fit(s, FIG + "architecture.png", Inches(0.7), Inches(1.4), Inches(11.9), Inches(5.5))

# ---------- Slide 7: Methodology ----------
s = slide(); header(s, "Methodology - AI Pipeline", 7)
img_fit(s, FIG + "ai_pipeline.png", Inches(0.5), Inches(1.5), Inches(12.3), Inches(2.6))
img_fit(s, FIG + "dataflow.png", Inches(0.5), Inches(4.2), Inches(12.3), Inches(2.4))

# ---------- Slide 8: Main Features ----------
s = slide(); header(s, "Main Features", 8)
bullets(s, Inches(0.7), Inches(1.45), Inches(11.9), Inches(5),
        ["Secure doctor accounts (JWT + bcrypt), per-user data isolation.",
         "Patient record management and persistent analysis history.",
         "X-ray upload with drag-and-drop and live preview.",
         "Automated decision + bounding-box localization + confidence score.",
         "Explainability heatmaps (Grad-CAM and related) on every prediction.",
         "Multiple models behind one registry; auto-generated Swagger API docs."], size=19)

# ---------- Slide 9: Technical Implementation ----------
s = slide(); header(s, "Technical Implementation", 9)
bullets(s, Inches(0.7), Inches(1.45), Inches(11.9), Inches(5),
        ["Frontend: Angular 21 with server-side rendering, route guards, central state + API service.",
         "Backend: FastAPI (fully async), lifespan startup that connects Mongo and warms the model.",
         "Inference service: model registry + single-load warmup + NMS + six explainability methods.",
         "Database: MongoDB (Motor) with users / patients / xray_analyses and indexes.",
         "Security: JWT, bcrypt, CORS, strict input validation, production secret-key guard.",
         "Models served from disk via Git LFS; inference runs on CPU or GPU."], size=18)

# ---------- Slide 10: Testing & Evaluation ----------
s = slide(); header(s, "Testing and Evaluation", 10)
bullets(s, Inches(0.7), Inches(1.45), Inches(11.9), Inches(2.6),
        ["Backend unit + integration tests (pytest), including per-user access-control tests.",
         "Preflight asset checker and an end-to-end inference smoke test.",
         "Metrics: AUC, precision, recall (sensitivity), specificity, F1, confusion matrix; mAP for detection."], size=18)
textbox(s, Inches(0.7), Inches(4.2), Inches(11.9), Inches(2),
        [("Experimental setup", 20, TEAL, True),
         ("RSNA dataset, DICOM->PNG, patient-wise split (20% held-out test: 4,135 normal / 1,202 pneumonia).", 18, DARK, False),
         ("Kaggle GPU (P100/T4), mixed-precision training, augmentation, early stopping.", 18, DARK, False)])

# ---------- Slide 11: Results ----------
s = slide(); header(s, "Results (held-out test set)", 11)
img_fit(s, FIG + "classification_metrics.png", Inches(0.4), Inches(1.4), Inches(6.4), Inches(3.6))
img_fit(s, FIG + "detection_metrics.png", Inches(6.7), Inches(1.4), Inches(6.2), Inches(3.6))
textbox(s, Inches(0.7), Inches(5.2), Inches(11.9), Inches(1.6),
        [("Best classifier EfficientNet-B0: AUC 0.886.  Deployed detector Faster R-CNN: recall 0.812 (mAP@0.5 0.381).", 18, NAVY, True),
         ("Recall is prioritized because a missed pneumonia is the costly error. Numbers are honest and leak-free.", 16, GREY, False)])

# ---------- Slide 12: Challenges & Lessons ----------
s = slide(); header(s, "Challenges and Lessons Learned", 12)
bullets(s, Inches(0.7), Inches(1.45), Inches(11.9), Inches(5),
        ["Found and fixed a patient-level data leak that had inflated early scores (patient-wise splitting).",
         "Served several large models efficiently with a single-load registry and warmup.",
         "Made detector predictions explainable (Eigen-CAM, occlusion) where standard saliency does not apply.",
         "Lesson: lightweight PSO/GWO/SA proxy search did not beat a tuned baseline (a real, useful finding).",
         "Lesson: honest evaluation and the clinically meaningful metric matter more than a headline number."], size=18)

# ---------- Slide 13: Conclusion ----------
s = slide(); header(s, "Conclusion", 13)
bullets(s, Inches(0.7), Inches(1.5), Inches(11.9), Inches(5),
        ["Delivered a complete, working, explainable full-stack pneumonia screening system.",
         "Five models rigorously and honestly evaluated; AUC 0.886 (classification), recall 0.812 (deployed detector).",
         "Secure, multi-user, reproducible, and competitive with the published literature.",
         "Demonstrates the full path from research model to usable clinical product."], size=20)

# ---------- Slide 14: Future Work ----------
s = slide(); header(s, "Future Work", 14)
bullets(s, Inches(0.7), Inches(1.5), Inches(11.9), Inches(5),
        ["Containerize with Docker Compose and add a CI/CD pipeline for one-command deployment.",
         "Add structured logging, metrics, monitoring, and model-drift detection in production.",
         "Out-of-distribution detection to reject non-chest or low-quality images.",
         "Extend to multi-finding detection; validate on additional, more diverse datasets.",
         "Pursue clinical validation and the regulatory path toward a certified tool."], size=20)

# ---------- Slide 15: Q&A ----------
s = slide()
rect(s, 0, 0, SW, SH, NAVY)
s.shapes.add_picture(LOGO, int((SW - Inches(2.4)) / 2), Inches(1.2), width=Inches(2.4))
textbox(s, Inches(1), Inches(3.2), Inches(11.33), Inches(1.2),
        [("Thank You", 48, WHITE, True)], align=PP_ALIGN.CENTER)
textbox(s, Inches(1), Inches(4.4), Inches(11.33), Inches(0.8),
        [("Questions and Discussion", 24, RGBColor(0xBF, 0xD7, 0xEA), True)], align=PP_ALIGN.CENTER)
textbox(s, Inches(1), Inches(5.4), Inches(11.33), Inches(1),
        [("Chest X-ray Pneumonia Detection System  -  Team 19", 16, WHITE, False),
         ("School of CSAI, Zewail City of Science and Technology  -  June 2026", 14, RGBColor(0xBF, 0xD7, 0xEA), False)], align=PP_ALIGN.CENTER)

prs.save(OUT)
print("WROTE", OUT, len(prs.slides._sldIdLst), "slides")
