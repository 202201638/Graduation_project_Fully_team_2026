import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';

import { AnalysisResult, AnalysisStateService } from '../analysis-state.service';
import { ApiPatientSummary, ApiService } from '../shared/api.service';
import { AuthService } from '../shared/auth.service';
import { NavbarComponent } from '../shared/navbar/navbar.component';
import { ProfileService } from '../profile/profile.service';

interface PatientRecordRow {
  analysisId: string;
  id: string;
  patientName: string;
  date: string;
  diagnosis: string;
  statusVariant: 'danger' | 'success' | 'warning';
  image?: string;
  confidence: number;
}

@Component({
  selector: 'app-patient-records',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, NavbarComponent],
  templateUrl: './patient-records.html',
  styleUrl: './patient-records.css',
})
export class PatientRecords implements OnInit, OnDestroy {
  search = '';
  diagnosisFilter = 'all';
  dateFilter = '';

  records: PatientRecordRow[] = [];
  filtered: PatientRecordRow[] = [];
  selected: PatientRecordRow | null = null;
  patients: ApiPatientSummary[] = [];
  errorMessage = '';

  readonly pageSize = 5;
  currentPage = 1;
  private historySubscription?: Subscription;

  constructor(
    private analysisState: AnalysisStateService,
    private apiService: ApiService,
    private authService: AuthService,
    private profileService: ProfileService,
    private router: Router,
  ) {}

  ngOnInit() {
    this.historySubscription = this.analysisState.history$.subscribe((history) => {
      this.records = history.map((result) => this.toRecordRow(result));
      this.applyFilters();
    });
    this.loadPatients();
    this.analysisState.loadAuthenticatedHistory();
  }

  ngOnDestroy(): void {
    this.historySubscription?.unsubscribe();
  }

  get avatarInitials(): string {
    return this.profileService.profile.avatarInitials;
  }

  get paged(): PatientRecordRow[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.filtered.slice(start, start + this.pageSize);
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filtered.length / this.pageSize));
  }

  private loadPatients(): void {
    const token = this.authService.getCurrentToken();
    if (!token) {
      this.errorMessage = 'Sign in to load patient records.';
      return;
    }

    this.apiService.getPatients(token).subscribe({
      next: (patients) => {
        this.patients = patients;
        this.errorMessage = '';
        this.records = this.analysisState.getHistory().map((result) => this.toRecordRow(result));
        this.applyFilters();
      },
      error: (error) => {
        this.errorMessage = error?.error?.detail || 'Unable to load patient records.';
      },
    });
  }

  private getPatientName(patientId: string): string {
    const patient = this.patients.find((item) => item.patient_id === patientId);
    return patient ? `${patient.first_name} ${patient.last_name}` : `Patient ${patientId}`;
  }

  private toRecordRow(result: AnalysisResult): PatientRecordRow {
    return {
      analysisId: result.analysisId,
      id: result.patientId,
      patientName: this.getPatientName(result.patientId),
      date: result.date,
      diagnosis: result.diagnosis,
      statusVariant: result.statusVariant,
      image: result.renderedImage || result.image,
      confidence: result.confidence,
    };
  }

  applyFilters() {
    const searchLower = this.search.trim().toLowerCase();

    this.filtered = this.records.filter((record) => {
      const matchesSearch =
        !searchLower ||
        record.id.toLowerCase().includes(searchLower) ||
        record.patientName.toLowerCase().includes(searchLower);

      const diagLower = record.diagnosis.toLowerCase();
      const matchesDiagnosis =
        this.diagnosisFilter === 'all'
          ? true
          : this.diagnosisFilter === 'pneumonia'
          ? record.statusVariant === 'danger'
          : this.diagnosisFilter === 'suspected'
          ? record.statusVariant === 'warning' || diagLower.includes('suspected')
          : this.diagnosisFilter === 'healthy'
          ? record.statusVariant === 'success' ||
            diagLower.includes('healthy') ||
            diagLower.includes('no pneumonia')
          : true;

      const matchesDate = !this.dateFilter || record.date === this.dateFilter;

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

  viewSelectedResult(): void {
    if (this.selected) {
      this.router.navigate(['/result', this.selected.analysisId]);
    }
  }

  private findAnalysisForSelected(): AnalysisResult | null {
    if (!this.selected) return null;
    return (
      this.analysisState
        .getHistory()
        .find((result) => result.analysisId === this.selected?.analysisId) || null
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
  ${r.renderedImage || r.image ? `<div class="section"><span class="label">X-ray Image:</span><br/><img src="${r.renderedImage || r.image}" alt="X-ray" /></div>` : ''}
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

    const current = this.findAnalysisForSelected();
    if (!current) {
      alert('Comparison is only available for saved scans.');
      return;
    }

    const samePatientHistory = this.analysisState
      .getHistory()
      .filter((item) => item.patientId === current.patientId);
    const index = samePatientHistory.findIndex((item) => item.analysisId === current.analysisId);
    const previous = samePatientHistory[index + 1];

    if (!previous) {
      alert('No previous scan found for this patient.');
      return;
    }

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
      ${previous.renderedImage ? `<img src="${previous.renderedImage}" alt="Previous X-ray" />` : '<div>No image available.</div>'}
    </div>
    <div class="card">
      <div class="title">Current Scan (${current.date})</div>
      <div>Patient ID: ${current.patientId}</div>
      <div>Diagnosis: ${current.diagnosis}</div>
      <div>Confidence: ${current.confidence}%</div>
      ${current.renderedImage ? `<img src="${current.renderedImage}" alt="Current X-ray" />` : '<div>No image available.</div>'}
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
