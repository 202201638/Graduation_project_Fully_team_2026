// Thesis generator for "Chest X-ray Pneumonia Detection System"
// Run: NODE_PATH="$(npm root -g)" node documentation/_generators/thesis.js
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Header, Footer, AlignmentType, LevelFormat, TableOfContents, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak, VerticalAlign,
} = require("docx");

const ROOT = "D:/Collage/graduation project";
const FIG = ROOT + "/documentation/figures/";
const LOGO = ROOT + "/Zewail Logo/11.png";
const OUT = ROOT + "/documentation/Graduation_Thesis_Chest_Xray_Pneumonia_Detection.docx";
const TNR = "Times New Roman";
const NAVY = "1F3B63";
const CW = 9072; // content width DXA (A4, 2.5cm margins)

// ---------- helpers ----------
const txt = (s, o = {}) => new TextRun({ text: s, font: TNR, ...o });
function P(s, o = {}) {
  return new Paragraph({
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { line: 360, lineRule: "auto", after: o.after == null ? 120 : o.after, before: o.before || 0 },
    children: Array.isArray(s) ? s : [txt(s, o.run || {})],
    ...(o.p || {}),
  });
}
const H1 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 240, after: 160 }, children: [txt(s)] });
const H2 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 180, after: 120 }, children: [txt(s)] });
const H3 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 140, after: 100 }, children: [txt(s)] });
const bullet = (s) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { line: 360, lineRule: "auto", after: 40 }, children: Array.isArray(s) ? s : [txt(s)] });
const ref = (s) => new Paragraph({ numbering: { reference: "refs", level: 0 }, spacing: { line: 300, lineRule: "auto", after: 60 }, children: [txt(s)] });
const PB = () => new Paragraph({ children: [new PageBreak()] });
function center(s, o = {}) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: o.after == null ? 80 : o.after, before: o.before || 0 }, children: Array.isArray(s) ? s : [txt(s, o.run || {})] });
}
function fig(file, n, caption, wPx, hPx) {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(FIG + file), transformation: { width: wPx, height: hPx }, altText: { title: caption, description: caption, name: file } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 140 }, children: [txt(`Figure ${n}. ${caption}`, { italics: true, size: 20 })] }),
  ];
}
function imgAbs(absPath, n, caption, wPx, hPx, type = "png") {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 }, children: [new ImageRun({ type, data: fs.readFileSync(absPath), transformation: { width: wPx, height: hPx }, altText: { title: caption, description: caption, name: caption } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 140 }, children: [txt(`Figure ${n}. ${caption}`, { italics: true, size: 20 })] }),
  ];
}
const BD = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const BORDERS = { top: BD, bottom: BD, left: BD, right: BD };
function cell(content, w, opts = {}) {
  const kids = Array.isArray(content) ? content : [new Paragraph({ spacing: { line: 276, lineRule: "auto", after: 0 }, children: [txt(String(content), { size: opts.size || 20, bold: !!opts.bold, color: opts.color })] })];
  return new TableCell({ borders: BORDERS, width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR, color: "auto" } : undefined, margins: { top: 60, bottom: 60, left: 110, right: 110 }, children: kids });
}
function table(headers, rows, widths, capN, caption) {
  const colW = widths;
  const head = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, colW[i], { bold: true, fill: "D9E2F0", size: 20 })) });
  const body = rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, colW[i], { size: 20 })) }));
  const t = new Table({ width: { size: colW.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: colW, rows: [head, ...body] });
  const out = [t];
  if (caption) out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 160 }, children: [txt(`Table ${capN}. ${caption}`, { italics: true, size: 20 })] }));
  return out;
}

// ---------- cover ----------
const cover = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 120 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(LOGO), transformation: { width: 250, height: 148 }, altText: { title: "Zewail City", description: "Zewail City logo", name: "logo" } })] }),
  center("Zewail City of Science and Technology", { run: { size: 26, bold: true, color: NAVY } }),
  center("School of Computational Sciences and Artificial Intelligence (CSAI)", { run: { size: 24 } }),
  center("Graduation Project Report", { run: { size: 24, italics: true }, after: 320 }),
  center("Chest X-ray Pneumonia Detection System", { run: { size: 40, bold: true, color: NAVY }, after: 80 }),
  center("An AI-Assisted Web Platform for Pneumonia Screening and Localization from Chest Radiographs", { run: { size: 22, italics: true }, after: 320 }),
  center("Submitted by", { run: { size: 24, bold: true }, after: 120 }),
];
const studentRows = [
  ["Moamen Elsayed Elsharkawy", "202202015", "CSAI"],
  ["Habiba Ayman Amin", "202202088", "CSAI"],
  ["Ahmed Gamal Abdelfattah", "202201638", "CSAI"],
  ["Sara Mostafa Ali", "202201305", "CSAI"],
];
const coverTable = table(["Student Name", "Student ID", "Program"], studentRows, [4400, 2400, 2272]);
const cover2 = [
  new Paragraph({ spacing: { after: 200 }, children: [txt("")] }),
  center([txt("Supervisor: ", { size: 24, bold: true }), txt("Prof. Dr. Khaled Mostafa", { size: 24 })]),
  center([txt("Team Number: ", { size: 24, bold: true }), txt("19", { size: 24 }), txt("    |    ", { size: 24 }), txt("Academic Program: ", { size: 24, bold: true }), txt("CSAI", { size: 24 })], { after: 240 }),
  center("Submitted in Partial Fulfillment of the Requirements for the Degree of", { run: { size: 22, italics: true }, after: 40 }),
  center("Bachelor of Science in Computational Sciences and Artificial Intelligence", { run: { size: 22, italics: true }, after: 240 }),
  center("Date: June 2026", { run: { size: 24, bold: true } }),
  PB(),
];

