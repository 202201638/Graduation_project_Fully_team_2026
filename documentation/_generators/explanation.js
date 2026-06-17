// In-depth explanation generator. Run: NODE_PATH="$(npm root -g)" node documentation/_generators/explanation.js
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Footer, AlignmentType, LevelFormat, TableOfContents, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak, VerticalAlign,
} = require("docx");

const ROOT = "D:/Collage/graduation project";
const FIG = ROOT + "/documentation/figures/";
const LOGO = ROOT + "/Zewail Logo/11.png";
const OUT = ROOT + "/documentation/Project_Explanation_InDepth.docx";
const FONT = "Calibri";
const NAVY = "1F3B63";
const TEAL = "1D6B5F";

const txt = (s, o = {}) => new TextRun({ text: s, font: FONT, ...o });
function P(s, o = {}) {
  return new Paragraph({ alignment: o.align || AlignmentType.JUSTIFIED, spacing: { line: 288, lineRule: "auto", after: o.after == null ? 120 : o.after, before: o.before || 0 }, children: Array.isArray(s) ? s : [txt(s, o.run || {})] });
}
const H1 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 260, after: 140 }, children: [txt(s)] });
const H2 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 }, children: [txt(s)] });
const H3 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 140, after: 80 }, children: [txt(s)] });
const bullet = (s) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { line: 288, lineRule: "auto", after: 40 }, children: Array.isArray(s) ? s : [txt(s)] });
const PB = () => new Paragraph({ children: [new PageBreak()] });
function qa(q, a) {
  return [
    new Paragraph({ spacing: { before: 100, after: 20 }, children: [txt("Q: " + q, { bold: true, color: NAVY })] }),
    new Paragraph({ spacing: { after: 80 }, alignment: AlignmentType.JUSTIFIED, children: [txt("A: ", { bold: true, color: TEAL }), txt(a)] }),
  ];
}
const BD = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const BORDERS = { top: BD, bottom: BD, left: BD, right: BD };
function cell(c, w, o = {}) {
  return new TableCell({ borders: BORDERS, width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined, margins: { top: 50, bottom: 50, left: 100, right: 100 }, children: [new Paragraph({ spacing: { after: 0, line: 264, lineRule: "auto" }, children: [txt(String(c), { size: o.size || 19, bold: !!o.bold })] })] });
}
function table(headers, rows, widths) {
  const head = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { bold: true, fill: "D9E2F0" })) });
  const body = rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, widths[i])) }));
  return [new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths, rows: [head, ...body] }), new Paragraph({ spacing: { after: 120 }, children: [txt("")] })];
}
function fig(file, caption, w, h) {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 30 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(FIG + file), transformation: { width: w, height: h }, altText: { title: caption, description: caption, name: file } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 140 }, children: [txt(caption, { italics: true, size: 18, color: "777777" })] }),
  ];
}

const children = [];
const A = (...x) => children.push(...x);

// ---- Cover ----
A(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 160 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(LOGO), transformation: { width: 240, height: 142 }, altText: { title: "Zewail City", description: "logo", name: "logo" } })] }));
A(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [txt("Chest X-ray Pneumonia Detection System", { size: 40, bold: true, color: NAVY })] }));
A(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [txt("In-Depth Project Explanation", { size: 30, italics: true })] }));
A(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [txt("A complete, plain-language walkthrough of how everything works: the AI pipeline and the web application.", { size: 22 })] }));
A(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [txt("Team 19  -  School of CSAI, Zewail City of Science and Technology  -  Supervisor: Prof. Dr. Khaled Mostafa  -  June 2026", { size: 20, color: "555555" })] }));
A(P("How to read this document: it is written so that someone who has never seen the project can finish it and confidently explain every part. It has two main sections. Section A covers the AI pipeline (the data, the models, how they were trained and evaluated, and why we got the results we did). Section B covers the web application (the frontend, backend, database, security, and how a request flows end to end). Each section ends with a bank of questions the examiners are likely to ask, with answers.", { run: { italics: true } }));
A(PB());
A(H1("Table of Contents"));
A(new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }));
A(PB());

