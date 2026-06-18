// In-depth explanation generator - Egyptian Arabic (RTL) with English technical terms.
// Run: NODE_PATH="$(npm root -g)" node documentation/_generators/explanation.js
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
const FONT = "Arial"; // supports Arabic + Latin so English terms render inline
const NAVY = "1F3B63";
const TEAL = "1D6B5F";

// Arabic run (RTL). English technical terms inside the string are reordered LTR by the
// Unicode bidi algorithm, so we can mix "Faster R-CNN", "mAP", etc. straight into the text.
const t = (s, o = {}) => new TextRun({ text: s, font: FONT, rightToLeft: true, ...o });

function P(s, o = {}) {
  return new Paragraph({
    bidirectional: true,
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { line: 300, lineRule: "auto", after: o.after == null ? 130 : o.after, before: o.before || 0 },
    children: Array.isArray(s) ? s : [t(s, o.run || {})],
  });
}
const H1 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_1, bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { before: 280, after: 150 }, children: [t(s)] });
const H2 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_2, bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { before: 220, after: 110 }, children: [t(s)] });
const H3 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_3, bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { before: 150, after: 90 }, children: [t(s)] });
const bullet = (s) => new Paragraph({ numbering: { reference: "bul", level: 0 }, bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { line: 300, lineRule: "auto", after: 50 }, children: Array.isArray(s) ? s : [t(s)] });
const PB = () => new Paragraph({ children: [new PageBreak()] });

function qa(q, a) {
  return [
    new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { before: 110, after: 20 }, children: [t("س: " + q, { bold: true, color: NAVY })] }),
    new Paragraph({ bidirectional: true, alignment: AlignmentType.JUSTIFIED, spacing: { after: 90 }, children: [t("ج: ", { bold: true, color: TEAL }), t(a)] }),
  ];
}

const BD = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const BORDERS = { top: BD, bottom: BD, left: BD, right: BD };
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const NO_BORDERS = { top: NONE, bottom: NONE, left: NONE, right: NONE };

function cell(c, w, o = {}) {
  return new TableCell({
    borders: BORDERS, width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 50, bottom: 50, left: 100, right: 100 },
    children: [new Paragraph({ bidirectional: true, alignment: o.align || AlignmentType.RIGHT, spacing: { after: 0, line: 276, lineRule: "auto" }, children: [t(String(c), { size: o.size || 19, bold: !!o.bold })] })],
  });
}
function table(headers, rows, widths) {
  const head = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { bold: true, fill: "D9E2F0" })) });
  const body = rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, widths[i])) }));
  return [new Table({ visuallyRightToLeft: true, width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths, rows: [head, ...body] }), new Paragraph({ spacing: { after: 130 }, children: [t("")] })];
}

function fig(file, caption, w, h) {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 30 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(FIG + file), transformation: { width: w, height: h }, altText: { title: caption, description: caption, name: file } })] }),
    new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 140 }, children: [t(caption, { size: 18, color: "777777" })] }),
  ];
}
function imageCell(file, caption, w, h) {
  return new TableCell({
    borders: NO_BORDERS, verticalAlign: VerticalAlign.CENTER, margins: { top: 40, bottom: 40, left: 40, right: 40 },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 20 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(FIG + file), transformation: { width: w, height: h } })] }),
      new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 0 }, children: [t(caption, { size: 16, color: "777777" })] }),
    ],
  });
}
// images in a borderless 2-column grid
function imageGrid(items, w, h) {
  const rows = [];
  for (let i = 0; i < items.length; i += 2) {
    const pair = items.slice(i, i + 2);
    rows.push(new TableRow({ children: pair.map(([f, c]) => imageCell(f, c, w, h)) }));
  }
  return [new Table({ visuallyRightToLeft: true, width: { size: 100, type: WidthType.PERCENTAGE }, rows }), new Paragraph({ spacing: { after: 130 }, children: [t("")] })];
}

const children = [];
const A = (...x) => children.push(...x);

// ===================== Cover =====================
A(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 160 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(LOGO), transformation: { width: 240, height: 142 }, altText: { title: "Zewail City", description: "logo", name: "logo" } })] }));
A(new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 70 }, children: [t("نظام الكشف عن الالتهاب الرئوي من أشعة الصدر", { size: 38, bold: true, color: NAVY })] }));
A(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: "Chest X-ray Pneumonia Detection System", font: FONT, size: 30, italics: true })] }));
A(new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [t("شرح تقني متعمّق: الـ AI pipeline كامل + الـ web application", { size: 24, color: TEAL })] }));
A(new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [t("شرح بالمصري للمشروع كله من أول الـ data لحد ما الـ model يشتغل في الموقع، بالتفاصيل والأرقام والصور.", { size: 22 })] }));
A(new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [t("Team 19  -  School of CSAI, Zewail City of Science and Technology  -  Supervisor: Prof. Dr. Khaled Mostafa  -  June 2026", { size: 20, color: "555555" })] }));
A(P("الورقة دي مكتوبة عشان أي حد يقراها يقدر يفهم المشروع كله ويشرحه بثقة، حتى لو أول مرة يشوفه. فيها قسمين: القسم A بيشرح الـ AI pipeline (الـ data، الـ preprocessing، الـ models، التدريب، التقييم، والـ XAI)، والقسم B بيشرح الـ web application (الـ frontend والـ backend والـ database والـ security ورحلة الطلب من الأول للآخر). كل قسم بينتهي ببنك أسئلة متوقّعة من لجنة المناقشة بإجاباتها.", { run: { color: "555555" } }));
A(PB());
A(H1("الفهرس - Table of Contents"));
A(new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }));
A(PB());

// =====================================================================
// SECTION A - AI PIPELINE
// =====================================================================
A(H1("القسم A - الـ AI Pipeline"));
A(P("باختصار في جملة: بناخد صورة أشعة صدر (chest X-ray)، بنعدّيها على deep-learning model مدرّب، وبيرجّعلنا يا إما احتمال إن الرئة فيها التهاب رئوي (دي مهمة الـ classification)، يا إما box حوالين مكان الالتهاب مع نسبة ثقة (دي مهمة الـ detection). كل اللي تحت بيشرح إزاي بنوصل من صورة طبية خام للإجابة دي، وليه بتطلع كده."));
A(...fig("ai_pipeline.png", "شكل A1. مراحل الـ AI pipeline الثمانية (phases 1 -> 8).", 600, 146));

