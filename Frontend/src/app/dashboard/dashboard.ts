import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';

import { AnalysisResult, AnalysisStateService } from '../analysis-state.service';
import { NavbarComponent } from '../shared/navbar/navbar.component';
import { ProfileService } from '../profile/profile.service';

interface DashboardActivity {
  analysisId: string;
  name: string;
  timestamp: string;
  diagnosis: string;
  confidence: string;
  statusLabel: string;
  statusVariant: 'danger' | 'success' | 'warning';
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit, OnDestroy {
  history: AnalysisResult[] = [];
  private historySubscription?: Subscription;

  constructor(
    private profileService: ProfileService,
    private analysisState: AnalysisStateService,
  ) {}

  ngOnInit(): void {
    this.historySubscription = this.analysisState.history$.subscribe((history) => {
      this.history = history;
    });
    this.analysisState.loadAuthenticatedHistory();
  }

  ngOnDestroy(): void {
    this.historySubscription?.unsubscribe();
  }

  get stats() {
    const total = this.history.length;
    const positive = this.history.filter((item) => item.detected).length;
    const averageConfidence =
      total > 0
        ? this.history.reduce((sum, item) => sum + item.confidence, 0) / total
        : 0;

    return [
      {
        label: 'Stored Analyses',
        value: String(total),
        description: 'Completed X-ray scans saved to this account.',
        accent: 'blue',
      },
      {
        label: 'Pneumonia Positive Cases',
        value: total ? `${Math.round((positive / total) * 100)}%` : '0%',
        description: 'Share of saved scans confirmed by the selected model.',
        accent: 'amber',
      },
      {
        label: 'Average Model Confidence',
        value: total ? `${averageConfidence.toFixed(1)}%` : '0%',
        description: 'Mean confidence across saved analyses.',
        accent: 'green',
      },
    ];
  }

  get activities(): DashboardActivity[] {
    return this.history.slice(0, 6).map((item) => ({
      analysisId: item.analysisId,
      name: `Patient ${item.patientId}`,
      timestamp: item.date,
      diagnosis: item.diagnosis,
      confidence: `${item.confidence.toFixed(1)}%`,
      statusLabel: item.diagnosis,
      statusVariant: item.statusVariant,
    }));
  }

  get displayName(): string {
    return this.profileService.profile.name;
  }

  get avatarInitials(): string {
    return this.profileService.profile.avatarInitials;
  }
}