// ---------- abstracts ----------
const absEn = [
  H1("Abstract"),
  P("Pneumonia remains one of the leading causes of illness and death worldwide, and the chest X-ray is the first-line tool used to detect it. In many clinics, however, the number of radiographs far exceeds the number of radiologists available to read them, which delays diagnosis and increases the chance of human error and missed cases. This project presents the Chest X-ray Pneumonia Detection System, a complete, doctor-facing web application that uses deep learning to support pneumonia screening from chest radiographs. The system lets a physician register, create patient records, upload an X-ray image, and receive an automated reading that includes whether pneumonia is likely present, where the suspicious region is located as a bounding box, a numeric confidence score, and a visual heatmap that explains the model decision. Every result is stored per patient so it can be reviewed later."),
  P("The platform is built as a modular three-tier system: an Angular single-page frontend with server-side rendering, an asynchronous FastAPI backend, and a MongoDB database, with a PyTorch inference layer that serves five trained models through a single model registry. Two of these are object detectors that localize pneumonia (Faster R-CNN and YOLOv8), and three are image classifiers (ResNet50, DenseNet121, and EfficientNet-B0). All models were trained and evaluated on the RSNA Pneumonia Detection Challenge dataset using a leak-free, patient-wise split. On the held-out test set, the strongest classifier (EfficientNet-B0) reached an AUC of 0.886, and the deployed detector (Faster R-CNN) reached a recall of 0.812, which is the property that matters most clinically because it minimizes missed pneumonia. Authentication uses JSON Web Tokens with hashed passwords, and every prediction is accompanied by explainability so the clinician stays in control of the final decision. The result is a reproducible, end-to-end system that demonstrates how modern AI can be embedded into a practical clinical workflow rather than left as an isolated model."),
];
const absAr = [
  H1("الملخص (Arabic Abstract)"),
  new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { line: 360, lineRule: "auto", after: 120 }, children: [new TextRun({ text: "يُعد الالتهاب الرئوي من أكثر الأمراض انتشارًا وخطورة على مستوى العالم، وتُعتبر أشعة الصدر السينية الأداة الأولى لاكتشافه. إلا أن أعداد صور الأشعة في كثير من المستشفيات تفوق بكثير عدد أطباء الأشعة المتاحين لقراءتها، مما يؤخر التشخيص ويزيد من احتمال الخطأ البشري وإغفال بعض الحالات. يقدم هذا المشروع نظام الكشف عن الالتهاب الرئوي من أشعة الصدر، وهو تطبيق ويب متكامل موجَّه للأطباء يستخدم التعلم العميق لمساعدتهم في فحص الالتهاب الرئوي من صور الأشعة. يتيح النظام للطبيب تسجيل الدخول وإنشاء ملفات المرضى ورفع صورة الأشعة، ثم يحصل على قراءة آلية تتضمن احتمالية وجود الالتهاب الرئوي، وموقعه على الصورة في صورة مربع تحديد، ودرجة ثقة رقمية، وخريطة حرارية توضح أساس قرار النموذج.", font: TNR, rightToLeft: true, size: 24 })] }),
  new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { line: 360, lineRule: "auto", after: 120 }, children: [new TextRun({ text: "بُني النظام على ثلاث طبقات: واجهة أمامية باستخدام Angular، وخادم خلفي غير متزامن باستخدام FastAPI، وقاعدة بيانات MongoDB، إضافة إلى طبقة استدلال باستخدام PyTorch تقدم خمسة نماذج مدربة عبر سجل نماذج موحد. اثنان منها نموذجا كشف يحددان موقع الالتهاب (Faster R-CNN وYOLOv8)، وثلاثة نماذج تصنيف (ResNet50 وDenseNet121 وEfficientNet-B0). دُرِّبت جميع النماذج وقُيِّمت على بيانات تحدي RSNA باستخدام تقسيم خالٍ من تسرب البيانات على مستوى المريض. على مجموعة الاختبار، حقق أفضل نموذج تصنيف (EfficientNet-B0) مساحة تحت المنحنى بلغت 0.886، وحقق النموذج المنشور للكشف (Faster R-CNN) معدل استرجاع بلغ 0.812، وهو الأهم سريريًا لأنه يقلل من الحالات المُغفَلة. يعتمد التحقق من الهوية على رموز JWT مع تشفير كلمات المرور، وكل تنبؤ مصحوب بتفسير بصري يُبقي القرار النهائي بيد الطبيب.", font: TNR, rightToLeft: true, size: 24 })] }),
  PB(),
];

// ---------- TOC ----------
const toc = [
  H1("Table of Contents"),
  P("This table of contents is generated automatically. In Microsoft Word, right-click it and choose Update Field to populate page numbers. Figures and tables are captioned throughout the document.", { run: { italics: true, size: 20 } }),
  new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
  PB(),
];