A(H2("A1. الـ Dataset: RSNA Pneumonia Detection Challenge"));
A(P("استخدمنا dataset بتاع تحدي RSNA Pneumonia Detection اللي نشرته الـ Radiological Society of North America. فيه حوالي 26,684 صورة أشعة صدر أمامية (frontal chest X-rays)، كل واحدة اتعلّمت (labeled) من radiologists. أهم نقطة إنه بيدّينا نوعين من الـ labels: label على مستوى الصورة (فيه التهاب ولا لأ) بنستخدمه في الـ classification، وbounding boxes (المستطيلات اللي بتحدد مكان الـ opacity اللي بيشبه الالتهاب) بنستخدمها في الـ detection. اخترناه لأنه كبير، متعلّم بإيد متخصصين، ومستخدَم كـ benchmark مشهور (يعني أرقامنا تقدر تتقارن بغيرنا)، وبيدعم المهمتين مع بعض."));
A(P([t("ليه ده مهم؟ ", { bold: true }), t("جودة أي model مسقوفة بجودة الـ data بتاعته. وبما إن RSNA متعلّم من خبراء، النتائج بتاعتنا بتعكس الـ model نفسه، مش noise إحنا اللي دخّلناه.")]));

A(H2("A2. من صورة خام لـ model input (الـ Preprocessing)"));
A(P("الأشعة الطبية مبتجيش صور عادية، بتيجي على هيئة DICOM files، وده format طبي بيخزّن الـ pixels مع بيانات المريض. الـ preprocessing بتاعنا بيحوّل كل DICOM لـ PNG نضيفة الـ model يقدر يقراها، بالخطوات دي:"));
A(bullet([t("قراءة الـ DICOM ", {}), t("بمكتبة pydicom عشان نطلّع مصفوفة الـ grayscale pixels الخام.")]));
A(bullet([t("Robust intensity normalization: ", { bold: true }), t("سطوع الأشعة بيختلف من جهاز للتاني، فبنقص (clip) كل صورة عند الـ 2nd-98th percentiles وبنرجّعها لمدى 0-255. ده بيشيل الـ outliers ويخلّي الصور قابلة للمقارنة.")]));
A(bullet([t("CLAHE contrast enhancement: ", { bold: true }), t("الـ Contrast Limited Adaptive Histogram Equalization (clip limit = 2.0، tiles = 8x8) بيزوّد الـ contrast محليًا عشان الـ opacities الخفيفة في الرئة تبان. بيعمل equalize في مربعات صغيّرة مش على الصورة كلها، وده مثالي للأشعة.")]));
A(bullet([t("Resize ", {}), t("لمقاس ثابت (224x224 للـ classifiers، و640x640 للـ detectors) مع حفظ الأبعاد الأصلية عشان نقدر نرجّع إحداثيات الـ boxes صح.")]));
A(P([t("أهم درس اتعلمناه هنا (وغالبًا سؤال امتحان): ", { bold: true }), t("في الأول كانت النتايج عالية بشكل مريب. السبب كان data leak: الـ contrast enhancement كان متطبّق بشكل مختلف على صور الالتهاب وصور الطبيعي، فالـ model بقى بيغش وبيكتشف الـ preprocessing مش المرض. صلّحناها بإننا نطبّق نفس الـ CLAHE بالظبط على كل الصور بغض النظر عن الـ label. الأرقام الأقل اللي بنعرضها دلوقتي هي الحقيقية. الدرس: ثِق في البروتوكول مش في الرقم.")]));

A(H2("A3. تقسيم الـ data صح + معالجة عدم توازن الـ classes (imbalance)"));
A(P("قسّمنا الـ data لـ train / validation / test على مستوى المريض (patient-level) مش على مستوى الصورة، وبـ seed ثابت (42) عشان النتائج تتكرر. المريض الواحد ممكن يكون عنده أكتر من صورة، ولو صور نفس المريض اتوزّعت بين الـ train والـ test، الـ model ممكن يحفظ المريض ده وياخد درجة أعلى من الحقيقة. التقسيم بالمريض بيضمن إن الـ test set فيه ناس الـ model عمره ما شافها. والتقسيم كمان stratified يعني نسبة الالتهاب للطبيعي محفوظة في كل جزء. الـ test set المعزول = 20% من المرضى: 4,135 صورة طبيعية و1,202 صورة التهاب، ومبنلمسهوش خالص أثناء التدريب أو اختيار الـ model."));
A(P([t("عدم التوازن (class imbalance): ", { bold: true }), t("الالتهاب هو الـ class الأقل (minority)، فلو سبنا الـ model زي ما هو ممكن ياخد accuracy عالية بإنه يقول 'طبيعي' على طول. عالجنا ده بـ class-weighted CrossEntropy: بنّدّي وزن أكبر للـ class النادر بنسبة عكسية لتكراره (inverse class frequency)، فالـ model بيتعاقب أكتر لما يفوّت حالة التهاب. وكمان بنقيّم بـ AUC و recall والـ confusion matrix مش بالـ accuracy لوحدها. وعلى مستوى الصور بنستخدم augmentation وقت التدريب بس (h-flip، rotation، color jitter) عشان نقلّل الـ overfitting.")]));

A(H2("A4. مهمتين: classification و detection"));
A(P("الـ classification بيجاوب على سؤال 'هل فيه التهاب في الصورة دي؟' باحتمال. والـ detection بيجاوب 'فين بالظبط؟' برسم box أو أكتر، كل واحد معاه نسبة ثقة. عملنا الاتنين لأن الدكتور عايز screening سريع (نعم/لأ) وكمان مؤشّر بصري للمكان المشكوك فيه. الـ model اللي بننشره كـ default هو detector (Faster R-CNN) لأن تحديد المكان أنفع إكلينيكيًا."));