// =====================================================================
// SECTION A - AI PIPELINE
// =====================================================================
A(H1("Section A - The AI Pipeline"));
A(P("In one sentence: we take a chest X-ray image, pass it through a trained deep-learning model, and get back either a probability that the lungs show pneumonia (classification) or a box around the pneumonia region with a confidence score (detection). Everything below explains how we get from a raw medical image to that answer, and why it works."));
A(...fig("ai_pipeline.png", "Figure A1. The eight phases of the AI pipeline.", 600, 146));

A(H2("A1. The dataset: RSNA Pneumonia Detection Challenge"));
A(P("We used the RSNA Pneumonia Detection Challenge dataset, published by the Radiological Society of North America. It contains about 26,684 frontal chest X-rays, each labeled by radiologists. Crucially, it provides two kinds of labels: an image-level label (pneumonia or not) that we use for classification, and bounding boxes (the exact rectangles where lung opacity consistent with pneumonia appears) that we use for detection. We chose it because it is large, professionally annotated, widely used as a benchmark (so our numbers can be compared to others), and supports both tasks at once."));
A(P([txt("Why this matters: ", { bold: true }), txt("the quality of a model is capped by the quality of its data. Because RSNA is expert-labeled and balanced enough to be usable, our results reflect the model, not label noise we introduced ourselves.")]));

A(H2("A2. From a raw scan to a model input (preprocessing)"));
A(P("Medical scans do not arrive as ordinary images. They come as DICOM files, a medical format that stores the pixel data plus patient metadata. Our preprocessing turns each DICOM into a clean PNG the model can read, in these steps:"));
A(bullet([txt("Read the DICOM ", {}), txt("with the pydicom library to get the raw grayscale pixel array.")]));
A(bullet([txt("Robust intensity normalization: ", { bold: true }), txt("X-ray brightness varies between machines, so we clip each image to its 2nd-98th intensity percentiles and rescale to 0-255. This removes extreme outliers and makes images comparable.")]));
A(bullet([txt("CLAHE contrast enhancement: ", { bold: true }), txt("Contrast Limited Adaptive Histogram Equalization (clip limit 2.0, 8x8 tiles) locally boosts contrast so subtle lung opacities become visible. It equalizes brightness in small tiles rather than globally, which is ideal for X-rays.")]));
A(bullet([txt("Resize ", {}), txt("to a fixed size (224x224 for classifiers, 640x640 for detectors) and save the original dimensions so detection boxes can be scaled back correctly.")]));
A(P([txt("The most important lesson here (a likely exam question): ", { bold: true }), txt("our early results were suspiciously high. The cause was a data leak: contrast enhancement had been applied differently to pneumonia and normal images, so the model could 'cheat' by detecting the preprocessing instead of the disease. We fixed it by applying the exact same CLAHE to every image regardless of label. The honest, lower numbers we now report are the real ones. This is the single most valuable thing we learned: trust the protocol, not the number.")]));

A(H2("A3. Splitting the data correctly (no leakage)"));
A(P("We split the data into training, validation, and test sets at the patient level, not the image level, with a fixed random seed (42) for reproducibility. A single patient can have several X-rays; if some of a patient's images were in training and others in testing, the model could memorize that specific patient and score artificially high. Splitting by patient guarantees the test set contains people the model has never seen. The split is also stratified, meaning the pneumonia-to-normal ratio is kept the same in each part. The held-out test set is 20 percent of patients: 4,135 normal and 1,202 pneumonia images. It is never touched during training or model selection."));

A(H2("A4. Two tasks: classification and detection"));
A(P("Classification answers 'is there pneumonia anywhere in this image?' with a probability. Detection answers 'where is it?' by drawing one or more boxes, each with a confidence. We built both because doctors want both a yes/no screen and a visual pointer to the suspicious region. The deployed default is a detector (Faster R-CNN) because localization is more useful clinically."));