// ---------- Chapter 1 ----------
const ch1 = [
  H1("Chapter 1 - Introduction"),
  H2("1.1 Background"),
  P("Healthcare systems everywhere are under growing pressure to read more medical images with fewer specialists. Chest radiography, the chest X-ray, is the most common imaging examination in the world because it is fast, inexpensive, and widely available. It is also the standard first step when a clinician suspects pneumonia, an infection that inflames the air sacs of the lungs and appears on an X-ray as a hazy region of increased opacity. The challenge is that reading these images correctly requires expert training, and that expertise is scarce. A single emergency department can generate hundreds of radiographs in a day, while only one or two radiologists may be on duty to interpret them."),
  P("Over the last decade, deep learning, and in particular convolutional neural networks, has reached a level of performance on medical images that makes computer-assisted reading genuinely useful. Rather than replacing the doctor, these models act as a fast second reader: they flag images that look abnormal, point to the region that drives their decision, and let the clinician focus attention where it matters. This project sits in exactly that space."),
  H2("1.2 Problem Statement"),
  P("Manual interpretation of chest X-rays for pneumonia is slow, depends on scarce expertise, and is vulnerable to fatigue and inter-reader variability. There is a need for a practical, accessible system that can screen chest radiographs automatically, highlight suspicious regions, quantify its confidence, and keep a reviewable record per patient, all while keeping the physician firmly in control of the final diagnosis."),
  H2("1.3 Motivation"),
  P("The motivation is both clinical and engineering. Clinically, an automated screening aid can shorten the time to diagnosis and reduce missed cases, which is the most dangerous type of error in pneumonia. From an engineering standpoint, most academic AI work stops at a model in a notebook. We wanted to show the full path: take research-grade models and deliver them inside a secure, usable, end-to-end product that a doctor could actually operate."),
  H2("1.4 Proposed Solution"),
  P("We built the Chest X-ray Pneumonia Detection System, a web application in which a physician signs in, manages patient records, uploads a chest X-ray, and receives an automated reading. The backend runs a deep-learning model that returns a pneumonia decision, a bounding box for localization, a confidence score, and an explainability heatmap. Results are persisted per patient. The system supports multiple models behind one registry, with Faster R-CNN selected as the deployed default because it gives the best localization recall."),
  H2("1.5 Objectives"),
  bullet("Train and rigorously evaluate deep-learning models for pneumonia detection and localization on a public, professionally labeled dataset."),
  bullet("Deliver a secure, multi-user web application with authentication, patient management, and persistent analysis history."),
  bullet("Provide visual explainability with every prediction so the result is interpretable and trustworthy."),
  bullet("Build the system so it is reproducible, documented, and maintainable, not a one-off script."),
  H2("1.6 Scope of the Project"),
  P("The system targets binary pneumonia screening (pneumonia versus normal) on adult chest radiographs, delivered as a decision-support tool for clinicians. It is not a certified medical device and does not make an autonomous diagnosis; the physician reviews and confirms every result. Image acquisition, hospital information system integration, and regulatory certification are outside the current scope and are discussed as future work."),
  H2("1.7 Challenges Addressed"),
  bullet("A data leak in early preprocessing that produced unrealistically high scores, which we found and fixed with patient-wise splitting and uniform image processing."),
  bullet("Serving several large models efficiently from one backend without reloading them on every request."),
  bullet("Making detection results explainable, including for detectors where standard saliency methods do not apply directly."),
  bullet("Integrating an asynchronous Python AI backend with a modern Angular frontend and a document database in a clean, secure way."),
  H2("1.8 Contributions of the Work"),
  bullet("A reproducible, leak-free training and evaluation pipeline that benchmarks five architectures on the RSNA dataset."),
  bullet("A production-style inference service with a model registry, single-load warmup, non-maximum suppression, and six explainability methods."),
  bullet("A complete, secure full-stack application that turns those models into a usable clinical workflow."),
  bullet("An honest evaluation that calibrates the results against the published literature rather than overstating them."),
  H2("1.9 Report Organization"),
  P("Chapter 2 presents the market and business case. Chapter 3 reviews related work and background. Chapter 4 describes the system design. Chapter 5 details the implementation. Chapter 6 covers testing and evaluation, and Chapter 7 presents and discusses the results. Chapter 8 addresses ethics, compliance, and standards. Chapter 9 concludes and outlines future work. References and two appendices, a user guide and supporting material, follow."),
  PB(),
];

// ---------- Chapter 2 ----------
const ch2 = [
  H1("Chapter 2 - Market Visibility and Business Case"),
  H2("2.1 Market Relevance"),
  P("Pneumonia is a high-volume, high-impact clinical problem. It is among the leading causes of hospitalization and death globally, and chest radiography is the workhorse imaging test used to triage it. The global medical-imaging AI market has grown rapidly precisely because imaging volume is rising faster than the supply of radiologists. Tools that help clinicians read more images, more consistently, and faster therefore address a real and growing demand."),
  H2("2.2 Target Users and Stakeholders"),
  bullet("Primary users: general physicians, emergency and internal-medicine doctors, and radiologists who need a fast second read."),
  bullet("Healthcare facilities: clinics and hospitals, especially in under-served regions where specialist radiologists are scarce."),
  bullet("Patients: the ultimate beneficiaries through faster, more consistent screening."),
  bullet("Health administrators: who care about throughput, turnaround time, and auditability."),
  H2("2.3 Existing Market Gaps"),
  P("Commercial chest-imaging AI exists, but it is often expensive, closed, and tied to specific hospital infrastructure. Many academic prototypes, on the other hand, never leave the notebook: they report a metric but provide no usable interface, no patient record, no security, and no explanation. The gap we target is a practical, transparent, end-to-end screening tool that is interpretable by design and simple to operate."),
  H2("2.4 Competitive Analysis"),
  ...table(["Solution", "Type", "Localization", "Explainability", "Accessibility"], [
    ["Lunit INSIGHT CXR", "Commercial", "Yes", "Heatmaps", "Enterprise, paid"],
    ["Aidoc", "Commercial", "Yes", "Limited", "Enterprise, paid"],
    ["qure.ai qXR", "Commercial", "Yes", "Heatmaps", "Enterprise, paid"],
    ["Typical academic model", "Research", "Sometimes", "Rare", "Notebook only"],
    ["This project", "Academic, full-stack", "Yes (boxes)", "6 methods", "Open, self-hostable"],
  ], [2400, 1700, 1500, 1700, 1772], 1, "Comparison of our system with representative existing solutions."),
  H2("2.5 Potential Impact, Innovation, and Sustainability"),
  P("The system can reduce time-to-screening and act as a safety net that lowers missed-case rates, which has direct clinical value. Its innovation is not a single new algorithm but the combination of rigorous, leak-free evaluation, multi-model flexibility through a registry, and explainability on every prediction, all delivered as a working product. Because the models are self-hosted and run on commodity hardware (inference works on CPU), the running cost is low and the design is sustainable for resource-constrained settings."),
  H2("2.6 Feasibility, Scalability, and Commercialization"),
  P("Technically the project is already feasible: it is implemented and runs end to end. The architecture is stateless at the API layer, so it scales horizontally behind a load balancer, and the model can be moved to its own service for heavier loads. Commercially, the natural path is a hosted SaaS offering for clinics, or an on-premise deployment for hospitals with data-residency requirements, with the explainability and audit trail as differentiators."),
  PB(),
];

