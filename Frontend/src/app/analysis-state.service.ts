import { Injectable } from '@angular/core';

export interface AnalysisResult {
  patientId: string;
  scanType: string;
  date: string;
  image?: string;
  diagnosis: string;
  confidence: number;
}

@Injectable({ providedIn: 'root' })
export class AnalysisStateService {
  private lastResult: AnalysisResult | null = null;
  private history: AnalysisResult[] = [];

  setResult(result: AnalysisResult) {
    this.lastResult = result;
    this.history = [...this.history, result];
  }

  getResult(): AnalysisResult | null {
    return this.lastResult;
  }

  getHistory(): AnalysisResult[] {
    return this.history.slice();
  }

  clear() {
    this.lastResult = null;
  }
}
