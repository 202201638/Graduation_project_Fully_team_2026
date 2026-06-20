import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import {
  AnalysisResult,
  AnalysisStateService,
  ExplainabilityMap,
} from '../analysis-state.service';
import { NavbarComponent } from '../shared/navbar/navbar.component';

type ImageTabKey = string;

interface ImageTab {
  key: ImageTabKey;
  label: string;
}

interface ReliabilityItem {
  label: string;
  value: string;
  hint: string;
}

@Component({
  selector: 'app-result',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  templateUrl: './result.html',
  styleUrl: './result.css',
})
export class Result implements OnInit {
  result: AnalysisResult | null = null;
  isLoading = false;
  errorMessage = '';
  activeImageTab: ImageTabKey = 'original';

  get statusLabel(): string {
    return this.result?.diagnosis || 'No pneumonia detected';
  }

  get isClassification(): boolean {
    return this.result?.modelFamily === 'classification';
  }

  get isDetection(): boolean {
    return this.result?.modelFamily === 'detection';
  }

  get confidenceLabel(): string {
    if (!this.result) {
      return '0%';
    }

    if (this.isClassification) {
      if (this.result.suspected) {
        return `${this.result.confidence}% pneumonia probability (below ${this.confirmationThresholdLabel} confirmation threshold)`;
      }

      return `${this.result.confidence}% pneumonia probability`;
    }

    if (!this.result.detected && !this.result.suspected && this.result.detections.length === 0) {
      return 'No region detected above threshold';
    }

    if (this.result.suspected) {
      return `${this.result.confidence}% (below ${this.confirmationThresholdLabel} confirmation threshold)`;
    }

    return `${this.result.confidence}%`;
  }

  get confidenceValue(): number {
    const value = this.result?.confidence ?? 0;
    return Math.max(0, Math.min(100, value));
  }

  get confidenceCaption(): string {
    if (this.isClassification) {
      return 'Pneumonia probability';
    }
    return 'Top region confidence';
  }

  get confirmationThresholdLabel(): string {
    const value = this.result?.analysisDetails?.['confirmed_conf'];
    const threshold = typeof value === 'number' ? value : this.isClassification ? 0.75 : 0.25;

    return `${(threshold * 100).toFixed(0)}%`;
  }

  // ---- Image viewer ---------------------------------------------------------

  get originalSrc(): string | undefined {
    return this.result?.originalImage || this.result?.image;
  }

  get explainabilityMaps(): ExplainabilityMap[] {
    return this.result?.explainabilityMaps ?? [];
  }

  get hasHeatmap(): boolean {
    return this.explainabilityMaps.length > 0 || !!this.result?.heatmapImage;
  }

  get imageTabs(): ImageTab[] {
    const tabs: ImageTab[] = [];
    for (const map of this.explainabilityMaps) {
      tabs.push({ key: `xai:${map.key}`, label: map.label });
    }
    if (this.result?.renderedImage) {
      tabs.push({ key: 'rendered', label: this.isDetection ? 'Detected regions' : 'Annotated' });
    }
    if (this.originalSrc) {
      tabs.push({ key: 'original', label: 'Original' });
    }
    return tabs;
  }

  private activeMap(): ExplainabilityMap | undefined {
    if (!this.activeImageTab.startsWith('xai:')) {
      return undefined;
    }
    const key = this.activeImageTab.slice('xai:'.length);
    return this.explainabilityMaps.find((map) => map.key === key);
  }

  get activeImageSrc(): string | undefined {
    if (!this.result) {
      return undefined;
    }
    const map = this.activeMap();
    if (map) {
      return map.image;
    }
    if (this.activeImageTab === 'rendered') {
      return this.result.renderedImage;
    }
    return this.originalSrc;
  }

  get activeImageCaption(): string {
    const map = this.activeMap();
    if (map) {
      return map.caption;
    }
    if (this.activeImageTab === 'rendered') {
      return this.isDetection
        ? 'Predicted pneumonia regions. Box colour reflects confidence relative to the confirmation threshold.'
        : 'Model output with the predicted probabilities.';
    }
    return 'The X-ray as uploaded, without annotations.';
  }

  selectImageTab(key: ImageTabKey): void {
    this.activeImageTab = key;
  }

  private initImageTab(): void {
    this.activeImageTab = this.imageTabs[0]?.key ?? 'original';
  }

  // ---- Doctor-facing interpretation ----------------------------------------

