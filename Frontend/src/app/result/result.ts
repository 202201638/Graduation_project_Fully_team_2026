import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { AnalysisResult, AnalysisStateService } from '../analysis-state.service';

@Component({
  selector: 'app-result',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './result.html',
  styleUrl: './result.css',
})
export class Result implements OnInit {
  result: AnalysisResult | null = null;

  get statusLabel(): string {
    return this.result?.diagnosis || 'No pneumonia detected';
  }

  get confidenceLabel(): string {
    if (!this.result) {
      return '0%';
    }

    if (this.result.modelFamily === 'classification') {
      if (this.result.suspected) {
        return `${this.result.confidence}% pneumonia probability (below ${this.confirmationThresholdLabel} confirmation threshold)`;
      }

      return `${this.result.confidence}% pneumonia probability`;
    }

    if (!this.result.detected && !this.result.suspected && this.result.detections.length === 0) {
      return '0% (no detection above threshold)';
    }

    if (this.result.suspected) {
      return `${this.result.confidence}% (below ${this.confirmationThresholdLabel} confirmation threshold)`;
    }

    return `${this.result.confidence}%`;
  }

  get confirmationThresholdLabel(): string {
    const value = this.result?.analysisDetails?.['confirmed_conf'];
    const threshold = typeof value === 'number' ? value : 0.25;

    return `${(threshold * 100).toFixed(0)}%`;
  }

  get metadataWeightsFile(): string {
    return this.result?.weightsFile || 'n/a';
  }

  get metadataTask(): string {
    return this.result?.taskName || 'n/a';
  }

  get metadataModelName(): string {
    return this.result?.modelDisplayName || 'n/a';
  }

  get metadataModelFamily(): string {
    const family = this.result?.modelFamily;
    return family ? family[0].toUpperCase() + family.slice(1) : 'n/a';
  }

  get emptyDetectionsMessage(): string {
    if (this.result?.modelFamily === 'classification') {
      return 'This classification model does not return bounding boxes.';
    }

    return 'No bounding boxes were returned for this image.';
  }

  get metadataWebDetected(): string {
    const demoValue = this.result?.metadata?.demoResult?.['detected'];
    if (typeof demoValue === 'boolean') {
      return String(demoValue);
    }

    const summary = this.result?.metadata?.webResult?.['summary'];
    if (summary && typeof summary === 'object') {
      const summaryValue = (summary as Record<string, unknown>)['demo_detected'];
      if (typeof summaryValue === 'boolean') {
        return String(summaryValue);
      }
    }

    return 'n/a';
  }

  get metadataWebConfidence(): string {
    const demoValue = this.result?.metadata?.demoResult?.['confidence'];
    if (typeof demoValue === 'number') {
      return String(demoValue);
    }

    const summary = this.result?.metadata?.webResult?.['summary'];
    if (summary && typeof summary === 'object') {
      const summaryValue = (summary as Record<string, unknown>)['demo_confidence'];
      if (typeof summaryValue === 'number') {
        return String(summaryValue);
      }
    }

    return 'n/a';
  }

  constructor(
    private router: Router,
    private analysisState: AnalysisStateService,
  ) {}

  ngOnInit() {
    this.result = this.analysisState.getResult();
    if (!this.result) {
      this.router.navigate(['/upload']);
    }
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

    const reportHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AI Diagnosis Report</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 24px; }
    h1 { font-size: 20px; margin-bottom: 16px; }
    .section { margin-bottom: 16px; }
    .label { font-weight: 600; }
    img { max-width: 100%; height: auto; margin-top: 8px; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>AI Diagnosis Report</h1>
  <div class="section"><span class="label">Analysis ID:</span> ${r.analysisId}</div>
  <div class="section"><span class="label">Patient ID:</span> ${r.patientId}</div>
  <div class="section"><span class="label">Scan type:</span> ${r.scanType}</div>
  <div class="section"><span class="label">Model:</span> ${r.modelDisplayName}</div>
  <div class="section"><span class="label">Model family:</span> ${r.modelFamily}</div>
  <div class="section"><span class="label">Scan date:</span> ${r.date}</div>
  <div class="section"><span class="label">Diagnosis:</span> ${r.diagnosis}</div>
  <div class="section"><span class="label">Confidence:</span> ${r.confidence}%</div>
  <div class="section"><span class="label">Findings:</span> ${r.findings}</div>
  <div class="section"><span class="label">Recommendations:</span> ${r.recommendations}</div>
  <div class="section"><span class="label">Detections:</span> ${detectionsHtml}</div>
  ${r.renderedImage ? `<div class="section"><span class="label">Rendered output:</span><br/><img src="${r.renderedImage}" alt="Rendered X-ray" /></div>` : ''}
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
      ${previous.renderedImage ? `<img src="${previous.renderedImage}" alt="Previous X-ray" />` : '<div>No image available.</div>'}
    </div>
    <div class="card">
      <div class="title">Current Scan (${current.date})</div>
      <div>Patient ID: ${current.patientId}</div>
      <div>Model: ${current.modelDisplayName}</div>
      <div>Diagnosis: ${current.diagnosis}</div>
      <div>Confidence: ${current.confidence}%</div>
      ${current.renderedImage ? `<img src="${current.renderedImage}" alt="Current X-ray" />` : '<div>No image available.</div>'}
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
