import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';
import { AnalysisStateService } from '../analysis-state.service';

@Component({
  selector: 'app-processing',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './processing.html',
  styleUrl: './processing.css',
})
export class Processing implements OnInit, OnDestroy {
  errorMessage = '';
  selectedModelDisplayName = 'Selected model';
  selectedModelFamily = '';

  private processSubscription?: Subscription;

  constructor(
    private router: Router,
    private analysisState: AnalysisStateService,
  ) {}

  ngOnInit() {
    const draft = this.analysisState.getDraft();
    if (draft) {
      this.selectedModelDisplayName = draft.modelDisplayName || draft.modelName;
      this.selectedModelFamily = draft.modelFamily || '';
    }

    const currentState = this.analysisState.getProcessState();

    if (currentState.status === 'completed' && this.analysisState.getResult()) {
      this.router.navigate(['/result', this.analysisState.getResult()!.analysisId]);
      return;
    }

    if (currentState.status === 'idle') {
      this.router.navigate(['/upload']);
      return;
    }

    if (currentState.status === 'error') {
      this.errorMessage = currentState.error || 'The analysis request failed.';
    }

    this.processSubscription = this.analysisState.processState$.subscribe((state) => {
      if (state.status === 'completed' && this.analysisState.getResult()) {
        this.router.navigate(['/result', this.analysisState.getResult()!.analysisId]);
      } else if (state.status === 'error') {
        this.errorMessage = state.error || 'The analysis request failed.';
      }
    });
  }

  ngOnDestroy() {
    this.processSubscription?.unsubscribe();
  }

  backToUpload() {
    this.analysisState.resetProcessState();
    this.router.navigate(['/upload']);
  }
}