  get interpretation(): string {
    if (!this.result) {
      return '';
    }
    const r = this.result;

    if (this.isClassification) {
      const where = this.hasHeatmap
        ? ' The heatmap highlights the lung regions that drove this score.'
        : '';
      if (r.diagnosisStatus === 'pneumonia_detected') {
        return `The model assigns a high pneumonia probability (${r.confidence}%), above its confirmation threshold.${where}`;
      }
      if (r.diagnosisStatus === 'suspected_pneumonia') {
        return `The model assigns an intermediate pneumonia probability (${r.confidence}%), below the ${this.confirmationThresholdLabel} confirmation threshold. Treat as equivocal.${where}`;
      }
      return `The model assigns a low pneumonia probability (${r.confidence}%).${where}`;
    }

    const count = r.detections.length;
    if (count === 0) {
      return 'The model did not localise any pneumonia region above the detection threshold on this scan.';
    }
    const plural = count > 1 ? 's' : '';
    return `The model localised ${count} candidate region${plural} suspicious for pneumonia, outlined on the scan. Box colour reflects confidence relative to the confirmation threshold.`;
  }

  get reliabilityItems(): ReliabilityItem[] {
    if (!this.result) {
      return [];
    }

    if (this.isClassification) {
      return [
        { label: 'AUC', value: this.formatRatio(this.metric('auc')), hint: 'Overall ranking quality' },
        { label: 'Sensitivity', value: this.formatPercent(this.metric('recall')), hint: 'Pneumonia cases caught' },
        { label: 'Specificity', value: this.formatPercent(this.metric('specificity')), hint: 'Normal cases cleared' },
      ];
    }

    return [
      { label: 'mAP@0.5', value: this.formatRatio(this.metric('map50')), hint: 'Localisation accuracy' },
      { label: 'Recall', value: this.formatPercent(this.metric('recall')), hint: 'Regions caught' },
      { label: 'mAP@[.5:.95]', value: this.formatRatio(this.metric('map')), hint: 'Strict localisation' },
    ];
  }

  get hasReliability(): boolean {
    return this.reliabilityItems.some((item) => item.value !== 'n/a');
  }

  get reliabilityCaption(): string {
    return 'Measured on a held-out test set (RSNA Pneumonia Detection Challenge). Use as a guide to how much weight to give this result.';
  }

  get disclaimer(): string {
    return 'AI decision support, not a diagnosis. A qualified clinician must review the image and correlate with the clinical context before any decision.';
  }

  private metric(key: string): number | null {
    const value = this.result?.modelMetrics?.[key];
    return typeof value === 'number' ? value : null;
  }

  private formatRatio(value: number | null): string {
    return value == null ? 'n/a' : value.toFixed(3);
  }

  private formatPercent(value: number | null): string {
    return value == null ? 'n/a' : `${(value * 100).toFixed(1)}%`;
  }

  // ---- Model info -----------------------------------------------------------

  get metadataModelName(): string {
    return this.result?.modelDisplayName || 'n/a';
  }

  get metadataModelFamily(): string {
    const family = this.result?.modelFamily;
    return family ? family[0].toUpperCase() + family.slice(1) : 'n/a';
  }

  get metadataTask(): string {
    const task = this.result?.taskName;
    if (!task) {
      return 'n/a';
    }
    return task.replace(/_/g, ' ');
  }

  get metadataWeightsFile(): string {
    return this.result?.weightsFile || 'n/a';
  }

  get emptyDetectionsMessage(): string {
    if (this.isClassification) {
      return 'This is a classification model: it scores the whole image rather than drawing boxes. See the AI heatmap for localisation.';
    }

    return 'No bounding boxes were returned for this image.';
  }

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private analysisState: AnalysisStateService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit() {
    const analysisId = this.route.snapshot.paramMap.get('analysisId');
    const currentResult = this.analysisState.getResult();

    if (analysisId && currentResult?.analysisId !== analysisId) {
      this.isLoading = true;
      this.analysisState.loadStoredAnalysis(analysisId).subscribe({
        next: (result) => {
          this.result = result;
          this.initImageTab();
          this.isLoading = false;
          this.cdr.markForCheck();
        },
        error: (error) => {
          this.errorMessage = error?.message || 'Unable to load this saved analysis.';
          this.isLoading = false;
          this.cdr.markForCheck();
        },
      });
      return;
    }

    this.result = currentResult;
    if (!this.result) {
      this.router.navigate(['/records']);
      return;
    }
    this.initImageTab();
  }

  backToUpload() {
    this.analysisState.resetProcessState();
    this.router.navigate(['/upload']);
  }