A(H2("A5. الـ Models بالتفصيل + عدد الـ parameters"));
A(P("كل الـ models الست بتستخدم transfer learning: بدل ما تتعلّم الرؤية من الصفر، بتبدأ من weights مدرّبة على ImageNet (dataset ضخم لصور طبيعية) وبعدين بنعمل fine-tune على أشعة الصدر. ده standard في الـ medical imaging لأن الـ datasets الطبية صغيّرة، والـ low-level features (الحواف والـ textures) بتنتقل كويس."));
A(...table(["الـ Model", "النوع", "عدد الـ Parameters", "الفكرة المميِّزة"], [
  ["ResNet50", "classifier", "23.5M", "residual connections (شورت كت بيخلّي الشبكة العميقة تتدرّب)"],
  ["DenseNet121", "classifier", "7.0M", "كل layer متوصّلة بكل اللي بعدها، فالـ features بتتعاد استخدامها (backbone بتاع CheXNet)"],
  ["EfficientNet-B0", "classifier", "4.0M", "compound scaling - أصغر classifier وأكفأ واحد عندنا"],
  ["Faster R-CNN", "detector", "41.3M", "two-stage: RPN يقترح boxes وبعدين head يصنّف ويظبط - أعلى recall (المنشور)"],
  ["YOLOv8n", "detector", "3.0M", "one-stage anchor-free - أسرع وأخف بس recall أقل"],
  ["SSDlite320 MobileNetV3", "detector", "2.2M", "أخف وأسرع detector - mobile/edge، input 320px (الجديد)"],
], [2300, 1500, 1700, 3500]));
A(H3("الـ classifiers الثلاثة"));
A(bullet([t("ResNet50: ", { bold: true }), t("شبكة convolutional من 50 layer، فكرتها الأساسية الـ residual connection (شورت كت بيخلّي الإشارة تتخطّى layers)، وده حلّ مشكلة إن الشبكات العميقة جدًا صعب تتدرّب.")]));
A(bullet([t("DenseNet121: ", { bold: true }), t("كل layer متوصّلة بكل اللي بعدها فبيحصل feature reuse على طول الشبكة. كفؤة في الـ parameters وكانت الـ backbone بتاع CheXNet، الموديل الشهير اللي وصل لمستوى الـ radiologist.")]));
A(bullet([t("EfficientNet-B0: ", { bold: true }), t("بيستخدم compound scaling عشان يوازن بين العمق والعرض ودقة الـ input. هو أحسن classifier عندنا وكمان أصغرهم (4M parameters)، فهو الأكفأ.")]));
A(H3("الـ detectors الثلاثة"));
A(bullet([t("Faster R-CNN (two-stage): ", { bold: true }), t("الأول Region Proposal Network بيقترح boxes مرشّحة، وبعدين head تاني بيصنّف كل box ويظبط إحداثياته. بيستخدم ResNet50 backbone مع Feature Pyramid Network عشان يشوف الأحجام المختلفة. دقيق خصوصًا في الـ recall، وعشان كده بننشره.")]));
A(bullet([t("YOLOv8 (one-stage): ", { bold: true }), t("بيتنبأ بكل الـ boxes في forward pass واحدة بـ head من غير anchors. أسرع وأصغر بكتير، بس في اختباراتنا فوّت حالات التهاب أكتر (recall أقل) من Faster R-CNN.")]));
A(bullet([t("SSDlite320 MobileNetV3-Large (one-stage، الجديد): ", { bold: true }), t("الـ detector الخفيف السريع في التدريب: حوالي 2.2M parameters بس، وinput 320px (أصغر من 640 فأسرع). مبني على MobileNetV3 backbone وبيستخدم نفس الـ TorchVision detection path بتاع Faster R-CNN، وممكن يتدرّب على نص الـ data (fraction) عشان يخلّص أسرع. مناسب للـ edge/mobile deployment.")]));

A(H2("A6. تدريب الـ classifiers (كل الإعدادات)"));
A(...table(["الإعداد", "القيمة", "السبب"], [
  ["Optimizer", "Adam", "خيار افتراضي قوي ومتكيّف للـ fine-tuning"],
  ["Learning rate", "1e-4", "صغير عشان مايخربش الـ pretrained weights"],
  ["Loss", "Cross-entropy موزون بالـ class", "بيدّي وزن للـ class النادر (الالتهاب) فمايتجاهلوش"],
  ["LR scheduler", "ReduceLROnPlateau (على val AUC، x0.5)", "بيقلّل الـ LR لما الـ validation يبطّل يتحسّن"],
  ["Mixed precision (AMP)", "On على الـ GPU", "تدريب أسرع وذاكرة أقل"],
  ["Early stopping", "patience = 4 على val AUC", "نوقف قبل الـ overfitting ونرجّع أحسن weights"],
  ["Augmentation (train بس)", "h-flip، rotate 10، color jitter", "بيعلّم الـ model الثبات ويقلّل الـ overfitting"],
  ["Normalization", "ImageNet mean/std", "يطابق الـ pretrained backbone"],
  ["Image size", "224 x 224", "المقاس القياسي للـ backbones دي"],
], [2300, 3100, 3600]));
A(P([t("نقطتين مهمين. ", {}), t("Class weighting: ", { bold: true }), t("الالتهاب هو الأقلية، فبنوزن الـ loss بنسبة عكسية لتكرار الـ class، من غيرها الـ model ممكن ياخد accuracy عالية بإنه يقول 'طبيعي' دايمًا. "), t("Best-checkpoint restore: ", { bold: true }), t("بنحتفظ بالـ weights من الـ epoch اللي عندها أحسن validation AUC، مش آخر epoch، عشان منشحنش model عمل overfit.")]));

A(H2("A7. تدريب الـ detectors"));
A(P("Faster R-CNN و SSDlite بيشتركوا في نفس الـ TorchVision training loop: optimizer = SGD (momentum 0.9)، learning-rate schedule = linear warmup بعدها cosine decay، تجميد الـ backbone في أول epoch عشان الـ heads الجديدة تستقر قبل ما نعمل fine-tune للشبكة كلها، AMP، early stopping على mAP@0.5، وbest-checkpoint restore. بيتحسّنوا على الـ Faster R-CNN multi-task loss (objectness + box للـ RPN، وclassification + box-regression للـ head). وقت الـ inference بنطبّق Non-Maximum Suppression (NMS) عشان نشيل الـ boxes المكررة المتداخلة (مشروح في القسم B). أما YOLOv8 فبيتدرّب من خلال الـ Ultralytics pipeline بالـ augmentation الجاهز بتاعه. SSDlite بياخد input 320px جوّه الـ model فبيخلّص أسرع."));