A(H2("A5. The models, explained from scratch"));
A(P("All five models use transfer learning: instead of learning vision from zero, they start from weights pretrained on ImageNet (a huge natural-image dataset) and are then fine-tuned on chest X-rays. This is standard in medical imaging because medical datasets are small, and the low-level features (edges, textures) learned on ImageNet transfer well."));
A(H3("The three classifiers"));
A(bullet([txt("ResNet50: ", { bold: true }), txt("a 50-layer convolutional network whose key idea is the 'residual connection', a shortcut that lets the signal skip layers. This solves the problem that very deep networks become hard to train, and made very deep networks practical.")]));
A(bullet([txt("DenseNet121: ", { bold: true }), txt("every layer is connected to every later layer, so features are reused throughout the network. It is parameter-efficient and was the backbone of CheXNet, the famous radiologist-level pneumonia model.")]));
A(bullet([txt("EfficientNet-B0: ", { bold: true }), txt("uses 'compound scaling' to balance network depth, width, and input resolution. It is our best classifier and also by far the smallest (4 million parameters), which is why we consider it the most efficient choice.")]));
A(H3("The two detectors"));
A(bullet([txt("Faster R-CNN (two-stage): ", { bold: true }), txt("first a Region Proposal Network suggests candidate boxes, then a second head classifies each box and refines its coordinates. It uses a ResNet50 backbone with a Feature Pyramid Network so it sees objects at multiple scales. It is accurate, especially in recall, which is why we deploy it.")]));
A(bullet([txt("YOLOv8 (one-stage): ", { bold: true }), txt("predicts all boxes in a single forward pass with an anchor-free head. It is much faster and smaller, but in our tests it missed many more pneumonia regions (lower recall) than Faster R-CNN.")]));

A(H2("A6. How we trained the classifiers (every parameter)"));
A(...table(["Setting", "Value", "Why"], [
  ["Optimizer", "Adam", "Adaptive, robust default for fine-tuning"],
  ["Learning rate", "1e-4", "Small, so pretrained weights are not destroyed"],
  ["Loss", "Cross-entropy, class-weighted", "Weights the rare pneumonia class so it is not ignored"],
  ["LR scheduler", "ReduceLROnPlateau (val AUC, x0.5)", "Lowers LR when validation stops improving"],
  ["Mixed precision (AMP)", "On (GPU)", "Faster training, less memory"],
  ["Early stopping", "Patience 4 on val AUC", "Stop before overfitting; restore best weights"],
  ["Augmentation (train only)", "h-flip, rotate 10, color jitter", "Teaches invariance, reduces overfitting"],
  ["Normalization", "ImageNet mean/std", "Matches the pretrained backbone"],
  ["Image size", "224 x 224", "Standard for these backbones"],
], [2300, 3100, 3600]));
A(P([txt("Two details worth highlighting. ", {}), txt("Class weighting: ", { bold: true }), txt("pneumonia is the minority class, so we weight the loss by inverse class frequency; without this, a model can score high accuracy by always predicting 'normal'. "), txt("Best-checkpoint restore: ", { bold: true }), txt("we keep the weights from the epoch with the best validation AUC, not the last epoch, so we never ship an overfitted model.")]));

A(H2("A7. How we trained the detectors"));
A(P("Faster R-CNN was trained for up to 10 epochs (learning rate 5e-3, batch size 4, weight decay 5e-4), freezing the backbone for the first epoch so the new detection heads stabilize before the whole network is fine-tuned. It optimizes the standard Faster R-CNN multi-task loss: the proposal network's objectness and box losses plus the final head's classification and box-regression losses. At inference we apply Non-Maximum Suppression to remove duplicate overlapping boxes (explained in Section B). YOLOv8 was trained through the Ultralytics pipeline with its built-in augmentation."));

A(H2("A8. Hyperparameter optimization: PSO, GWO, SA"));
A(P("To search for better settings we implemented three nature-inspired optimizers. They are all ways to search a space of configurations without trying every combination:"));
A(bullet([txt("Particle Swarm Optimization (PSO): ", { bold: true }), txt("a swarm of candidate solutions 'flies' through the search space, each pulled toward its own best result and the swarm's best, like birds flocking to food.")]));
A(bullet([txt("Grey Wolf Optimizer (GWO): ", { bold: true }), txt("models a wolf pack hierarchy; the best three solutions ('alpha, beta, delta') lead the rest of the pack toward promising regions.")]));
A(bullet([txt("Simulated Annealing (SA): ", { bold: true }), txt("inspired by cooling metal; it sometimes accepts worse solutions early (high 'temperature') to escape local traps, then settles as it cools.")]));
A(P([txt("Honest result (a likely exam question): ", { bold: true }), txt("we scored each candidate with a cheap proxy (a few epochs on part of the data) so the search fit in one GPU session. That proxy was too noisy: the settings it preferred did not survive a full retrain. So we kept the validation-best checkpoint per model instead of the search-suggested one. The lesson, that a lightweight proxy search does not automatically beat a carefully tuned baseline, is a real and defensible finding, not a failure.")]));