  downloadReport() {
    if (!this.result) {
      return;
    }

    const r = this.result;
    const detectionsHtml = r.detections.length
      ? `<ul>${r.detections
          .map(
            (detection) =>
              `<li>${detection.label} - ${(detection.confidence * 100).toFixed(1)}% ` +
              `(${detection.bbox.x1}, ${detection.bbox.y1}) to (${detection.bbox.x2}, ${detection.bbox.y2})</li>`,
          )
          .join('')}</ul>`
      : `<div>${this.emptyDetectionsMessage}</div>`;

    const reliabilityHtml = this.hasReliability
      ? `<ul>${this.reliabilityItems
          .map((item) => `<li><b>${item.label}:</b> ${item.value} <span style="color:#64748b">(${item.hint})</span></li>`)
          .join('')}</ul>`
      : '';

    const imageBlock = (title: string, src?: string) =>
      src ? `<div class="section"><span class="label">${title}:</span><br/><img src="${src}" alt="${title}" /></div>` : '';

    const explainabilityBlocks = this.explainabilityMaps
      .map((map) => imageBlock(map.label, map.image))
      .join('');

    const reportHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AI Diagnosis Report</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 24px; color: #0f172a; }
    h1 { font-size: 20px; margin-bottom: 4px; }
    .sub { color: #64748b; margin-bottom: 16px; font-size: 13px; }
    .section { margin-bottom: 14px; }
    .label { font-weight: 600; }
    .images { display: flex; gap: 16px; flex-wrap: wrap; }
    .images > div { flex: 1; min-width: 240px; }
    img { max-width: 100%; height: auto; margin-top: 8px; border-radius: 8px; }
    .disclaimer { margin-top: 20px; padding: 12px; border: 1px solid #fcd34d; background: #fffbeb; border-radius: 8px; font-size: 13px; }
  </style>
</head>
<body>
  <h1>AI Diagnosis Report</h1>
  <div class="sub">${r.modelDisplayName} (${r.modelFamily}) &middot; ${r.date}</div>
  <div class="section"><span class="label">Analysis ID:</span> ${r.analysisId}</div>
  <div class="section"><span class="label">Patient ID:</span> ${r.patientId}</div>
  <div class="section"><span class="label">Scan type:</span> ${r.scanType}</div>
  <div class="section"><span class="label">Diagnosis:</span> ${r.diagnosis}</div>
  <div class="section"><span class="label">Confidence:</span> ${this.confidenceLabel}</div>
  <div class="section"><span class="label">Interpretation:</span> ${this.interpretation}</div>
  <div class="section"><span class="label">Findings:</span> ${r.findings}</div>
  <div class="section"><span class="label">Recommendations:</span> ${r.recommendations}</div>
  <div class="section"><span class="label">Detections:</span> ${detectionsHtml}</div>
  ${reliabilityHtml ? `<div class="section"><span class="label">Model reliability (held-out test set):</span> ${reliabilityHtml}</div>` : ''}
  <div class="images">
    ${explainabilityBlocks}
    ${imageBlock('Model output', r.renderedImage)}
    ${imageBlock('Original upload', this.originalSrc)}
  </div>
  <div class="disclaimer">${this.disclaimer}</div>
</body>
</html>`;

    const reportWindow = window.open('', '_blank');
    if (!reportWindow) {
      return;
    }

    reportWindow.document.write(reportHtml);
    reportWindow.document.close();
    reportWindow.focus();
    reportWindow.print();
  }

  compareWithPreviousScan() {
    if (!this.result) {
      return;
    }

    const history = this.analysisState.getHistory();
    if (history.length < 2) {
      alert('No previous scans available for comparison.');
      return;
    }

    const previous = history[1];
    const current = history[0];

    const compareHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Compare Scans</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 24px; }
    h1 { font-size: 20px; margin-bottom: 16px; }
    .grid { display: flex; gap: 16px; }
    .card { flex: 1; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; }
    .title { font-weight: 600; margin-bottom: 4px; }
    img { max-width: 100%; height: auto; border-radius: 8px; margin-top: 8px; }
  </style>
</head>
<body>
  <h1>Compare Scans</h1>
  <div class="grid">
    <div class="card">
      <div class="title">Previous Scan (${previous.date})</div>
      <div>Patient ID: ${previous.patientId}</div>
      <div>Model: ${previous.modelDisplayName}</div>
      <div>Diagnosis: ${previous.diagnosis}</div>
      <div>Confidence: ${previous.confidence}%</div>
      ${previous.heatmapImage || previous.renderedImage ? `<img src="${previous.heatmapImage || previous.renderedImage}" alt="Previous X-ray" />` : '<div>No image available.</div>'}
    </div>
    <div class="card">
      <div class="title">Current Scan (${current.date})</div>
      <div>Patient ID: ${current.patientId}</div>
      <div>Model: ${current.modelDisplayName}</div>
      <div>Diagnosis: ${current.diagnosis}</div>
      <div>Confidence: ${current.confidence}%</div>
      ${current.heatmapImage || current.renderedImage ? `<img src="${current.heatmapImage || current.renderedImage}" alt="Current X-ray" />` : '<div>No image available.</div>'}
    </div>
  </div>
</body>
</html>`;

    const compareWindow = window.open('', '_blank');
    if (!compareWindow) {
      return;
    }

    compareWindow.document.write(compareHtml);
    compareWindow.document.close();
    compareWindow.focus();
  }
}
