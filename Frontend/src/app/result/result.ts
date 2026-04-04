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
    this.router.navigate(['/upload']);
  }

  downloadReport() {
    if (!this.result) return;

    const r = this.result;
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
  <div class="section"><span class="label">Patient ID:</span> ${r.patientId}</div>
  <div class="section"><span class="label">Scan type:</span> ${r.scanType}</div>
  <div class="section"><span class="label">Scan date:</span> ${r.date}</div>
  <div class="section"><span class="label">Diagnosis:</span> ${r.diagnosis}</div>
  <div class="section"><span class="label">Confidence:</span> ${r.confidence}%</div>
  ${r.image ? `<div class="section"><span class="label">X-ray Image:</span><br/><img src="${r.image}" alt="X-ray" /></div>` : ''}
</body>
</html>`;

    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(reportHtml);
    w.document.close();
    w.focus();
    w.print();
  }

  compareWithPreviousScan() {
    if (!this.result) return;

    const history = this.analysisState.getHistory();
    if (history.length < 2) {
      alert('No previous scans available for comparison.');
      return;
    }

    const currentIndex = history.lastIndexOf(this.result);
    const previousIndex = currentIndex > 0 ? currentIndex - 1 : history.length - 2;
    const previous = history[previousIndex];

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
      <div>Diagnosis: ${previous.diagnosis}</div>
      <div>Confidence: ${previous.confidence}%</div>
      ${previous.image ? `<img src="${previous.image}" alt="Previous X-ray" />` : '<div>No image available.</div>'}
    </div>
    <div class="card">
      <div class="title">Current Scan (${this.result.date})</div>
      <div>Patient ID: ${this.result.patientId}</div>
      <div>Diagnosis: ${this.result.diagnosis}</div>
      <div>Confidence: ${this.result.confidence}%</div>
      ${this.result.image ? `<img src="${this.result.image}" alt="Current X-ray" />` : '<div>No image available.</div>'}
    </div>
  </div>
</body>
</html>`;

    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(compareHtml);
    w.document.close();
    w.focus();
  }
}
