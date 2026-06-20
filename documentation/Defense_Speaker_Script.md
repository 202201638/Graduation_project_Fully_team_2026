# Defense Speaking Script - Team 19

Chest X-ray Pneumonia Detection System - final defense (~15 minutes).
Speaking order: **Moamen -> Habiba -> Ahmed -> Sarah**. Each person takes a contiguous block of
4 slides, so handoffs are clean.

| Presenter | Slides | Block |
|---|---|---|
| Moamen | 1-4 | Intro + Problem + Motivation + Literature |
| Habiba | 5-8 | Solution + Architecture + Methodology + Features |
| Ahmed | 9-12 | Implementation + Testing + Results + Challenges |
| Sarah | 13-16 | Conclusion + Future Work + Live Demo + Q&A |

**Delivery reminders (from the supervisor):** keep the whole talk to ~15 min (up to ~30 with
discussion); everyone presents; high-contrast slides; present from a local copy, not only the
Drive link; keep the recorded demo ready as a fallback.

**Q&A routing:** deep **AI / model** questions go to **Moamen & Habiba**; deep **software /
system** questions go to **Ahmed & Sarah** - no matter who presented the slide. If a question is
unclear, ask them to rephrase; if it is outside what you did, say so briefly and move on.

---

## MOAMEN - Slides 1 to 4 (intro, problem, motivation, literature)

### Slide 1 - Title
"Good morning, everyone, and thank you for being here. We are Team 19, and our graduation project
is the **Chest X-ray Pneumonia Detection System** - an explainable, full-stack deep-learning
platform that screens chest X-rays for pneumonia. I am Moamen, and with me are Habiba, Ahmed, and
Sarah; our supervisor is Prof. Dr. Khaled Mostafa. Over the next 15 minutes we will go from the
clinical problem, through our models and the system we built, to our results, and we will finish
with a live demo."
*Handoff:* "Let me start with the problem we set out to solve."

### Slide 2 - Problem Statement
"What exactly is the problem? Pneumonia is one of the most common and dangerous lung conditions,
and the chest X-ray is the first-line test to find it. The concrete task is this: **given a chest
X-ray, automatically decide whether pneumonia is present, localize where it is, and produce a
report.** Today that is done manually - it is slow and depends on radiologist expertise that many
clinics do not have enough of, and there is no accessible, explainable, end-to-end tool that does
it while keeping the doctor in control. **That gap is the problem we solve.**"
*Handoff:* "That is the problem - now, why it matters."

### Slide 3 - Motivation and Objectives
"The motivation is practical. Radiologists are scarce and X-ray volume is high, so reads get
delayed and doctors are overloaded. Manual reading is tiring and error-prone, and a missed
pneumonia is the costliest mistake - so an AI second reader saves time and catches misses. The
commercial tools that exist are closed and expensive, so smaller clinics are left out. From that
we set four objectives: rigorously and honestly evaluate our models, ship a real secure
multi-user product, attach an explanation to every prediction, and keep everything reproducible."
*Handoff:* "With the goals set, let me place our work against what already exists."

### Slide 4 - Literature and Existing Solutions
"We built on solid prior work. For classification, CheXNet - a 121-layer DenseNet - reached
radiologist-level pneumonia detection, and ImageNet-pretrained backbones transfer well to X-rays.
For localization, two families dominate: two-stage Faster R-CNN, which is accurate, and one-stage
YOLO, which is fast - both standard on the RSNA challenge, the benchmark we use. As the table
shows, commercial tools do all this but are closed and expensive, and typical academic models
stay in a notebook. **Our gap, the bottom row, is to combine leak-free evaluation across five
models with six explainability methods, delivered as an open, self-hostable product.**"
*Handoff:* "Habiba will now walk you through the solution we built."

**Questions likely for Moamen:** the clinical framing; why pneumonia and the RSNA dataset; how
this differs from CheXNet and commercial tools; why localization matters beyond classification;
and, as integration lead, how all the pieces fit together.

---