A(H2("A9. Evaluation metrics, explained simply"));
A(bullet([txt("Accuracy: ", { bold: true }), txt("fraction of all predictions that are correct. Misleading on imbalanced data, so we do not rely on it alone.")]));
A(bullet([txt("Recall / Sensitivity: ", { bold: true }), txt("of the truly sick patients, how many we caught. This is the most important metric here, because a missed pneumonia is dangerous.")]));
A(bullet([txt("Specificity: ", { bold: true }), txt("of the truly healthy patients, how many we correctly cleared.")]));
A(bullet([txt("Precision: ", { bold: true }), txt("of the patients we flagged, how many really had pneumonia.")]));
A(bullet([txt("F1: ", { bold: true }), txt("the balance (harmonic mean) of precision and recall.")]));
A(bullet([txt("AUC: ", { bold: true }), txt("the area under the ROC curve; the probability the model ranks a random sick patient above a random healthy one. 0.5 is random, 1.0 is perfect. It is threshold-independent, which is why we use it as our headline classification metric.")]));
A(bullet([txt("Confusion matrix: ", { bold: true }), txt("the table of true/false positives and negatives that all the above are computed from.")]));
A(bullet([txt("mAP, IoU, mAP@0.5: ", { bold: true }), txt("for detection. IoU (Intersection over Union) measures box overlap; a box counts as correct if its IoU with the truth exceeds a threshold (e.g., 0.5). mAP is the average precision across recall levels; mAP@0.5 uses a 0.5 IoU threshold, and mAP@[.5:.95] averages over stricter thresholds.")]));

A(H2("A10. Results, why we got them, and how to improve"));
A(...table(["Model", "Key metric", "Value"], [
  ["EfficientNet-B0 (best classifier)", "AUC", "0.886"],
  ["DenseNet121", "AUC", "0.883"],
  ["ResNet50", "AUC", "0.884"],
  ["Faster R-CNN (deployed detector)", "Recall / mAP@0.5", "0.812 / 0.381"],
  ["YOLOv8n", "Recall / mAP@0.5", "0.382 / 0.346"],
], [4000, 2500, 2500]));
A(...fig("confusion_matrices.png", "Figure A2. Confusion matrices for the three classifiers.", 600, 194));
A(P([txt("Why these numbers? ", { bold: true }), txt("An AUC around 0.88 is what honest pneumonia classifiers reach on this kind of data; for comparison, the well-known CheXNet reported 0.768 on a different dataset. The classifiers keep specificity high (around 0.83) while catching about 76-79 percent of pneumonia. For detection, both detectors reach a similar mAP@0.5 (about 0.35-0.38, exactly the 0.32-0.39 range reported in the literature), but Faster R-CNN recalls 0.812 of pneumonia regions versus 0.382 for YOLO. Because missing a case is the costly error, we deploy Faster R-CNN even though it is larger and slower.")]));
A(P([txt("How to get better results: ", { bold: true }), txt("train on more and more diverse data (different hospitals and machines); use higher input resolution so faint opacities survive; ensemble several models; tune the decision threshold to trade specificity for recall as a clinic prefers; add stronger, medically realistic augmentation; pretrain on a large chest-X-ray corpus before fine-tuning; and, for detection, train longer with the full (not proxy) objective. External validation on a second dataset would also make the results more trustworthy.")]));