// ---------- Chapter 3 ----------
const ch3 = [
  H1("Chapter 3 - Literature Review and Needed Background"),
  H2("3.1 Deep Learning for Chest X-ray Analysis"),
  P("Convolutional neural networks (CNNs) learn hierarchical visual features directly from pixels and have become the standard approach for medical image classification. A landmark example is CheXNet, a 121-layer DenseNet trained on the ChestX-ray14 dataset, which reported radiologist-level performance on pneumonia detection and popularized transfer learning for chest radiographs. Subsequent work confirmed that ImageNet-pretrained backbones such as ResNet, DenseNet, and EfficientNet provide strong starting points that fine-tune well on smaller medical datasets."),
  H2("3.2 Object Detection for Localization"),
  P("Classification alone tells the clinician whether pneumonia is likely, but not where. Object detection adds localization. Two families dominate: two-stage detectors such as Faster R-CNN, which first proposes candidate regions and then classifies and refines them, and one-stage detectors such as the YOLO family, which predict boxes directly in a single pass and are faster but often less sensitive on small or diffuse findings. Both were used in solutions to the RSNA Pneumonia Detection Challenge, the dataset we adopt."),
  H2("3.3 The RSNA Pneumonia Detection Challenge"),
  P("The RSNA Pneumonia Detection Challenge dataset, curated by the Radiological Society of North America, contains roughly 26,684 frontal chest radiographs with expert bounding-box annotations of lung opacities consistent with pneumonia. It is widely used as a benchmark because it is large, professionally labeled, and provides both image-level labels and box annotations, which makes it suitable for classification and detection alike."),
  H2("3.4 Explainable AI for Medical Imaging"),
  P("Trust requires explanation. Gradient-based methods such as Grad-CAM, Integrated Gradients, and GradientSHAP attribute a prediction back to image regions; gradient-free methods such as Score-CAM, Eigen-CAM, and occlusion sensitivity perturb or analyze activations instead. For a clinical tool, these visual explanations are essential: they let the physician verify that the model is looking at the lungs and not at an irrelevant artifact."),
  H2("3.5 Comparative Analysis and Positioning"),
  P("Most prior work optimizes a single metric on a single model, and many report inflated numbers because of data leakage between train and test at the patient level. Our work differs in three ways: we benchmark five architectures under one consistent, leak-free protocol; we deploy the result inside a secure, usable application rather than a notebook; and we attach explainability to every prediction. We also report honest numbers and calibrate them against the literature, where RSNA detection mAP typically sits between 0.32 and 0.39."),
  PB(),
];