A(H2("A8. الـ Nature-Inspired Optimization: PSO و GWO و SA"));
A(P("عشان ندوّر على إعدادات (hyperparameters) أحسن، طبّقنا ثلاث خوارزميات مستوحاة من الطبيعة. كلهم طرق للبحث في فضاء من الإعدادات من غير ما نجرّب كل الاحتمالات:"));
A(bullet([t("Particle Swarm Optimization (PSO): ", { bold: true }), t("سرب من الحلول المرشّحة 'بيطير' في فضاء البحث، كل واحد بينجذب لأحسن نتيجة ليه ولأحسن نتيجة للسرب كله، زي العصافير اللي بتلمّ على الأكل.")]));
A(bullet([t("Grey Wolf Optimizer (GWO): ", { bold: true }), t("بيقلّد هرم قطيع الدياب؛ أحسن ثلاث حلول (alpha و beta و delta) بيقودوا باقي القطيع ناحية المناطق الواعدة.")]));
A(bullet([t("Simulated Annealing (SA): ", { bold: true }), t("مستوحى من تبريد المعدن؛ بيقبل أحيانًا حلول أسوأ في الأول (حرارة عالية) عشان يهرب من الـ local traps، وبعدين بيستقر مع ما بيبرد.")]));
A(P([t("النتيجة الصادقة (سؤال متوقّع): ", { bold: true }), t("في النسخة الأولى قيّمنا كل candidate بـ proxy رخيص (epoch واحدة على جزء من الـ data وبـ budget صغير: population=3, iterations=2) عشان البحث يخلّص في session واحدة على Kaggle. الـ proxy ده طلع noisy جدًا: الإعدادات اللي اختارها مكانتش بتكسب بعد التدريب الكامل، وفي حالات خلّت النتيجة أسوأ من الـ baseline (مثلًا Faster R-CNN mAP@0.5 نزلت من 0.381 لـ 0.175، وEfficientNet AUC من 0.886 لـ 0.874). الدرس إن proxy search خفيف مش بالضرورة بيتفوّق على baseline متظبوط، وده finding حقيقي ومحترم مش فشل.")]));
A(H3("الحل: إعادة بحث أقوى (Stronger re-run)"));
A(P([t("ضفنا في كل notebook قسم 'Stronger nature-inspired search + retrain' بيعيد الـ Phase 4 بـ budget أكبر ", { }), t("ودقّة proxy أعلى ", { bold: true }), t("(epochs أكتر و data أكتر لكل candidate، عشان الإعدادات اللي بتتختار تنفع فعلًا في التدريب الكامل)، وبعدين بيعمل retrain كامل. القسم ده بيقرأ الـ baseline المحفوظ من results/<model>_report.json عشان يقارن before/after، فمش محتاج يعيد تدريب الـ Phase 3 خالص، وبيستبدل الـ checkpoint المنشور بس لو النسخة الجديدة كسبت الـ baseline. الأرقام النهائية للجزء ده بتتحدّث بعد ما نشغّله على Kaggle.")]));

A(H2("A9. مقاييس التقييم (Metrics) بشرح بسيط"));
A(bullet([t("Accuracy: ", { bold: true }), t("نسبة التنبؤات الصح من الكل. مضلِّلة على الـ data غير المتوازنة، فمابنعتمدش عليها لوحدها.")]));
A(bullet([t("Recall / Sensitivity: ", { bold: true }), t("من المرضى الحقيقيين، كام واحد مسكناه. ده أهم مقياس هنا، لأن حالة التهاب فايتة ممكن تكون خطر على الحياة.")]));
A(bullet([t("Specificity: ", { bold: true }), t("من الأصحاء الحقيقيين، كام واحد طلّعناه سليم صح.")]));
A(bullet([t("Precision: ", { bold: true }), t("من اللي قلنا عليهم مرضى، كام واحد فعلًا عنده التهاب.")]));
A(bullet([t("F1: ", { bold: true }), t("التوازن (harmonic mean) بين الـ precision والـ recall.")]));
A(bullet([t("AUC: ", { bold: true }), t("المساحة تحت الـ ROC curve؛ احتمال إن الـ model يرتّب مريض عشوائي أعلى من سليم عشوائي. 0.5 عشوائي و1.0 مثالي. مش معتمد على threshold، فهو المقياس الرئيسي عندنا للـ classification.")]));
A(bullet([t("Confusion matrix: ", { bold: true }), t("جدول الـ true/false positives و negatives اللي بنحسب منه كل اللي فوق.")]));
A(bullet([t("mAP و IoU و mAP@0.5: ", { bold: true }), t("للـ detection. الـ IoU (Intersection over Union) بيقيس تداخل الـ boxes؛ الـ box بيتحسب صح لو الـ IoU بتاعه مع الحقيقة عدّى threshold (مثلًا 0.5). الـ mAP متوسط الـ precision عبر مستويات الـ recall؛ mAP@0.5 بيستخدم threshold = 0.5، وmAP@[.5:.95] بيتوسّط على thresholds أصعب.")]));