A(H2("A11. Explainability: showing the doctor why"));
A(P("Every prediction is shown with a heatmap so the clinician can check that the model looked at the lungs, not at text or an artifact. We implemented several methods:"));
A(bullet([txt("Grad-CAM, Integrated Gradients, GradientSHAP, Score-CAM (for classifiers): ", { bold: true }), txt("these highlight the pixels that most influenced the decision, using gradients or by perturbing the image.")]));
A(bullet([txt("Eigen-CAM and occlusion sensitivity (for detectors): ", { bold: true }), txt("standard gradient saliency does not apply cleanly to detectors, so we use Eigen-CAM (which analyzes the network's activations) and occlusion (sliding a mask over the image and watching how the prediction drops).")]));
A(P("Explainability is rendered live with each request and is best-effort: if a method fails, it is skipped rather than breaking the prediction."));

A(H2("A12. Section A - Questions the examiners may ask"));
A(...qa("Why did your early results look almost perfect, and what did you do?", "They were inflated by a preprocessing data leak: contrast enhancement was applied differently to the two classes, so the model detected the preprocessing, not the disease. We fixed it by applying identical CLAHE to every image and we report the honest, lower numbers."));
A(...qa("Why split by patient instead of by image?", "Because one patient can have multiple X-rays. Splitting by image could put the same patient in both train and test, letting the model memorize that patient and score artificially high. Patient-wise splitting guarantees the test set is truly unseen."));
A(...qa("Why is recall your most important metric?", "Because in pneumonia screening a false negative (a missed case) can be life-threatening, while a false positive only leads to a second look. We optimize and select models to minimize missed cases."));
A(...qa("Why deploy Faster R-CNN instead of the faster YOLO?", "Both reach similar mAP@0.5, but Faster R-CNN recalls 0.812 of pneumonia regions versus YOLO's 0.382. We accept the larger, slower model because catching cases matters more than speed here."));
A(...qa("How did you handle class imbalance?", "We weighted the loss by inverse class frequency so the rare pneumonia class is not ignored, and we evaluate with AUC, recall, and the confusion matrix rather than accuracy alone."));
A(...qa("How do you prevent overfitting?", "Transfer learning, train-only augmentation, weight decay, a learning-rate scheduler, early stopping on validation AUC, and restoring the best-validation checkpoint rather than the last epoch."));
A(...qa("Did the metaheuristic optimization help?", "Not on our cheap proxy: PSO, GWO, and SA preferred settings that did not survive a full retrain. We therefore selected the validation-best checkpoint. The honest takeaway is that proxy search does not automatically beat a tuned baseline."));
A(...qa("Is the model safe to use clinically?", "It is decision support, not an autonomous diagnosis. The doctor confirms every result, and every prediction comes with a confidence and an explainability heatmap so it can be challenged. It would need external validation and regulatory approval before clinical use."));
A(PB());

// =====================================================================
// SECTION B - WEBAPP PIPELINE
// =====================================================================
A(H1("Section B - The Web Application Pipeline"));
A(P("The application has three tiers: a frontend the doctor sees, a backend that does the work, and a database that stores everything. A dedicated inference service inside the backend runs the AI models. This section explains each piece and then traces a single request from click to result."));
A(...fig("architecture.png", "Figure B1. The three-tier architecture plus the inference service.", 600, 349));

A(H2("B1. The frontend (Angular 21)"));
A(P("The frontend is a single-page application built with Angular, written in TypeScript. Single-page means the browser loads one app and then swaps views without full page reloads, which feels fast. Its parts:"));
A(bullet([txt("Components / pages: ", { bold: true }), txt("login, signup, dashboard, upload, processing, result, patient records, profile, and settings. Each is a self-contained piece of UI.")]));
A(bullet([txt("Routing and guards: ", { bold: true }), txt("the router maps URLs to pages; route guards block protected pages (like the dashboard) unless the user is logged in, and redirect logged-in users away from the login page.")]));
A(bullet([txt("State service: ", { bold: true }), txt("a central analysis-state service holds the current analysis and history so different pages share data without passing it around manually.")]));
A(bullet([txt("API service: ", { bold: true }), txt("one service centralizes every call to the backend, so the rest of the app never deals with HTTP directly. It attaches the login token to each request.")]));
A(bullet([txt("Server-side rendering (SSR): ", { bold: true }), txt("public pages are pre-rendered on a small Express server for a fast first paint and better link previews; the app then 'hydrates' into the interactive single-page app.")]));

