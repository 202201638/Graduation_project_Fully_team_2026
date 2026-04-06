import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AnalysisMetadata, AnalysisStateService } from '../analysis-state.service';
import { ProfileService } from '../profile/profile.service';
import { NavbarComponent } from '../shared/navbar/navbar.component';
import { ApiAvailableModel } from '../shared/api.service';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, NavbarComponent],
  templateUrl: './upload.html',
  styleUrl: './upload.css',
})
export class Upload implements OnInit, OnDestroy {
  patientId = '';
  scanType = '';
  selectedModelKey = '';
  metadata: AnalysisMetadata | null = null;

  private selectedFile: File | null = null;
  selectedFilePreview: string | null = null;
  private metadataSubscription?: Subscription;

  recentUploads: { id: string; date: string; image?: string }[] = [];

  get canAnalyze(): boolean {
    return !!(
      this.selectedFile &&
      this.selectedFilePreview &&
      this.patientId &&
      this.scanType &&
      this.selectedModelKey
    );
  }

  get modelStatusLabel(): string {
    const status = this.metadata?.modelStatus?.status;

    if (status === 'ready') {
      return 'Ready';
    }

    if (status === 'degraded') {
      return 'Needs setup';
    }

    return 'Loading';
  }

  get availableModels(): ApiAvailableModel[] {
    return (this.metadata?.availableModels ?? []).filter((model) => model.available);
  }

  get selectedModel(): ApiAvailableModel | undefined {
    return this.availableModels.find((model) => model.key === this.selectedModelKey);
  }

  get weightsFile(): string {
    return this.selectedModel?.weights_file || 'n/a';
  }

  get taskName(): string {
    return this.selectedModel?.task || 'n/a';
  }

  get modelFamilyLabel(): string {
    const family = this.selectedModel?.model_family;
    return family ? family[0].toUpperCase() + family.slice(1) : 'n/a';
  }

  get classNamesLabel(): string {
    const classNames = this.selectedModel?.class_names ?? [];
    return classNames.length ? classNames.join(', ') : 'n/a';
  }

  get primaryMetricLabel(): string {
    return this.selectedModel?.primary_metric_label || 'Primary metric';
  }

  get primaryMetricValue(): string {
    return this.formatMetric(this.selectedModel?.primary_metric_value);
  }

  get secondaryMetricLabel(): string {
    return this.selectedModel?.secondary_metric_label || 'Threshold';
  }

  get secondaryMetricValue(): string {
    if (this.selectedModel?.secondary_metric_value != null) {
      return this.formatMetric(this.selectedModel.secondary_metric_value);
    }

    if (this.selectedModel?.confirmed_conf != null) {
      return `${(this.selectedModel.confirmed_conf * 100).toFixed(0)}% confirm`;
    }

    return 'n/a';
  }

  get selectedModelDescription(): string {
    return (
      this.selectedModel?.description ||
      'Select an available model to run pneumonia analysis on this upload.'
    );
  }

  get modelLoadError(): string | null {
    const value = this.metadata?.modelStatus?.load_error;
    return typeof value === 'string' && value ? value : null;
  }

  get avatarInitials(): string {
    return this.profileService.profile.avatarInitials;
  }

  constructor(
    private router: Router,
    private analysisState: AnalysisStateService,
    private profileService: ProfileService,
  ) {}

  ngOnInit() {
    const draft = this.analysisState.getDraft();
    if (draft) {
      this.patientId = draft.patientId;
      this.scanType = draft.scanType;
      this.selectedModelKey = draft.modelName;
      this.selectedFilePreview = draft.imagePreview ?? null;
    }

    this.metadata = this.analysisState.getMetadata();
    this.applyDefaultModel();
    this.metadataSubscription = this.analysisState.metadata$.subscribe((metadata) => {
      this.metadata = metadata;
      this.applyDefaultModel();
    });

    if (typeof window !== 'undefined') {
      this.analysisState.loadMetadata();
    }

    const history = this.analysisState.getHistory();
    this.recentUploads = history.slice(0, 6).map((item) => ({
      id: item.patientId,
      date: item.date,
      image: item.renderedImage || item.image,
    }));
  }

  ngOnDestroy() {
    this.metadataSubscription?.unsubscribe();
  }

  private applyDefaultModel() {
    if (this.selectedModelKey && this.availableModels.some((model) => model.key === this.selectedModelKey)) {
      return;
    }

    const defaultModel =
      this.availableModels.find((model) => model.key === this.metadata?.defaultModelKey) ||
      this.availableModels[0];

    this.selectedModelKey = defaultModel?.key || '';
  }

  private formatMetric(value?: number | null): string {
    if (typeof value !== 'number') {
      return 'n/a';
    }

    return value >= 0 && value <= 1 ? `${(value * 100).toFixed(1)}%` : value.toFixed(3);
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
    if (
      !this.selectedFile ||
      !this.selectedFilePreview ||
      !this.patientId ||
      !this.scanType ||
      !this.selectedModelKey
    ) {
      return;
    }

    this.analysisState.resetProcessState();
    this.analysisState.startAnalysis(
      this.selectedFile,
      this.patientId.trim(),
      this.scanType,
      this.selectedModelKey,
      this.selectedModel?.display_name,
      this.selectedModel?.model_family,
      this.selectedFilePreview,
    );
    this.router.navigate(['/processing']);
  }
}