// ---------- Chapter 4 ----------
const ch4 = [
  H1("Chapter 4 - System Design"),
  H2("4.1 Functional Requirements"),
  ...table(["ID", "Requirement"], [
    ["FR-1", "A doctor can register, log in, and log out securely."],
    ["FR-2", "A doctor can create, view, update, and delete patient records."],
    ["FR-3", "A doctor can upload a chest X-ray image for analysis."],
    ["FR-4", "The system runs inference and returns a pneumonia decision, bounding box, confidence, and heatmap."],
    ["FR-5", "Each analysis is saved and linked to its patient and owning doctor."],
    ["FR-6", "A doctor can browse the history of past analyses."],
    ["FR-7", "A doctor can only access their own patients and analyses."],
  ], [1200, 7872], 2, "Core functional requirements."),
  H2("4.2 Use Cases and User Flow"),
  P("The main use case is a single, linear clinical flow: the doctor authenticates, selects or creates a patient, uploads an X-ray, waits on a processing screen while inference runs, and then reviews a result screen showing the annotated image, the confidence, and a recommendation. The result is stored and appears in the patient history. Figure 2 shows this data flow."),
  H2("4.3 Non-Functional Requirements"),
  ...table(["Attribute", "Target / Approach"], [
    ["Security", "JWT authentication, bcrypt password hashing, per-user authorization, input validation."],
    ["Performance", "Models loaded once at startup (warmup); async I/O for non-blocking requests."],
    ["Scalability", "Stateless API behind a load balancer; database holds all state."],
    ["Reliability", "Health endpoint; best-effort explainability that never crashes a prediction."],
    ["Maintainability", "Modular routers, a model registry, and a reproducible AI pipeline."],
    ["Usability", "Clean Angular UI with a guided, linear workflow."],
  ], [2400, 6672], 3, "Non-functional requirements."),
  H2("4.4 Architecture Design"),
  P("The system follows a modular three-tier architecture. An Angular single-page application (with server-side rendering) is the presentation layer; an asynchronous FastAPI service is the application layer; and MongoDB is the data layer. A dedicated inference service inside the backend owns all model logic and loads weights from a model registry. Figure 1 shows the high-level architecture."),
  ...fig("architecture.png", 1, "High-level system architecture (three tiers plus the inference service and model registry).", 600, 349),
  ...fig("dataflow.png", 2, "End-to-end prediction data flow, from upload to stored, displayed result.", 600, 142),
  H2("4.5 Database Design"),
  P("The database uses three MongoDB collections: users, patients, and xray_analyses. A user owns many patients, and each patient has many analyses. Unique indexes enforce email and identifier uniqueness, and a compound index on owner and creation time supports fast history queries. Figure 3 shows the entity relationships."),
  ...fig("erd.png", 3, "Entity relationship diagram for the three MongoDB collections.", 580, 274),
  H2("4.6 API Design"),
  ...table(["Endpoint", "Method", "Purpose"], [
    ["/api/auth/signup, /login, /me", "POST/GET", "Authentication and current user."],
    ["/api/patients", "CRUD", "Patient record management."],
    ["/api/xray/upload", "POST", "Upload, run inference, persist result."],
    ["/api/xray, /api/xray/{id}", "GET/DELETE", "List and manage analyses."],
    ["/api/xray/status, /metadata", "GET", "Model status and metadata."],
    ["/health, /docs", "GET", "Health check and OpenAPI (Swagger) documentation."],
  ], [3500, 1500, 4072], 4, "Main REST API endpoints. Full OpenAPI docs are auto-generated at /docs."),
  H2("4.7 Deployment Architecture and Technology Stack"),
  ...table(["Layer", "Technology"], [
    ["Frontend", "Angular 21 (TypeScript), server-side rendering via Express"],
    ["Backend", "FastAPI (Python), Uvicorn ASGI server, async I/O"],
    ["Database", "MongoDB with the Motor async driver"],
    ["AI / ML", "PyTorch, torchvision, Ultralytics; FAISS-free, self-hosted weights"],
    ["Auth & Security", "JWT (python-jose), bcrypt (passlib), CORS"],
    ["Model storage", "Git LFS for the .pt checkpoints"],
  ], [2400, 6672], 5, "Technology stack by layer."),
  H2("4.8 UI / UX Design"),
  P("The interface is intentionally simple and linear so a busy clinician can move from upload to result with no training. The main screens are the dashboard, the upload page with drag-and-drop and live preview, a processing screen, the result screen with the annotated image and confidence, and the patient-records and history views. Navigation is guarded so that protected pages require authentication. A sample annotated model output is shown in Figure 4."),
  ...imgAbs(ROOT + "/Backend/model_assets/demo_output.png", 4, "Sample detector output: the predicted pneumonia region drawn on a chest radiograph.", 320, 320),
  PB(),
];

// ---------- Chapter 5 ----------
const ch5 = [
  H1("Chapter 5 - Implementation Details"),
  P("This chapter describes the main modules. For each, we give its purpose, the technologies used, its internal workflow, and the key engineering decisions."),
  H2("5.1 Authentication Module"),
  P("Purpose: secure, multi-user access. Technologies: FastAPI dependencies, python-jose for JSON Web Tokens, passlib with bcrypt for password hashing. Workflow: on signup the password is hashed with a per-password salt and never stored in plaintext; on login the server issues a signed JWT with an expiry; protected endpoints require a valid bearer token, which is decoded and verified on each request. A production guard refuses to start the server if it is run in production mode with the default secret key, preventing a common deployment mistake."),
  H2("5.2 AI / ML Inference Module"),
  P("Purpose: turn an uploaded image into a clinical reading. The module is a single inference service that holds a model registry mapping a model key to its weights, task, and thresholds. At startup the default model is warmed up, that is loaded once into memory, so requests do not pay the load cost. A request validates the image, runs the model, applies non-maximum suppression (NMS) to remove overlapping duplicate boxes, renders the annotated image, generates an explainability heatmap, and returns a structured result. Faster R-CNN is the deployed default detector; the registry also exposes YOLOv8 and the three classifiers."),
  P("Key decisions: a single warmed model instance keeps latency low and memory predictable; NMS with an intersection-over-union threshold of 0.30 prevents duplicate boxes; and explainability is best-effort, meaning that if a heatmap method fails it is skipped rather than failing the whole prediction. Figure 5 shows the AI pipeline that produced these models."),
  ...fig("ai_pipeline.png", 5, "The eight-phase AI pipeline used to prepare, train, optimize, and deploy the models.", 600, 146),
  H2("5.3 Backend Services"),
  P("Purpose: orchestrate authentication, patient management, inference, and persistence. Technology: FastAPI with fully asynchronous request handling and a lifespan context that connects to MongoDB and warms the model on startup and cleans up on shutdown. Routers are split by resource (auth, patients, x-ray) for clarity, and Pydantic models validate every request and response."),
  H2("5.4 Frontend Application"),
  P("Purpose: the doctor-facing interface. Technology: Angular 21 with server-side rendering for fast first paint and better SEO on public pages. State is held in a central analysis-state service, routing is protected by authentication guards, and a single API service centralizes all backend calls so the rest of the app never talks to HTTP directly. The build is a standard Angular production build that prerenders the public routes."),
  H2("5.5 Database Layer"),
  P("Purpose: durable storage of users, patients, and analyses. Technology: MongoDB through the asynchronous Motor driver. We chose a document database because one analysis is naturally a single nested document (boxes, scores, heatmap paths, timestamps) that is always read as a whole. Indexes are created at connection time to guarantee uniqueness and to make per-user history queries fast."),
  H2("5.6 Hyperparameter Optimization"),
  P("To tune the models we implemented three nature-inspired search algorithms: Particle Swarm Optimization (PSO), Grey Wolf Optimizer (GWO), and Simulated Annealing (SA). Each candidate configuration was scored with a fast proxy (few epochs on a data fraction) so the search fit within a single GPU session, and the best configuration across the three was kept. As discussed in Chapter 7, this search did not beat a carefully tuned baseline, which is itself a meaningful engineering finding."),
  H2("5.7 Security and Deployment Considerations"),
  P("Secrets are read from environment variables and kept out of version control; large model weights are tracked with Git LFS; CORS is restricted to known origins; and uploads are validated for type, size, and decodability before they ever reach a model. The application is designed to be containerized and run behind a reverse proxy, which is described as the immediate next step in Chapter 9."),
  PB(),
];