A(H2("B2. The backend (FastAPI)"));
A(P("The backend is a FastAPI service in Python. FastAPI is asynchronous, meaning it can handle many requests at once without blocking: while one request waits on the database or the model, the server serves others. Its parts:"));
A(bullet([txt("Routers: ", { bold: true }), txt("the API is split by resource into auth, patients, and x-ray routers, which keeps the code organized.")]));
A(bullet([txt("Pydantic models: ", { bold: true }), txt("every request and response is validated against a typed schema, so malformed data is rejected automatically with a clear error.")]));
A(bullet([txt("Lifespan startup: ", { bold: true }), txt("when the server boots it connects to MongoDB and warms up the default model (loads it into memory once), then cleans up on shutdown.")]));
A(bullet([txt("Model warmup (singleton): ", { bold: true }), txt("the model is loaded a single time at startup and reused for every request, so users never pay the multi-second load cost. This is the key performance decision.")]));

A(H2("B3. The inference service, step by step"));
A(P("This is the heart of the backend. When an image arrives, it:"));
A(bullet([txt("Validates ", { bold: true }), txt("the file: allowed type (jpg/png/etc.), size under 10 MB, and that it actually decodes as an image.")]));
A(bullet([txt("Looks up the model ", { bold: true }), txt("in the model registry (a table mapping a model key to its weights, task, and thresholds).")]));
A(bullet([txt("Runs the model ", { bold: true }), txt("to get raw predictions (boxes and scores, or a class probability).")]));
A(bullet([txt("Applies Non-Maximum Suppression (NMS): ", { bold: true }), txt("detectors often output several overlapping boxes for one finding; NMS keeps the highest-confidence box and drops others that overlap it by more than 30 percent, so the doctor sees one clean box per region.")]));
A(bullet([txt("Renders ", { bold: true }), txt("the annotated image and an explainability heatmap.")]));
A(bullet([txt("Returns ", { bold: true }), txt("a structured result: decision, boxes, confidence, processing time, and image paths, which the backend then saves.")]));
A(P([txt("Confidence thresholds: ", { bold: true }), txt("a detection above 0.10 is shown as 'suspected'; above 0.25 it is treated as a confident finding. These thresholds are configurable per model in the registry.")]));
A(...fig("dataflow.png", "Figure B2. The prediction data flow.", 600, 142));

A(H2("B4. Security"));
A(bullet([txt("JWT authentication: ", { bold: true }), txt("on login the server issues a signed JSON Web Token (a tamper-proof ticket with an expiry). The browser sends it on every request; the server verifies the signature to know who you are, without storing sessions.")]));
A(bullet([txt("bcrypt password hashing: ", { bold: true }), txt("passwords are never stored in plaintext. bcrypt adds a random salt and is deliberately slow, which makes stolen password databases very hard to crack.")]));
A(bullet([txt("Per-user authorization: ", { bold: true }), txt("every database query is filtered by the logged-in doctor's id, so one doctor can never read another's patients. This is tested.")]));
A(bullet([txt("Input validation and CORS: ", { bold: true }), txt("uploads are checked before they reach a model, and the API only accepts requests from known frontend origins.")]));
A(bullet([txt("Production secret guard: ", { bold: true }), txt("the server refuses to start in production with the default secret key, preventing a common, dangerous deployment mistake.")]));

A(H2("B5. The database (MongoDB)"));
A(P("We use MongoDB, a document database, through the asynchronous Motor driver. It has three collections: users, patients, and xray_analyses. We chose a document database because one analysis is naturally one self-contained document (its boxes, scores, heatmap paths, and timestamps are always read together), which maps cleanly to a JSON-like document and avoids complex joins. Unique indexes enforce that emails and identifiers are not duplicated, and a compound index on owner plus creation time makes loading a doctor's history fast."));

A(H2("B6. The API"));
A(...table(["Endpoint", "Method", "What it does"], [
  ["/api/auth/signup, /login, /me", "POST/GET", "Register, log in (returns a token), get current user"],
  ["/api/patients", "CRUD", "Create, read, update, delete patients (per doctor)"],
  ["/api/xray/upload", "POST", "Upload an image, run inference, save the result"],
  ["/api/xray, /api/xray/{id}", "GET/DELETE", "List or manage saved analyses"],
  ["/health, /docs", "GET", "Health check; interactive Swagger documentation"],
], [3600, 1600, 3800]));

