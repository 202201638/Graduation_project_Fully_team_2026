import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { AnalysisResult, AnalysisStateService } from '../analysis-state.service';
import { NavbarComponent } from '../shared/navbar/navbar.component';

interface PatientRecordRow {
  id: string;
  patientName: string;
  date: string;
  diagnosis: string;
  statusVariant: 'danger' | 'success' | 'neutral';
  image?: string;
  confidence: number;
  source: 'history' | 'sample';
}

@Component({
  selector: 'app-patient-records',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, NavbarComponent],
  templateUrl: './patient-records.html',
  styleUrl: './patient-records.css',
})
export class PatientRecords implements OnInit {
  search = '';
  diagnosisFilter = 'all'; // all | pneumonia | healthy
  dateFilter = '';

  records: PatientRecordRow[] = [];
  filtered: PatientRecordRow[] = [];
  selected: PatientRecordRow | null = null;

  readonly pageSize = 5;
  currentPage = 1;

  constructor(
    private analysisState: AnalysisStateService,
    private router: Router,
  ) {}

  ngOnInit() {
    const history = this.analysisState.getHistory();

    const historyRows: PatientRecordRow[] = history.map(
      (r: AnalysisResult, index: number) => ({
        id: r.patientId || `HX-${index + 1}`,
        patientName: `Patient ${r.patientId || index + 1}`,
        date: r.date,
        diagnosis: r.diagnosis,
        statusVariant: r.diagnosis.toLowerCase().includes('pneumonia')
          ? 'danger'
          : 'success',
        image: r.image,
        confidence: r.confidence,
        source: 'history',
      }),
    );

    const sampleRows: PatientRecordRow[] = [
      {
        id: 'PX001',
        patientName: 'Alice Smith',
        date: '2025-10-28',
        diagnosis: 'Pneumonia Detected',
        statusVariant: 'danger',
        confidence: 92.5,
        source: 'sample',
      },
      {
        id: 'PX002',
        patientName: 'Bob Johnson',
        date: '2025-10-27',
        diagnosis: 'Pneumonia Detected',
        statusVariant: 'danger',
        confidence: 89.1,
        source: 'sample',
      },
      {
        id: 'PX003',
        patientName: 'Carol White',
        date: '2025-10-25',
        diagnosis: 'Healthy',
        statusVariant: 'success',
        confidence: 97.2,
        source: 'sample',
      },
      {
        id: 'PX004',
        patientName: 'David Brown',
        date: '2025-10-24',
        diagnosis: 'Pneumonia Detected',
        statusVariant: 'danger',
        confidence: 90.4,
        source: 'sample',
      },
      {
        id: 'PX005',
        patientName: 'Eve Davis',
        date: '2025-10-23',
        diagnosis: 'Healthy',
        statusVariant: 'success',
        confidence: 95.3,
        source: 'sample',
      },
    ];

    // Show real uploads first, then samples
    this.records = [...historyRows, ...sampleRows];
    this.applyFilters();
  }

  get paged(): PatientRecordRow[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.filtered.slice(start, start + this.pageSize);
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filtered.length / this.pageSize));
  }

  applyFilters() {
    const searchLower = this.search.trim().toLowerCase();

    this.filtered = this.records.filter((r) => {
      const matchesSearch =
        !searchLower ||
        r.id.toLowerCase().includes(searchLower) ||
        r.patientName.toLowerCase().includes(searchLower);

      const diagLower = r.diagnosis.toLowerCase();
      const matchesDiagnosis =
        this.diagnosisFilter === 'all'
          ? true
          : this.diagnosisFilter === 'pneumonia'
          ? diagLower.includes('pneumonia')
          : this.diagnosisFilter === 'healthy'
          ? diagLower.includes('healthy')
          : true;

      const matchesDate = !this.dateFilter || r.date === this.dateFilter;

      return matchesSearch && matchesDiagnosis && matchesDate;
    });

    this.currentPage = 1;
    this.selected = this.filtered[0] || null;
  }

  onSearchChange() {
    this.applyFilters();
  }

  onDiagnosisChange() {
    this.applyFilters();
  }

  onDateChange() {
    this.applyFilters();
  }

  selectRecord(row: PatientRecordRow) {
    this.selected = row;
  }

  prevPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
    }
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
    }
  }

  private findAnalysisForSelected(): AnalysisResult | null {
    if (!this.selected) return null;
    const history = this.analysisState.getHistory();
    return (
      history.find(
        (r) => r.patientId === this.selected!.id && r.date === this.selected!.date,
      ) || null
    );
  }

  downloadSelectedReport() {
    const base = this.findAnalysisForSelected();
    if (!base && !this.selected) return;

    const r =
      base ||
      ({
        patientId: this.selected!.id,
        scanType: '',
        date: this.selected!.date,
        image: this.selected!.image,
        diagnosis: this.selected!.diagnosis,
        confidence: this.selected!.confidence,
      } as AnalysisResult);

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

  enableComparison() {
    if (!this.selected) return;

    const history = this.analysisState.getHistory();
    if (!history.length) {
      alert('No scans available for comparison.');
      return;
    }

    const base = this.findAnalysisForSelected();
    if (!base) {
      alert('Comparison is only available for scans uploaded in this session.');
      return;
    }

    const index = history.indexOf(base);
    if (index <= 0) {
      alert('No previous scan found for comparison.');
      return;
    }

    const previous = history[index - 1];

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
      <div class="title">Current Scan (${base.date})</div>
      <div>Patient ID: ${base.patientId}</div>
      <div>Diagnosis: ${base.diagnosis}</div>
      <div>Confidence: ${base.confidence}%</div>
      ${base.image ? `<img src="${base.image}" alt="Current X-ray" />` : '<div>No image available.</div>'}
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