A(H2("A10. النتائج، وليه طلعت كده، وإزاي نحسّنها"));
A(...fig("classification_metrics.png", "شكل A2. مقارنة أداء الـ classifiers الثلاثة على الـ test set.", 560, 300));
A(...table(["الـ Model (classifier)", "AUC", "Accuracy", "Recall", "F1", "Params"], [
  ["EfficientNet-B0 (الأحسن، منشور)", "0.886", "0.815", "0.765", "0.651", "4.0M"],
  ["DenseNet121 (منشور)", "0.883", "0.802", "0.785", "0.641", "7.0M"],
  ["ResNet50", "0.884", "0.810", "0.761", "0.643", "23.5M"],
], [3200, 1300, 1500, 1300, 1300, 1300].slice(0, 6)));
A(...fig("confusion_matrices.png", "شكل A3. الـ confusion matrices للـ classifiers الثلاثة على الـ test set.", 600, 194));
A(...table(["الـ Model (detector)", "mAP@0.5", "mAP@[.5:.95]", "Recall", "Params"], [
  ["Faster R-CNN (المنشور)", "0.381", "0.124", "0.812", "41.3M"],
  ["YOLOv8n", "0.346", "0.138", "0.382", "3.0M"],
  ["SSDlite320 (الجديد)", "قيد التحديث بعد Kaggle", "-", "-", "2.2M"],
], [3000, 1900, 1900, 1500, 1300]));
A(...fig("detection_metrics.png", "شكل A4. مقارنة الـ detectors (YOLO مقابل Faster R-CNN).", 560, 300));
A(P([t("ليه الأرقام دي؟ ", { bold: true }), t("AUC حوالي 0.88 هو اللي بيوصله أي classifier صادق على نوع الـ data ده؛ للمقارنة، CheXNet المشهور سجّل 0.768 على dataset تاني. الـ classifiers بيحافظوا على specificity عالية (حوالي 0.83) ومع كده بيمسكوا حوالي 76-79% من حالات الالتهاب. في الـ detection، الـ detectors بيوصلوا لـ mAP@0.5 متقارب (حوالي 0.35-0.38، وده بالظبط المدى 0.32-0.39 المذكور في الأبحاث)، بس Faster R-CNN بيمسك recall = 0.812 من مناطق الالتهاب مقابل 0.382 لـ YOLO.")]));
A(H3("ليه Faster R-CNN هو الأحسن (والمنشور)؟"));
A(P([t("الخطأ الأغلى في الـ screening هو إننا نفوّت حالة (false negative). Faster R-CNN عنده أعلى recall بفارق كبير (0.812 مقابل 0.382 لـ YOLO)، يعني بيفوّت أقل حالات بكتير، وكمان أعلى mAP@0.5 بين الـ detectors. عشان كده بننشره كـ default رغم إنه أكبر (41.3M parameters) وأبطأ. الـ trade-off مقصود: في الطب، مسك الحالة أهم من السرعة. وهنا بييجي دور SSDlite الجديد: لو محتاجين نشر سريع/خفيف على جهاز ضعيف، SSDlite (2.2M بس) بيدّينا بديل سريع جدًا في التدريب والـ inference، حتى لو دقته أقل شوية.")]));
A(P([t("إزاي نطلّع نتايج أحسن؟ ", { bold: true }), t("ندرّب على data أكتر وأكثر تنوّعًا (مستشفيات وأجهزة مختلفة)؛ نرفع دقة الـ input عشان الـ opacities الخفيفة تفضل بانة؛ نعمل ensemble لأكتر من model؛ نظبط الـ decision threshold عشان نبادل specificity بـ recall حسب احتياج العيادة؛ نضيف augmentation أقوى وواقعي طبيًا؛ نعمل pretrain على corpus كبير لأشعة الصدر قبل الـ fine-tune؛ وللـ detection، ندرّب أطول بالـ objective الكامل (مش proxy). وكمان external validation على dataset تاني هيخلّي النتايج أكتر مصداقية.")]));

A(H2("A11. الـ Explainability (XAI): نوري الدكتور 'ليه'"));
A(P("كل تنبؤ بنعرضه مع heatmap عشان الدكتور يتأكد إن الـ model بصّ على الرئة، مش على نص أو artifact. ده بيبني الثقة وبيخلّي القرار قابل للمراجعة. طبّقنا أكتر من طريقة، وكلها بتشتغل live مع كل طلب، وكلها best-effort (لو طريقة فشلت بتتخطّى من غير ما تكسر التنبؤ)."));
A(H3("للـ classifiers"));
A(bullet([t("Grad-CAM: ", { bold: true }), t("بيستخدم الـ gradients عند آخر convolutional layer عشان يطلّع heatmap للمناطق اللي زوّدت احتمال الالتهاب. أكتر طريقة شائعة ومباشرة.")]));
A(bullet([t("Integrated Gradients: ", { bold: true }), t("بيجمع الـ gradient على طول مسار من صورة سودا (baseline) للصورة الحقيقية، فبيدّي attribution لكل pixel.")]));
A(bullet([t("GradientSHAP: ", { bold: true }), t("تقدير على طريقة SHAP بياخد متوسط (input - baseline) * gradient على عينات فيها noise.")]));
A(bullet([t("Score-CAM: ", { bold: true }), t("من غير gradients؛ بيقنّع الصورة بكل activation channel ويوزنه بالـ pneumonia score الناتج، فبيدّي map class-discriminative.")]));
A(P([t("مثال حقيقي - حالة Pneumonia: ", { bold: true }), t("كل الصور دي نواتج فعلية من الـ web application على نفس صورة الأشعة. الـ classifier (EfficientNet-B0) قال "), t("PNEUMONIA باحتمال 75%", { bold: true, color: NAVY }), t(". تحت كل صورة مكتوب التنبؤ، والـ heatmaps بتركّز على الرئة اليسرى (مكان الـ opacity) مش على حرف أو حافة.")]));
A(...imageGrid([
  ["xai_banner.png", "EfficientNet-B0 - التنبؤ: PNEUMONIA (75%)"],
  ["xai_gradcam.png", "Grad-CAM - بيركّز على الرئة المصابة"],
  ["xai_integrated_gradients.png", "Integrated Gradients - PNEUMONIA"],
  ["xai_gradient_shap.png", "GradientSHAP - PNEUMONIA"],
  ["xai_score_cam.png", "Score-CAM (من غير gradients) - PNEUMONIA"],
  ["xai_orig.png", "الصورة الأصلية (input X-ray)"],
], 245, 245));
A(H3("للـ detectors"));
A(bullet([t("Eigen-CAM: ", { bold: true }), t("الـ saliency القياسي بالـ gradients مبيتطبّقش بسهولة على الـ detectors، فبنستخدم Eigen-CAM اللي بيحلّل الـ activations بتاعة الـ backbone (المكوّن الرئيسي - principal component) عشان يبيّن الشبكة بتركّز فين.")]));
A(bullet([t("Occlusion sensitivity: ", { bold: true }), t("بنغطّي أجزاء من الصورة بمربع ونشوف ثقة الـ detection بتنزل قد إيه؛ كل ما النزول أكبر، كل ما المنطقة دي أهم.")]));
A(P([t("نفس الصورة بالـ detectors: ", { bold: true }), t("Faster R-CNN لقى الالتهاب ورسم box (نسبة 54%، ومكتوب "), t("Pneumonia Detected", { bold: true }), t(" فوق الصورة)، لكن YOLO فوّت الحالة (no detection) - وده بالظبط سبب نشرنا لـ Faster R-CNN: الـ recall الأعلى. والـ Eigen-CAM والـ Occlusion بيوضّحوا منطقة تركيز الـ detector.")]));
A(...imageGrid([
  ["xai_det_box.png", "Faster R-CNN - التنبؤ: Pneumonia Detected (box)"],
  ["xai_yolo_box.png", "YOLOv8 - فوّت الحالة (no detection)"],
  ["xai_eigencam.png", "Eigen-CAM (Faster R-CNN backbone)"],
  ["xai_occlusion.png", "Occlusion sensitivity (Faster R-CNN)"],
], 245, 245));
A(P([t("للمقارنة - حالة Normal: ", { bold: true }), t("على أشعة صدر سليمة، نفس الـ classifier قال "), t("Normal باحتمال 99%", { bold: true, color: TEAL }), t(" (احتمال الالتهاب 0.8% بس)، فالنظام بيفرّق بوضوح بين الحالتين.")]));
A(...imageGrid([
  ["xai_normal_orig.png", "أشعة صدر سليمة (input)"],
  ["xai_normal_banner.png", "EfficientNet-B0 - التنبؤ: Normal (99%)"],
], 245, 245));
A(P([t("ملاحظة: ", { bold: true }), t("كل الصور دي نواتج حقيقية من الـ web application الشغّال. الـ heatmaps في حالة الالتهاب بتركّز على الرئة المصابة، وده بيأكد إن الـ models بتتعلّم إشارات طبية حقيقية مش artifacts. نواتج SSDlite هتتضاف بعد تدريبه على Kaggle.")]));