A(H2("B7. A full request, traced end to end"));
A(P("1) The doctor logs in; the frontend stores the JWT. 2) They open a patient and upload an X-ray; the upload page shows a preview. 3) The frontend's API service POSTs the image (with the token) to /api/xray/upload. 4) FastAPI verifies the token, validates the file, and hands it to the inference service. 5) The warmed model predicts; NMS cleans the boxes; a heatmap is rendered. 6) The result is written to the xray_analyses collection and the annotated image is saved. 7) The backend returns the structured result; the frontend shows it on the result screen and adds it to the patient's history."));

A(H2("B8. Deployment and configuration"));
A(bullet([txt("Configuration ", { bold: true }), txt("lives in environment variables (the database URL, the secret key, allowed origins, token expiry), kept out of version control.")]));
A(bullet([txt("Model weights ", { bold: true }), txt("are stored with Git LFS because they are large binary files, so the repository stays small and clones fetch them on demand.")]));
A(bullet([txt("Scaling: ", { bold: true }), txt("the API keeps no per-user state in memory (all state is in the database and the token), so it can be cloned behind a load balancer; the model can also be moved to its own service for heavy load.")]));
A(bullet([txt("Running it: ", { bold: true }), txt("start MongoDB, run the backend with Uvicorn, build and serve the Angular frontend; full steps are in the README and the thesis user guide.")]));

A(H2("B9. Section B - Questions the examiners may ask"));
A(...qa("Why FastAPI and async?", "Inference and database calls involve waiting; an async server keeps serving other users during that wait, so the app stays responsive under load without a thread per request."));
A(...qa("Why MongoDB instead of a SQL database?", "An analysis is one self-contained nested document that we always read as a whole, which fits a document store naturally and avoids multi-table joins. We still enforce structure with indexes and validation."));
A(...qa("How does login actually work?", "On login we verify the bcrypt-hashed password and issue a signed JWT with an expiry. The browser sends that token on each request; the server verifies the signature to identify the user without server-side sessions."));
A(...qa("How do you stop one doctor seeing another's patients?", "Every query is filtered by the authenticated doctor's id, so records that are not theirs simply return not-found. We have an automated test that proves cross-user access is rejected."));
A(...qa("Why load the model once at startup?", "Loading a model takes seconds; doing it per request would make the app slow. We load it once (warmup) and reuse it, so each prediction is fast and memory use is predictable."));
A(...qa("What is NMS and why do you need it?", "Non-Maximum Suppression removes duplicate overlapping detection boxes, keeping the most confident one per region (here, when overlap exceeds 30 percent), so the doctor sees one clean box instead of several."));
A(...qa("How do you keep uploads safe?", "We validate type, size, and that the file decodes as an image before it reaches a model; the API is behind authentication and CORS; and secrets are kept in environment variables, not in code."));
A(...qa("How would you scale this to a hospital?", "The API is stateless, so we run several copies behind a load balancer, move the model to a dedicated inference service or GPU server, and use a managed MongoDB cluster. Containerization and monitoring are the immediate next steps."));

const doc = new Document({
  creator: "Team 19 - CSAI, Zewail City",
  title: "Chest X-ray Pneumonia Detection System - In-Depth Explanation",
  styles: {
    default: { document: { run: { font: FONT, size: 22 }, paragraph: { spacing: { line: 288, lineRule: "auto" } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, font: FONT, color: NAVY }, paragraph: { spacing: { before: 260, after: 140 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: FONT, color: NAVY }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, font: FONT, color: TEAL }, paragraph: { spacing: { before: 140, after: 80 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 520, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [txt("In-Depth Project Explanation  |  Chest X-ray Pneumonia Detection System  |  Team 19  |  ", { size: 16, color: "888888" }), new TextRun({ children: ["Page ", PageNumber.CURRENT], font: FONT, size: 16, color: "888888" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("WROTE", OUT, buf.length, "bytes"); });
