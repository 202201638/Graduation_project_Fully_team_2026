# Supervisor feedback - defense slides review (2026-06-18)

Source: `2026-06-18 17-36-21.m4a` (47.5 min), auto-transcribed (Egyptian Arabic colloquial)
to `meeting_feedback_2026-06-18.txt`. Transcript is rough; this is the interpreted, actionable
summary. Supervisor: Prof. Dr. Khaled Mostafa (with Dr. Maher and other faculty present).

## Content / structure feedback

| # | Feedback | Slide(s) addressed |
|---|---|---|
| 1 | **Title:** Zewail logo clearly, title, names + IDs, then supervisor name. No photos. | 1 Title |
| 2 | **Problem Statement is not Motivation.** What the team wrote (doctor/device shortage, slow reads) is the *motivation*. The Problem Statement must state the actual problem the system solves: given a chest X-ray, decide pneumonia vs normal, localize it, and produce a report. | 2 Problem Statement |
| 3 | **Motivation** holds the reasons: radiologist scarcity, overload/time, human error, existing tools expensive/closed. | 3 Motivation & Objectives |
| 4 | **Proposed Solution: show a block diagram / workflow first** (X-ray -> preprocessing -> classification -> detection/localization -> report), explained block by block. | 5 Proposed Solution |
| 5 | **The output is an auto-filled templated report** (pneumonia probability + each detected region with coordinates). Highlight it. | 5, 8 |
| 6 | **System Architecture vs Implementation are different slides.** Architecture = the 3-tier block diagram (Angular presentation / FastAPI application / MongoDB data) and how the AI model integrates (its output feeds the app). Implementation = the technologies/libraries, on their own slide. | 6 Architecture, 9 Implementation |
| 7 | **Methodology shown as clear blocks** (preprocessing -> classification -> detection -> optimization -> evaluation -> XAI -> testing). | 7 Methodology |
| 8 | **Testing: separate the two kinds.** Software testing (unit, integration, **API testing with Postman**, UI testing) vs model evaluation (precision, recall, accuracy, mAP, per model, on the dataset; detection = is the region localized correctly). Do not conflate them. | 10 Testing & Evaluation |
| 9 | **Results:** per-model metrics + comparison + which model won + dataset size + detection localization quality. | 11 Results, backup B6/B7 |
| 10 | **Functional vs non-functional:** the features/workflow are functional; security, performance, and the optimizers are non-functional (improve the existing, no new feature). | 9 + backup |

## Delivery / logistics feedback

- **Time:** the whole talk ~15 minutes (not 15 for AI + 15 for software); up to ~30 with discussion if the panel interrupts with questions.
- **Everyone presents** a part, and **any member must be able to answer any question** (you cannot defer "that is X's part"). AI members should understand the software side and vice versa; deep AI questions go to the AI members, deep software questions to the software members.
- **Live demo** at the end (upload an X-ray -> classification + localization + report). Have a **recorded screen capture as a fallback** if the network/backend fails.
- **Slide design: high contrast.** No light-grey or light-red text on white that will not show on the projector.
- **Logistics:** keep documentation final; ask Dr. about poster printing/size (print near the project expo); put all deliverables + demo + figures on a Google Drive link, but **present from a local copy** (the Drive link failed live in the meeting).
- The person presenting the last part should be ready to compress if time runs short.

## How the deck was updated

The 15-slide template structure is unchanged. Edits: reframed Problem Statement (2) vs Motivation
(3); added the workflow **block diagram** to Proposed Solution (5) + the auto-report; strengthened
Architecture (6) to show the three tiers + AI-model integration; relabelled Testing (10) into
**Model Evaluation** vs **Software Testing** (Postman/UI/integration named); added a **Live Demo**
slide before Questions; added Postman and the functional/non-functional note; and put the delivery
tips into the title-slide speaker notes. All other technical content and the 16-slide backup are
unchanged.