A(H2("A12. القسم A - أسئلة متوقّعة من اللجنة"));
A(...qa("ليه نتايجكوا الأولى كانت شبه مثالية وعملتوا إيه؟", "كانت متضخّمة بسبب data leak في الـ preprocessing: الـ contrast enhancement كان متطبّق بشكل مختلف على الـ class اتنين، فالـ model كان بيكتشف الـ preprocessing مش المرض. صلّحناها بتطبيق نفس الـ CLAHE على كل الصور وبنعرض الأرقام الصادقة الأقل."));
A(...qa("ليه التقسيم بالمريض مش بالصورة؟", "لأن المريض الواحد ممكن يكون عنده أكتر من صورة. التقسيم بالصورة ممكن يحط نفس المريض في الـ train والـ test، فالـ model يحفظه وياخد درجة أعلى من الحقيقة. التقسيم بالمريض بيضمن إن الـ test مش متشاف."));
A(...qa("ليه الـ recall هو أهم مقياس عندكوا؟", "لأن في screening الالتهاب، الـ false negative (حالة فايتة) ممكن يكون خطر على الحياة، أما الـ false positive بيأدي لمراجعة تانية بس. فبنختار ونظبط الـ models عشان نقلّل الحالات الفايتة."));
A(...qa("ليه بتنشروا Faster R-CNN مش YOLO الأسرع؟", "الاتنين بيوصلوا mAP@0.5 متقارب، بس Faster R-CNN بيمسك recall = 0.812 مقابل 0.382 لـ YOLO. بنقبل الـ model الأكبر والأبطأ لأن مسك الحالات أهم من السرعة هنا."));
A(...qa("طب وضفتوا SSDlite ليه؟", "كـ detector خفيف وسريع جدًا في التدريب (2.2M parameters، input 320px). بيدّينا بديل للـ edge/mobile deployment وبيكمّل المقارنة (heavy = Faster R-CNN مقابل light = SSDlite/YOLO)، وبيستخدم نفس الـ TorchVision path فاندمج بسهولة."));
A(...qa("عالجتوا عدم التوازن (imbalance) إزاي؟", "وزّنّا الـ loss بنسبة عكسية لتكرار الـ class عشان الـ class النادر مايتجاهلش، وبنقيّم بـ AUC و recall والـ confusion matrix مش بالـ accuracy لوحدها."));
A(...qa("بتمنعوا الـ overfitting إزاي؟", "transfer learning، augmentation وقت التدريب بس، weight decay، LR scheduler، early stopping على validation AUC، واسترجاع أحسن checkpoint مش آخر epoch."));
A(...qa("الـ metaheuristic optimization نفع؟", "مع الـ proxy الرخيص لأ: PSO و GWO و SA اختاروا إعدادات مكسبتش بعد retrain كامل. عشان كده اخترنا أحسن validation checkpoint، وضفنا قسم re-run أقوى يعيد البحث ببدجت ودقّة أعلى، وبيستبدل الـ model بس لو كسب الـ baseline."));
A(...qa("الـ model آمن إكلينيكيًا؟", "هو decision support مش تشخيص أوتوماتيك. الدكتور بيأكد كل نتيجة، وكل تنبؤ بييجي بنسبة ثقة وheatmap عشان يتراجع. محتاج external validation وموافقات تنظيمية قبل الاستخدام الإكلينيكي الفعلي."));
A(PB());

// =====================================================================
// SECTION B - WEBAPP PIPELINE
// =====================================================================
A(H1("القسم B - الـ Web Application Pipeline"));
A(P("التطبيق من ثلاث طبقات: frontend الدكتور بيشوفه، backend بيعمل الشغل، وdatabase بيخزّن كل حاجة. وجوّه الـ backend في inference service متخصص بيشغّل الـ AI models. القسم ده بيشرح كل جزء وبعدين بيتتبّع طلب واحد من الضغطة للنتيجة."));
A(...fig("architecture.png", "شكل B1. الـ three-tier architecture مع الـ inference service.", 600, 349));

A(H2("B1. الـ Frontend (Angular 21)"));
A(P("الـ frontend هو single-page application (SPA) متعمول بـ Angular ومكتوب بـ TypeScript. الـ single-page معناها إن المتصفح بيحمّل تطبيق واحد وبعدين بيبدّل الشاشات من غير reload كامل، فبيحس بالسرعة. مكوّناته:"));
A(bullet([t("Components / pages: ", { bold: true }), t("login، signup، dashboard، upload، processing، result، patient records، profile، settings. كل واحدة قطعة UI مستقلة.")]));
A(bullet([t("Routing + guards: ", { bold: true }), t("الـ router بيربط الـ URLs بالصفحات؛ والـ route guards بيمنعوا الصفحات المحمية (زي الـ dashboard) إلا لو المستخدم عامل login، وبيرجّعوا اللي عامل login بعيد عن صفحة الـ login.")]));
A(bullet([t("State service: ", { bold: true }), t("analysis-state service مركزي بيمسك التحليل الحالي والـ history عشان الصفحات تشارك الـ data من غير ما نمررها بإيدينا.")]));
A(bullet([t("API service: ", { bold: true }), t("service واحد بيجمّع كل النداءات للـ backend، وبيحط الـ login token مع كل request، فباقي التطبيق مبيتعاملش مع الـ HTTP مباشرة.")]));
A(bullet([t("Server-side rendering (SSR): ", { bold: true }), t("الصفحات العامة بتترسم مبدئيًا على Express server صغير عشان أول ظهور يبقى سريع، وبعدين التطبيق بيعمل hydrate ويبقى SPA تفاعلي.")]));
A(...imageGrid([
  ["ui_welcome.png", "صفحة الترحيب (welcome)"],
  ["ui_login.png", "صفحة الـ login"],
  ["ui_dashboard.png", "الـ dashboard"],
  ["ui_upload.png", "صفحة رفع الأشعة (upload) مع اختيار الـ model"],
], 250, 150));