// ---------- Chapter 6 ----------
const ch6 = [
  H1("Chapter 6 - Testing and Evaluation"),
  H2("6.1 Testing Types"),
  bullet("Unit and integration tests for the backend (pytest), covering authentication and the full upload-to-history flow with a mocked database."),
  bullet("Access-control tests proving that one doctor cannot read another doctor's patient."),
  bullet("A preflight checker that validates that all required model assets and configuration are present before deployment."),
  bullet("An end-to-end inference smoke test that exercises the live prediction path against a running backend."),
  bullet("System and usability testing of the full clinical flow through the user interface."),
  H2("6.2 Evaluation Metrics"),
  P("For classification we report accuracy, precision, recall (sensitivity), specificity, F1, and the area under the ROC curve (AUC), together with the confusion matrix. For detection we report mean average precision at an IoU of 0.5 (mAP@0.5), mAP averaged over IoU thresholds from 0.5 to 0.95, recall, and precision. Recall is emphasized throughout because in pneumonia a false negative, a missed case, is the most costly error."),
  H2("6.3 Experimental Setup"),
  P("Models were trained on Kaggle GPU sessions (NVIDIA P100/T4) using PyTorch with mixed-precision training, early stopping on the validation metric, and standard data augmentation. The RSNA dataset was converted from DICOM to PNG with uniform contrast handling and split patient-wise into train, validation, and test sets with a fixed seed; the test set holds 20 percent of patients (4,135 normal and 1,202 pneumonia images) and is never seen during training or model selection."),
  PB(),
];

// ---------- Chapter 7 ----------
const ch7 = [
  H1("Chapter 7 - Results and Discussion"),
  H2("7.1 Classification Results"),
  ...table(["Model", "AUC", "Accuracy", "Recall", "Specificity", "F1", "Params"], [
    ["ResNet50", "0.884", "0.810", "0.761", "0.824", "0.644", "23.5M"],
    ["DenseNet121", "0.883", "0.802", "0.785", "0.807", "0.641", "7.0M"],
    ["EfficientNet-B0", "0.886", "0.815", "0.765", "0.830", "0.651", "4.0M"],
  ], [2200, 1100, 1300, 1150, 1372, 950, 1000], 6, "Classification results on the held-out test set."),
  ...fig("classification_metrics.png", 6, "Classification metrics across the three classifiers.", 560, 299),
  ...fig("confusion_matrices.png", 7, "Confusion matrices for the three classifiers on the held-out test set.", 620, 200),
  P("All three classifiers perform similarly, with AUCs clustered around 0.88. EfficientNet-B0 is the strongest and also by far the smallest (4.0 million parameters), which makes it the most efficient choice for serving. The confusion matrices show the expected trade-off on an imbalanced test set: the models keep specificity high while maintaining solid sensitivity."),
  H2("7.2 Detection Results"),
  ...table(["Model", "mAP@0.5", "mAP@[.5:.95]", "Recall", "Params"], [
    ["YOLOv8n", "0.346", "0.138", "0.382", "3.0M"],
    ["Faster R-CNN", "0.381", "0.124", "0.812", "41.3M"],
  ], [2400, 1700, 1900, 1400, 1672], 7, "Detection results on the held-out test set."),
  ...fig("detection_metrics.png", 8, "Detection metrics: YOLOv8n versus Faster R-CNN.", 560, 336),
  P("The two detectors reach a similar mAP@0.5, but they differ sharply on recall: Faster R-CNN recalls 0.812 of pneumonia regions versus 0.382 for YOLOv8n. Because a missed pneumonia is the dangerous error, we deploy Faster R-CNN as the default detector despite its larger size. This is a clear example of choosing a model on the clinically meaningful metric rather than on a headline number."),
  H2("7.3 Optimization: A Negative but Useful Result"),
  P("Our PSO, GWO, and SA hyperparameter search ran on a deliberately cheap proxy so it could fit a single GPU session. That proxy turned out to be too noisy to rank configurations reliably: the settings it preferred improved the proxy score but hurt the full retrain for most models. We therefore select the validation-best checkpoint per model rather than the search-suggested one. The lesson, that lightweight proxy search does not automatically beat a strong, carefully tuned baseline, is a genuine and defensible engineering finding."),
  H2("7.4 Calibration Against the Literature"),
  P("Our numbers are honest and competitive. A classification AUC near 0.88 is in line with established work; the well-known CheXNet reported an AUC of 0.768 for pneumonia on a different dataset. Reported RSNA detection results typically land between 0.32 and 0.39 mAP@0.5, so our Faster R-CNN at 0.381 is on par with engineered solutions. We deliberately avoided the inflated near-perfect scores that appear when the data leaks between train and test at the patient level."),
  H2("7.5 Limitations"),
  bullet("Performance is bounded by the difficulty and label noise of the RSNA dataset and may not transfer to other populations or equipment without re-validation."),
  bullet("The system does not yet detect out-of-distribution inputs, such as a non-chest image, beyond basic format checks."),
  bullet("Load testing and production monitoring are not yet in place, so we report architecture-level rather than measured scalability."),
  PB(),
];