## HABIBA - Slides 5 to 8 (solution, architecture, methodology, features)

### Slide 5 - Proposed Solution
"Thanks, Moamen. Here is our solution as a workflow. A chest X-ray comes in; it goes through
**preprocessing**; **classification** decides normal versus pneumonia; **detection** localizes
the region with a bounding box; and finally the system fills a template to produce an **automatic
report**. Around that pipeline we built a doctor-facing web app: the doctor signs in, manages
patients, uploads an X-ray, and gets back a decision with a confidence score, a localized box, and
an explainability heatmap - plus that report, saved to the patient's history. Five models sit
behind one registry, Faster R-CNN is the deployed default, and the physician confirms every
result."
*Handoff:* "Let me show you how this is put together."

### Slide 6 - System Architecture
"Architecturally it is a clean three-tier system. The **presentation** tier is an Angular
front-end in the doctor's browser. The **application** tier is an async FastAPI back-end for the
REST API, authentication, and routing. The **data** tier is MongoDB, holding users, patients, and
analyses, so the API stays stateless. And the key part the panel asked us to show: **the AI model
is integrated through a dedicated inference service** that loads every model once and feeds its
output back into the app, where it is stored and displayed. So the flow is doctor, browser,
FastAPI, the model, then the result and report, saved."
*Handoff:* "Now how we actually built and trained those models."

### Slide 7 - Methodology
"Our methodology has two tracks. The research track is this **eight-phase pipeline**, run
identically for every model - data preparation, baseline training, optimization, retraining,
explainability, evaluation, and a demo. Running it the same way for each model is what makes the
comparison fair. One critical detail: in preprocessing we apply the same CLAHE contrast to every
image regardless of its label, and we split the data by patient - both to prevent leakage, which
Ahmed will return to in the results. The bottom strip is the runtime flow: upload, validate, run
the warmed model, non-max suppression, heatmap, and store."
*Handoff:* "And here is what the doctor actually gets."

### Slide 8 - Main Features
"These are the main features. Secure doctor accounts with per-user isolation - this is health
data. Patient records with a persistent history. Drag-and-drop upload with a live preview. The
core: an automated decision, a localized box, and a confidence score. An explainability heatmap on
every prediction. And a model registry with auto-generated API docs. The screenshot on the right
is the real result screen."
*Handoff:* "Ahmed will take you into the technical implementation and how we tested it."

**Questions likely for Habiba:** the AI pipeline and why it is phased; CLAHE and the patient-wise
split; why five models; classification versus detection; how the explainability heatmaps are
produced; the model-registry idea.

---

## AHMED - Slides 9 to 12 (implementation, testing, results, challenges)

### Slide 9 - Technical Implementation
"Thanks, Habiba. On the stack: the front-end is Angular 21 with server-side rendering; the
back-end is FastAPI, fully async on Uvicorn; the database is MongoDB with the async Motor driver;
the models run on PyTorch, torchvision, and Ultralytics; security is JWT with bcrypt and CORS; we
used **Postman** to design and test the API; and weights are versioned with Git LFS. Two
engineering decisions worth noting: a **single-load model registry** with startup warmup, so no
request pays a model-load cost, and **non-max suppression** to clean overlapping boxes. The
features are functional requirements; security, performance, and the optimizers are the
non-functional side."
*Handoff:* "Now how we tested all of this - and there are two different kinds of testing."

### Slide 10 - Testing and Evaluation
"This distinction matters. On the left is **model evaluation** - how good the AI is: the RSNA
dataset, a patient-wise stratified split with a 20% held-out test set of 4,135 normal and 1,202
pneumonia images, and we report AUC, recall, specificity, F1, and mAP per model - and for
detection, whether the box actually lands on the finding. On the right is **software testing** -
whether the application works: unit and integration tests with pytest, API testing with Postman on
every endpoint, UI testing of the upload-to-result flow, and access-control tests proving one
doctor cannot see another's data. Different questions, different tools."
*Handoff:* "So what did the models actually score?"