A(H2("B2. الـ Backend (FastAPI)"));
A(P("الـ backend عبارة عن FastAPI service بالـ Python. FastAPI غير متزامن (asynchronous)، يعني بيقدر يخدم طلبات كتير في نفس الوقت من غير ما يتعطّل: وهو مستني الـ database أو الـ model، بيخدم غيره. مكوّناته:"));
A(bullet([t("Routers: ", { bold: true }), t("الـ API متقسّم حسب المورد لـ auth و patients و x-ray، وده بينظّم الكود.")]));
A(bullet([t("Pydantic models: ", { bold: true }), t("كل request و response بيتحقّق منه ضد schema بأنواع محددة، فالبيانات الغلط بترفض أوتوماتيك برسالة واضحة.")]));
A(bullet([t("Lifespan startup: ", { bold: true }), t("لما الـ server يقوم بيتوصّل بـ MongoDB ويعمل warmup للـ default model (يحمّله في الذاكرة مرة واحدة)، وبينضّف عند الإغلاق.")]));
A(bullet([t("Model warmup (singleton): ", { bold: true }), t("الـ model بيتحمّل مرة واحدة عند الإقلاع وبيتعاد استخدامه لكل طلب، فالمستخدم مبيدفعش تكلفة التحميل (ثواني) كل مرة. ده أهم قرار للأداء.")]));

A(H2("B3. الـ Inference Service خطوة بخطوة"));
A(P("ده قلب الـ backend. لما الصورة توصل، بيعمل:"));
A(bullet([t("Validate: ", { bold: true }), t("نوع الملف مسموح (jpg/png/...)، الحجم أقل من 10MB، وإنه فعلًا بيتفكّ كصورة.")]));
A(bullet([t("Model registry lookup: ", { bold: true }), t("بيدوّر على الـ model في registry (جدول بيربط مفتاح الـ model بالـ weights والـ task والـ thresholds). الـ registry فيه دلوقتي 6 models: YOLO، Faster R-CNN، SSDlite (detection)، وResNet50، DenseNet121، EfficientNet-B0 (classification).")]));
A(bullet([t("Predict: ", { bold: true }), t("بيشغّل الـ model عشان يطلّع التنبؤات الخام (boxes + scores، أو احتمال class).")]));
A(bullet([t("Non-Maximum Suppression (NMS): ", { bold: true }), t("الـ detectors بيطلّعوا كذا box متداخل لنفس المنطقة؛ الـ NMS بيسيب أعلى box ثقة ويشيل اللي بيتداخل معاه أكتر من 30%، فالدكتور يشوف box واحد نضيف لكل منطقة. (Faster R-CNN بيعمل NMS داخليًا، فبنطبّقه على YOLO بس.)")]));
A(bullet([t("Render + XAI: ", { bold: true }), t("بيرسم الصورة المعلَّمة (annotated) وheatmap الـ explainability.")]));
A(bullet([t("Respond: ", { bold: true }), t("بيرجّع نتيجة منظّمة: القرار، الـ boxes، الثقة، وقت المعالجة، ومسارات الصور، وبعدين الـ backend بيحفظها.")]));
A(P([t("الـ confidence thresholds: ", { bold: true }), t("الـ detection فوق 0.10 بيتعرض كـ 'مشتبه' (suspected)؛ وفوق 0.25 بيتعامل كـ finding مؤكّد. الـ thresholds دي قابلة للضبط لكل model في الـ registry.")]));
A(...fig("dataflow.png", "شكل B2. مسار البيانات للتنبؤ (prediction data flow).", 600, 142));

A(H2("B4. الـ Security"));
A(bullet([t("JWT authentication: ", { bold: true }), t("عند الـ login السيرفر بيصدر JSON Web Token موقّع (تذكرة مضادة للتزوير وبتنتهي). المتصفح بيبعته مع كل request، والسيرفر بيتأكد من التوقيع عشان يعرف إنت مين من غير sessions على السيرفر.")]));
A(bullet([t("bcrypt password hashing: ", { bold: true }), t("الباسوردات مبتتخزنش plaintext أبدًا. bcrypt بيضيف salt عشوائي وبطيء بقصد، فده بيصعّب كسر قواعد بيانات الباسوردات المسروقة.")]));
A(bullet([t("Per-user authorization: ", { bold: true }), t("كل database query متفلتر بـ id الدكتور المسجّل، فمفيش دكتور يقدر يقرأ مرضى دكتور تاني. ده متختبر.")]));
A(bullet([t("Input validation + CORS: ", { bold: true }), t("الـ uploads بتتفحص قبل ما توصل لأي model، والـ API بيقبل طلبات من origins معروفة بس.")]));
A(bullet([t("Production secret guard: ", { bold: true }), t("السيرفر بيرفض يقوم في الـ production بالـ secret key الافتراضي، فبيمنع غلطة نشر شائعة وخطيرة.")]));

A(H2("B5. الـ Database (MongoDB)"));
A(P("بنستخدم MongoDB، وهو document database، من خلال الـ Motor driver غير المتزامن. فيه ثلاث collections: users و patients و xray_analyses. اخترنا document database لأن التحليل الواحد طبيعي إنه يبقى document واحد مكتفي بذاته (الـ boxes والـ scores ومسارات الـ heatmaps والـ timestamps بنقراهم مع بعض دايمًا)، وده بيتطابق مع document شبه JSON ويتجنّب الـ joins المعقّدة. وفي unique indexes بتمنع تكرار الإيميلات والمعرّفات، وcompound index على المالك + وقت الإنشاء بيخلّي تحميل history الدكتور سريع."));
A(...fig("erd.png", "شكل B3. الـ Entity Relationship Diagram للـ collections.", 520, 320));