// ---------- Chapter 8 ----------
const ch8 = [
  H1("Chapter 8 - Ethics, Compliance, and Standards"),
  H2("8.1 Ethical Risks Assessed and Mitigated"),
  bullet("Bias and fairness: the model inherits the RSNA population, so it may underperform on under-represented groups; we flag this and recommend subgroup validation before clinical use."),
  bullet("Patient safety: the tool is decision-support only and never makes an autonomous diagnosis; the clinician confirms every result, which is the primary safeguard against a wrong output."),
  bullet("Over-reliance: confidence scores and explainability heatmaps are shown precisely so the doctor can challenge the model rather than trust it blindly."),
  bullet("Privacy: patient data is access-controlled per user, and inference runs on image pixels rather than on identity metadata."),
  H2("8.2 Data Handling and Consent"),
  P("Passwords are hashed with bcrypt and never stored in plaintext. Access to patient records and analyses is restricted to the owning doctor at the query level. In a real deployment the operating clinic is responsible for obtaining patient consent and for compliance with local data-protection law; the system is designed to support that with per-user isolation and an auditable, persisted record of every analysis."),
  H2("8.3 Standards Followed and Why"),
  bullet("OWASP secure-development guidance informed authentication, input validation, and secret handling, because the system stores sensitive health data."),
  bullet("GDPR-style data-minimization and access-control principles informed the database and authorization design, since the platform processes personal and health information."),
  bullet("Responsible-AI practice (human-in-the-loop, explainability, honest evaluation) was applied throughout, because an opaque or overstated medical model is unsafe."),
  P("Each standard was selected for its direct relevance to a clinical, data-sensitive application and was applied concretely in the design, from hashed credentials and scoped queries to mandatory explainability on every prediction."),
  PB(),
];

// ---------- Chapter 9 ----------
const ch9 = [
  H1("Chapter 9 - Conclusions and Future Work"),
  H2("9.1 Conclusions"),
  P("This project delivered a complete, working Chest X-ray Pneumonia Detection System: five rigorously evaluated deep-learning models served through a secure, explainable, full-stack web application. We met our objectives, train and evaluate honestly, deliver a usable multi-user product, explain every prediction, and keep the work reproducible. The strongest classifier reached an AUC of 0.886 and the deployed detector reached a recall of 0.812, results that are competitive with the literature and were obtained without data leakage."),
  H2("9.2 Lessons Learned"),
  bullet("Honest evaluation matters more than a high number; finding and fixing the data leak was one of the most valuable steps in the project."),
  bullet("Choosing a model on the clinically meaningful metric (recall) can mean preferring a larger, slower architecture, and that can be the right call."),
  bullet("Delivering a model as a product is a large engineering effort in its own right: security, persistence, explainability, and reproducibility all take real work."),
  H2("9.3 Future Work"),
  bullet("Containerize the system with Docker Compose and add a CI/CD pipeline for one-command, reproducible deployment."),
  bullet("Add structured logging, metrics, and monitoring, including model-drift detection in production."),
  bullet("Add out-of-distribution detection so non-chest or low-quality images are rejected before inference."),
  bullet("Extend from binary screening toward multi-finding detection and validate on additional, more diverse datasets."),
  bullet("Pursue the clinical validation and regulatory steps required to move from decision support toward a certified tool."),
  PB(),
];

// ---------- References ----------
const refs = [
  H1("References"),
  ref("P. Rajpurkar et al., \"CheXNet: Radiologist-level pneumonia detection on chest X-rays with deep learning,\" arXiv:1711.05225, 2017."),
  ref("S. Ren, K. He, R. Girshick, and J. Sun, \"Faster R-CNN: Towards real-time object detection with region proposal networks,\" IEEE Trans. Pattern Anal. Mach. Intell., vol. 39, no. 6, pp. 1137-1149, 2017."),
  ref("J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, \"You only look once: Unified, real-time object detection,\" in Proc. IEEE CVPR, 2016, pp. 779-788."),
  ref("G. Jocher et al., \"Ultralytics YOLO,\" GitHub Repository, 2023. [Online]. Available: https://github.com/ultralytics/ultralytics"),
  ref("Radiological Society of North America, \"RSNA Pneumonia Detection Challenge,\" Kaggle, 2018. [Online]. Available: https://www.kaggle.com/competitions/rsna-pneumonia-detection-challenge"),
  ref("K. He, X. Zhang, S. Ren, and J. Sun, \"Deep residual learning for image recognition,\" in Proc. IEEE CVPR, 2016, pp. 770-778."),
  ref("G. Huang, Z. Liu, L. van der Maaten, and K. Q. Weinberger, \"Densely connected convolutional networks,\" in Proc. IEEE CVPR, 2017, pp. 4700-4708."),
  ref("M. Tan and Q. V. Le, \"EfficientNet: Rethinking model scaling for convolutional neural networks,\" in Proc. ICML, 2019, pp. 6105-6114."),
  ref("R. R. Selvaraju et al., \"Grad-CAM: Visual explanations from deep networks via gradient-based localization,\" in Proc. IEEE ICCV, 2017, pp. 618-626."),
  ref("M. Sundararajan, A. Taly, and Q. Yan, \"Axiomatic attribution for deep networks,\" in Proc. ICML, 2017, pp. 3319-3328."),
  ref("J. Kennedy and R. Eberhart, \"Particle swarm optimization,\" in Proc. IEEE ICNN, 1995, pp. 1942-1948."),
  ref("S. Mirjalili, S. M. Mirjalili, and A. Lewis, \"Grey wolf optimizer,\" Advances in Engineering Software, vol. 69, pp. 46-61, 2014."),
  ref("S. Ramirez, \"FastAPI,\" 2018. [Online]. Available: https://fastapi.tiangolo.com/"),
  ref("Google, \"Angular,\" 2024. [Online]. Available: https://angular.dev/"),
  ref("MongoDB Inc., \"MongoDB,\" 2024. [Online]. Available: https://www.mongodb.com/"),
  ref("OWASP Foundation, \"OWASP Top 10 Web Application Security Risks,\" 2021. [Online]. Available: https://owasp.org/www-project-top-ten/"),
  PB(),
];