### Slide 11 - Results
"Here are the results on the held-out test set. Our best classifier is **EfficientNet-B0 at an AUC
of 0.886** - and it is also the smallest, four million parameters. Our deployed detector is
**Faster R-CNN at a recall of 0.812**, with mAP@0.5 of 0.381. We deliberately prioritize recall,
because in screening a missed pneumonia is the expensive error. These numbers are honest and
leak-free - our detection mAP sits right in the published RSNA range of about 0.32 to 0.39. If
anyone expected 0.99, that was the leak we caught, which is my next slide."
*Handoff:* "Which brings me to our challenges and what we learned."

### Slide 12 - Challenges and Lessons Learned
"Four honest lessons. First, the **data leak**: early models scored around 0.99 AUC, which was too
good - a patient-level leak plus label-correlated preprocessing. We fixed it with patient-wise
splits and uniform CLAHE, and the numbers became honest. Second, **class imbalance** - pneumonia
is the minority, about one to three-point-four - handled with weighted loss, recall-first metrics,
and augmentation. Third, **explainable detection** needed Eigen-CAM and occlusion, since standard
saliency does not apply to detectors. And fourth, our nature-inspired hyperparameter search
**did not beat the tuned baseline** under our budget, and we report that honestly rather than hide
it."
*Handoff:* "Sarah will close us out and run the demo."

**Questions likely for Ahmed:** the stack and why FastAPI and MongoDB; the model registry, warmup,
and NMS; software testing versus model testing; how authentication and per-user security work;
deployment and reproducibility. (Deep model follow-ups during Results he can pass to Habiba or
Moamen.)

---

## SARAH - Slides 13 to 16 (conclusion, future work, live demo, Q&A)

### Slide 13 - Conclusion
"Thank you, Ahmed. To bring it together: we delivered a **complete, working, explainable
full-stack pneumonia screening system**. We benchmarked five models honestly and leak-free under
one protocol - an AUC of 0.886 for classification and a recall of 0.812 for our deployed detector.
It is secure, multi-user, reproducible, and competitive with the literature. The real contribution
is the full path - from a research model all the way to a usable clinical product."
*Handoff:* "And here is where it can go next."

### Slide 14 - Future Work
"For future work: containerize with Docker and add CI/CD for one-command deployment; add
monitoring and model-drift detection in production; out-of-distribution rejection so the model
declines images it should not read; active learning that turns doctor confirmations into new
training labels; extending beyond pneumonia to multiple findings; and the clinical-validation and
regulatory path a real deployment needs."
*Handoff:* "Now let me show you the system live."

### Slide 15 - Live Demo
"Let me walk you through it live. I sign in as a doctor and open a patient. I upload a chest X-ray
- here is the live preview. The model runs, and here is the result: the pneumonia decision with
its confidence, the localized bounding box, and the explainability heatmap. And finally the
auto-generated report, saved to this patient's history."
*(Fallback if the system is down: "I will play our recorded demo instead" - have it open and
ready, running from a local copy.)*
*Handoff:* "And with that, we will take your questions."

### Slide 16 - Thank You / Q&A
"Thank you all for your attention. We are happy to take your questions."

**Questions likely for Sarah:** the front-end (Angular, SSR, route guards); the UX flow; how the
demo works end to end; the future-work rationale. (Deep model or back-end follow-ups she routes to
the right teammate.)

---

## One-line cheat sheet (numbers everyone should know)

- Dataset: **RSNA Pneumonia Detection Challenge**, ~26,684 X-rays; test split **4,135 normal /
  1,202 pneumonia** (~1:3.4), patient-wise, leak-free.
- Best classifier: **EfficientNet-B0, AUC 0.886** (smallest model, 4M params).
- Deployed detector: **Faster R-CNN, recall 0.812**, mAP@0.5 0.381 (recall-first by design).
- Five models, one registry; Faster R-CNN deployed. Stack: Angular 21 / FastAPI / MongoDB /
  PyTorch. Six explainability methods.
- The honest finding: the cheap PSO/GWO/SA search did **not** beat the tuned baseline.