A(H2("B6. الـ API"));
A(...table(["Endpoint", "Method", "بيعمل إيه"], [
  ["/api/auth/signup, /login, /me", "POST/GET", "تسجيل، login (بيرجّع token)، بيانات المستخدم الحالي"],
  ["/api/patients", "CRUD", "إنشاء/قراءة/تعديل/حذف المرضى (لكل دكتور)"],
  ["/api/xray/upload", "POST", "رفع صورة، تشغيل inference، حفظ النتيجة"],
  ["/api/xray, /api/xray/{id}", "GET/DELETE", "عرض أو إدارة التحاليل المحفوظة"],
  ["/health, /docs", "GET", "فحص الصحة؛ توثيق Swagger تفاعلي"],
], [3600, 1600, 3800]));

A(H2("B7. رحلة طلب كاملة من الأول للآخر"));
A(P("1) الدكتور بيعمل login؛ الـ frontend بيخزّن الـ JWT. 2) بيفتح مريض ويرفع أشعة؛ صفحة الرفع بتوريه preview ويختار الـ model. 3) الـ API service بيبعت الصورة (مع الـ token) لـ /api/xray/upload. 4) FastAPI بيتأكد من الـ token، بيفحص الملف، ويسلّمه للـ inference service. 5) الـ model المحمّل بيتنبأ؛ الـ NMS بينضّف الـ boxes؛ وheatmap بيترسم. 6) النتيجة بتتكتب في collection الـ xray_analyses والصورة المعلَّمة بتتحفظ. 7) الـ backend بيرجّع النتيجة المنظّمة؛ والـ frontend بيعرضها في شاشة النتيجة ويضيفها لـ history المريض."));
A(...imageGrid([
  ["ui_result.png", "شاشة النتيجة: القرار + الـ box + نسبة الثقة + التوصيات"],
  ["ui_records.png", "سجل التحاليل (records) لكل مريض"],
], 280, 175));
A(...fig("ui_record_detail.png", "شكل B4. تفاصيل تحليل محفوظ (record detail) بكل النواتج.", 420, 260));

A(H2("B8. الـ Deployment والإعداد"));
A(bullet([t("الإعدادات ", { bold: true }), t("بتعيش في environment variables (الـ database URL، الـ secret key، الـ allowed origins، مدة الـ token)، وبعيدة عن الـ version control.")]));
A(bullet([t("الـ Model weights ", { bold: true }), t("بتتخزّن بـ Git LFS لأنها ملفات binary كبيرة، فالـ repository يفضل صغير والـ clone بيجيبها عند الحاجة.")]));
A(bullet([t("Scaling: ", { bold: true }), t("الـ API مبيمسكش حالة لكل مستخدم في الذاكرة (كل الحالة في الـ database والـ token)، فينفع ينتسخ ورا load balancer؛ والـ model ممكن يتنقل لـ service لوحده للأحمال التقيلة.")]));
A(bullet([t("التشغيل: ", { bold: true }), t("شغّل MongoDB، شغّل الـ backend بـ Uvicorn، ابني وقدّم الـ Angular frontend؛ الخطوات الكاملة في الـ README ودليل المستخدم في الـ thesis.")]));

A(H2("B9. القسم B - أسئلة متوقّعة من اللجنة"));
A(...qa("ليه FastAPI و async؟", "الـ inference والـ database calls بتتضمّن انتظار؛ السيرفر الـ async بيفضل يخدم باقي المستخدمين أثناء الانتظار، فالتطبيق يفضل سريع تحت الضغط من غير thread لكل request."));
A(...qa("ليه MongoDB مش SQL؟", "التحليل الواحد document متداخل مكتفي بذاته بنقراه كوحدة، وده بيناسب الـ document store ويتجنّب الـ joins. وبرضه بنفرض البنية بـ indexes و validation."));
A(...qa("الـ login بيشتغل إزاي بالظبط؟", "عند الـ login بنتأكد من الباسورد المعمول له bcrypt-hash وبنصدر JWT موقّع بمدة صلاحية. المتصفح بيبعت الـ token مع كل request، والسيرفر بيتأكد من التوقيع عشان يعرف المستخدم من غير sessions."));
A(...qa("بتمنعوا دكتور يشوف مرضى دكتور تاني إزاي؟", "كل query متفلتر بـ id الدكتور المسجّل، فالسجلات اللي مش بتاعته بترجع not-found. وعندنا automated test بيثبت إن الوصول عبر المستخدمين مرفوض."));
A(...qa("ليه بتحمّلوا الـ model مرة واحدة عند الإقلاع؟", "تحميل الـ model بياخد ثواني؛ لو عملناه لكل request هيخلّي التطبيق بطيء. بنحمّله مرة (warmup) ونعيد استخدامه، فكل تنبؤ سريع والذاكرة متوقّعة."));
A(...qa("الـ NMS ده إيه وليه محتاجينه؟", "الـ Non-Maximum Suppression بيشيل الـ boxes المكررة المتداخلة، ويسيب أعلى واحد ثقة لكل منطقة (هنا لما التداخل يعدّي 30%)، فالدكتور يشوف box واحد نضيف بدل كذا واحد."));
A(...qa("بتأمّنوا الـ uploads إزاي؟", "بنتأكد من النوع والحجم وإن الملف بيتفكّ كصورة قبل ما يوصل model؛ والـ API ورا authentication و CORS؛ والـ secrets في environment variables مش في الكود."));
A(...qa("هتعملوا scale للمستشفى إزاي؟", "الـ API stateless، فبنشغّل كذا نسخة ورا load balancer، وننقل الـ model لـ inference service أو GPU server مخصص، ونستخدم managed MongoDB cluster. الـ containerization والـ monitoring هما أول خطوة جاية."));

const doc = new Document({
  creator: "Team 19 - CSAI, Zewail City",
  title: "Chest X-ray Pneumonia Detection System - In-Depth Explanation (Arabic)",
  styles: {
    default: { document: { run: { font: FONT, size: 22 }, paragraph: { spacing: { line: 300, lineRule: "auto" } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, font: FONT, color: NAVY, rightToLeft: true }, paragraph: { bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { before: 280, after: 150 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: FONT, color: NAVY, rightToLeft: true }, paragraph: { bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { before: 220, after: 110 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, font: FONT, color: TEAL, rightToLeft: true }, paragraph: { bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { before: 150, after: 90 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.RIGHT, style: { paragraph: { indent: { right: 360, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER, children: [t("شرح متعمّق  |  Chest X-ray Pneumonia Detection System  |  Team 19  |  ", { size: 16, color: "888888" }), new TextRun({ children: ["Page ", PageNumber.CURRENT], font: FONT, size: 16, color: "888888" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("WROTE", OUT, buf.length, "bytes"); });
