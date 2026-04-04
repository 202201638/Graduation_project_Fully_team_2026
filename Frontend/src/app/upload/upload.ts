import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AnalysisStateService } from '../analysis-state.service';
import { NavbarComponent } from '../shared/navbar/navbar.component';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, NavbarComponent],
  templateUrl: './upload.html',
  styleUrl: './upload.css',
})
export class Upload implements OnInit {
  private static readonly LETTERS = ['A', 'B', 'C', 'D', 'E', 'F'];
  private nextLetterIndex = 3; // first three are A, B, C

  private readonly makeLetter = (): string => {
    const letter = Upload.LETTERS[this.nextLetterIndex] ?? 'X';
    this.nextLetterIndex++;
    return letter;
  };

  patientId = '';
  scanType = '';
  private selectedFile: File | null = null;
  private selectedFilePreview: string | null = null;

  recentUploads: { id: string; date: string; image?: string; label?: string }[] = [
    {
      id: 'MS-798-B',
      date: '2025-10-28',
      label: 'A',
    },
    {
      id: 'MS-123-C',
      date: '2025-10-26',
      label: 'B',
    },
    {
      id: 'MS-456-D',
      date: '2025-10-24',
      label: 'C',
    },
  ];

  get canAnalyze(): boolean {
    return !!(this.selectedFilePreview && this.patientId && this.scanType);
  }

  constructor(
    private router: Router,
    private analysisState: AnalysisStateService,
  ) {}

  ngOnInit() {
    const history = this.analysisState.getHistory();
    if (!history.length) {
      return;
    }

    const historyItems = history.map((item) => ({
      id: item.patientId,
      date: item.date,
      image: item.image,
    }));

    this.recentUploads = [...historyItems, ...this.recentUploads];
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) {
      this.selectedFile = null;
      this.selectedFilePreview = null;
      return;
    }

    const file = input.files[0];
    this.selectedFile = file;

    const reader = new FileReader();
    reader.onload = () => {
      this.selectedFilePreview = reader.result as string;
    };
    reader.readAsDataURL(file);
  }

  onAnalyze() {
    if (!this.selectedFilePreview || !this.patientId || !this.scanType) {
      // Simple guard: all fields and an image are required.
      return;
    }

    const today = new Date().toISOString().slice(0, 10);

    const result = {
      patientId: this.patientId,
      scanType: this.scanType,
      date: today,
      image: this.selectedFilePreview!,
      diagnosis: 'Pneumonia Detected',
      confidence: 96,
    };

    // Save for Processing/Result pages
    this.analysisState.setResult(result);

    // Also add to recent uploads list
    this.recentUploads = [
      {
        id: this.patientId,
        date: today,
        image: this.selectedFilePreview!,
      },
      ...this.recentUploads,
    ];

    // Reset form state
    this.patientId = '';
    this.scanType = '';
    this.selectedFile = null;
    this.selectedFilePreview = null;

    const input = document.getElementById('xray-file') as HTMLInputElement | null;
    if (input) {
      input.value = '';
    }

    // Navigate to processing screen
    this.router.navigate(['/processing']);
  }
}