// ---------- Appendix 1 ----------
const ap1 = [
  H1("Appendix 1 - User Guide"),
  H2("A1.1 System Requirements"),
  bullet("Python 3.12, Node.js 20+ and npm, and a running MongoDB instance (local or MongoDB Atlas)."),
  bullet("Roughly 1 GB of disk for the model weights (tracked with Git LFS)."),
  H2("A1.2 Installation and Setup"),
  P("Backend: create a virtual environment, install requirements from Backend/requirements.txt, copy .env.example to .env and set the secret key and MongoDB URL, then start the API with \"python main.py\" or \"uvicorn main:app\". Frontend: from the Frontend folder run \"npm install\" and then \"npm start\" for development or \"npm run build\" for a production build. Ensure Git LFS is installed so the model weights are fetched on clone."),
  H2("A1.3 Using the System"),
  bullet("Register a doctor account and log in."),
  bullet("Create or select a patient record."),
  bullet("Open the upload page and choose a chest X-ray image; a preview is shown."),
  bullet("Submit for analysis and wait on the processing screen."),
  bullet("Review the result: the annotated image, the pneumonia decision, the confidence score, and the heatmap."),
  bullet("Find the saved analysis later in the patient history."),
  H2("A1.4 Troubleshooting"),
  bullet("If the backend fails to start, confirm MongoDB is running and the MONGODB_URL in .env is correct."),
  bullet("If a model fails to load, confirm Git LFS pulled the .pt files into Backend/model_assets."),
  bullet("If the browser cannot reach the API, confirm the backend port and the CORS_ORIGINS setting."),
  PB(),
];

// ---------- Appendix 2 ----------
const ap2 = [
  H1("Appendix 2 - Supporting Material"),
  H2("A2.1 Lessons Learned and Challenges"),
  P("The most instructive challenge was a preprocessing data leak that produced near-perfect early scores; fixing it with patient-wise splitting and uniform image processing taught the team to trust the protocol over the number. Serving several large models efficiently, and making detector predictions explainable, were the main engineering challenges, solved with a single-load model registry and detector-appropriate saliency methods (Eigen-CAM and occlusion sensitivity)."),
  H2("A2.2 Potential Improvements"),
  bullet("Containerization, CI/CD, and production monitoring."),
  bullet("A feedback loop that turns doctor confirmations and corrections into new training labels."),
  bullet("Model quantization to lower inference latency and memory."),
  H2("A2.3 Repository and Contribution Summary"),
  P("The complete source code, model assets, documentation, and these deliverables are available in the project GitHub repository. The team is split into an AI track (Moamen Elsayed Elsharkawy, Habiba Ayman Amin) responsible for the data pipeline, model training, evaluation, and explainability, and a full-stack track (Ahmed Gamal Abdelfattah, Sara Mostafa Ali) responsible for the Angular frontend, the FastAPI backend, the database, and integration. Individual contributions are reflected in the Git commit history."),
];

const children = [
  ...cover, coverTable, ...cover2,
  ...absEn, ...absAr,
  ...toc,
  ...ch1, ...ch2, ...ch3, ...ch4, ...ch5, ...ch6, ...ch7, ...ch8, ...ch9,
  ...refs, ...ap1, ...ap2,
];

const doc = new Document({
  creator: "Team 19 - CSAI, Zewail City",
  title: "Chest X-ray Pneumonia Detection System",
  styles: {
    default: { document: { run: { font: TNR, size: 24 }, paragraph: { spacing: { line: 360, lineRule: "auto" } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 36, bold: true, font: TNR, color: NAVY }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, font: TNR, color: NAVY }, paragraph: { spacing: { before: 180, after: 120 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: TNR }, paragraph: { spacing: { before: 140, after: 100 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: {
    config: [
      { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 600, hanging: 300 } } } }] },
      { reference: "refs", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 640, hanging: 480 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1417, right: 1417, bottom: 1417, left: 1417 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [txt("Chest X-ray Pneumonia Detection System  |  Team 19  |  ", { size: 16, color: "888888" }), new TextRun({ children: ["Page ", PageNumber.CURRENT], font: TNR, size: 16, color: "888888" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("WROTE", OUT, buf.length, "bytes"); });
