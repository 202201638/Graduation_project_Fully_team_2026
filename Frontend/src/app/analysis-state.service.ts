import { Injectable } from '@angular/core';
import { BehaviorSubject, forkJoin } from 'rxjs';
import { map, tap, throwError } from 'rxjs';
import {
  ApiAnalysisSummary,
  ApiAvailableModel,
  ApiDetectionPrediction,
  ApiDiagnosisStatus,
  ApiMetadataSummaryResponse,
  ApiModelStatusResponse,
  ApiService,
  ApiStoredAnalysisResponse,
  ApiWebAnalysisResponse,
} from './shared/api.service';
import { AuthService } from './shared/auth.service';

export interface AnalysisMetadata {
  manifest: Record<string, unknown>;
  baseline: Record<string, unknown>;
  webResult: Record<string, unknown>;
  demoResult?: Record<string, unknown>;
  availableModels: ApiAvailableModel[];
  defaultModelKey?: string;
  modelStatus?: ApiModelStatusResponse;
}

export interface AnalysisDraft {
  patientId: string;
  scanType: string;
  modelName: string;
  modelDisplayName?: string;
  modelFamily?: string;
  imagePreview?: string | null;
}

export type DiagnosisStatus = ApiDiagnosisStatus;
export type DiagnosisVariant = 'danger' | 'warning' | 'success';

export interface AnalysisResult {
  analysisId: string;
  patientId: string;
  scanType: string;
  date: string;
  image?: string;
  originalImage?: string;
  renderedImage?: string;
  diagnosis: string;
  diagnosisStatus: DiagnosisStatus;
  statusVariant: DiagnosisVariant;
  modelName: string;
  modelDisplayName: string;
  modelFamily: string;
  taskName: string;
  weightsFile: string;
  analysisDetails: Record<string, unknown>;
  confidence: number;
  detected: boolean;
  suspected: boolean;
  findings: string;
  recommendations: string;
  detections: ApiDetectionPrediction[];
  processingTime: number;
  metadata?: AnalysisMetadata;
}

export interface AnalysisProcessState {
  status: 'idle' | 'processing' | 'completed' | 'error';
  error?: string;
}

@Injectable({ providedIn: 'root' })
export class AnalysisStateService {
  private lastResult: AnalysisResult | null = null;
  private history: AnalysisResult[] = [];
  private draft: AnalysisDraft | null = null;
  private metadataLoaded = false;

  private metadataSubject = new BehaviorSubject<AnalysisMetadata | null>(null);
  private historySubject = new BehaviorSubject<AnalysisResult[]>([]);
  private processStateSubject = new BehaviorSubject<AnalysisProcessState>({ status: 'idle' });

  readonly metadata$ = this.metadataSubject.asObservable();
  readonly history$ = this.historySubject.asObservable();
  readonly processState$ = this.processStateSubject.asObservable();

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
  ) {}

  private normalizeMetadata(
    metadata: ApiMetadataSummaryResponse,
    modelStatus: ApiModelStatusResponse,
  ): AnalysisMetadata {
    return {
      manifest: metadata.manifest,
      baseline: metadata.baseline,
      webResult: metadata.web_result,
      demoResult: metadata.demo_result,
      availableModels: metadata.available_models ?? [],
      defaultModelKey:
        typeof metadata.default_model_key === 'string' ? metadata.default_model_key : undefined,
      modelStatus,
    };
  }

  private toRecord(value: unknown): Record<string, unknown> {
    return value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
  }

  private pickModelCatalogEntry(modelName?: string | null): ApiAvailableModel | undefined {
    const models = this.metadataSubject.value?.availableModels ?? [];
    return models.find((model) => model.key === modelName);
  }

  private resolveResponseModel(response: ApiWebAnalysisResponse, draft: AnalysisDraft) {
    const analysisDetails = this.toRecord(response.result.analysis_details);
    const modelName =
      response.model_name ||
      (typeof analysisDetails['model_name'] === 'string' ? analysisDetails['model_name'] : undefined) ||
      draft.modelName;
    const metadataModel = this.pickModelCatalogEntry(modelName);

    return {
      modelName,
      modelDisplayName:
        response.model_display_name ||
        (typeof analysisDetails['model_display_name'] === 'string'
          ? analysisDetails['model_display_name']
          : undefined) ||
        draft.modelDisplayName ||
        metadataModel?.display_name ||
        modelName,
      modelFamily:
        response.model_family ||
        (typeof analysisDetails['model_family'] === 'string'
          ? analysisDetails['model_family']
          : undefined) ||
        draft.modelFamily ||
        metadataModel?.model_family ||
        'detection',
      taskName:
        (typeof analysisDetails['task'] === 'string' ? analysisDetails['task'] : undefined) ||
        metadataModel?.task ||
        'pneumonia_detection',
      weightsFile:
        (typeof analysisDetails['weights_file'] === 'string'
          ? analysisDetails['weights_file']
          : undefined) ||
        metadataModel?.weights_file ||
        'fasterrcnn.pt',
      analysisDetails,
    };
  }

  private resolveDiagnosisStatus(response: ApiWebAnalysisResponse): DiagnosisStatus {
    const diagnosisStatus = response.result.diagnosis_status;

    if (
      diagnosisStatus === 'pneumonia_detected' ||
      diagnosisStatus === 'suspected_pneumonia' ||
      diagnosisStatus === 'no_pneumonia_detected'
    ) {
      return diagnosisStatus;
    }

    if (response.result.suspected_pneumonia) {
      return 'suspected_pneumonia';
    }

    return response.result.pneumonia_detected
      ? 'pneumonia_detected'
      : 'no_pneumonia_detected';
  }

  private getDiagnosisLabel(diagnosisStatus: DiagnosisStatus): string {
    if (diagnosisStatus === 'pneumonia_detected') {
      return 'Pneumonia detected';
    }

    if (diagnosisStatus === 'suspected_pneumonia') {
      return 'Suspected pneumonia';
    }

    return 'No pneumonia detected';
  }

  private getStatusVariant(diagnosisStatus: DiagnosisStatus): DiagnosisVariant {
    if (diagnosisStatus === 'pneumonia_detected') {
      return 'danger';
    }

    if (diagnosisStatus === 'suspected_pneumonia') {
      return 'warning';
    }

    return 'success';
  }

  private mapResponseToResult(
    response: ApiWebAnalysisResponse,
    draft: AnalysisDraft,
  ): AnalysisResult {
    const diagnosisStatus = this.resolveDiagnosisStatus(response);
    const confidence = Math.round(response.result.confidence_score * 1000) / 10;
    const model = this.resolveResponseModel(response, draft);

    return {
      analysisId: response.analysis_id,
      patientId: response.patient_id || draft.patientId,
      scanType: response.scan_type || draft.scanType,
      date: response.created_at.slice(0, 10),
      image: draft.imagePreview ?? undefined,
      originalImage:
        this.apiService.toAbsoluteUrl(response.result.original_image_url) || draft.imagePreview || undefined,
      renderedImage:
        this.apiService.toAbsoluteUrl(response.result.rendered_image_url) || draft.imagePreview || undefined,
      diagnosis: this.getDiagnosisLabel(diagnosisStatus),
      diagnosisStatus,
      statusVariant: this.getStatusVariant(diagnosisStatus),
      modelName: model.modelName,
      modelDisplayName: model.modelDisplayName,
      modelFamily: model.modelFamily,
      taskName: model.taskName,
      weightsFile: model.weightsFile,
      analysisDetails: model.analysisDetails,
      confidence,
      detected: diagnosisStatus === 'pneumonia_detected',
      suspected: diagnosisStatus === 'suspected_pneumonia',
      findings: response.result.findings,
      recommendations: response.result.recommendations,
      detections: response.result.detections,
      processingTime: response.processing_time,
      metadata: this.metadataSubject.value ?? undefined,
    };
  }

  private mapSummaryToResult(summary: ApiAnalysisSummary): AnalysisResult {
    const diagnosisStatus = summary.diagnosis_status || 'no_pneumonia_detected';
    const confidence = Math.round((summary.confidence_score || 0) * 1000) / 10;

    return {
      analysisId: summary.analysis_id,
      patientId: summary.patient_id,
      scanType: summary.scan_type || '',
      date: summary.created_at.slice(0, 10),
      image: this.apiService.toAbsoluteUrl(summary.rendered_image_url || summary.image_url),
      originalImage: this.apiService.toAbsoluteUrl(summary.image_url),
      renderedImage: this.apiService.toAbsoluteUrl(summary.rendered_image_url || summary.image_url),
      diagnosis: this.getDiagnosisLabel(diagnosisStatus),
      diagnosisStatus,
      statusVariant: this.getStatusVariant(diagnosisStatus),
      modelName: summary.model_name || '',
      modelDisplayName: summary.model_display_name || summary.model_name || 'Selected model',
      modelFamily: summary.model_family || 'detection',
      taskName: '',
      weightsFile: '',
      analysisDetails: {},
      confidence,
      detected: diagnosisStatus === 'pneumonia_detected',
      suspected: diagnosisStatus === 'suspected_pneumonia',
      findings: '',
      recommendations: '',
      detections: [],
      processingTime: 0,
      metadata: this.metadataSubject.value ?? undefined,
    };
  }

  private makeDraftFromStoredResponse(response: ApiStoredAnalysisResponse): AnalysisDraft {
    const analysisDetails = this.toRecord(response.result.analysis_details);

    return {
      patientId: response.patient_id || '',
      scanType: response.scan_type || '',
      modelName:
        response.model_name ||
        (typeof analysisDetails['model_name'] === 'string' ? analysisDetails['model_name'] : ''),
      modelDisplayName:
        response.model_display_name ||
        (typeof analysisDetails['model_display_name'] === 'string'
          ? analysisDetails['model_display_name']
          : undefined),
      modelFamily:
        response.model_family ||
        (typeof analysisDetails['model_family'] === 'string'
          ? analysisDetails['model_family']
          : undefined),
      imagePreview: this.apiService.toAbsoluteUrl(
        response.result.rendered_image_url || response.image_url,
      ),
    };
  }

  private rememberResult(result: AnalysisResult): void {
    this.lastResult = result;
    this.history = [result, ...this.history.filter((item) => item.analysisId !== result.analysisId)];
    this.historySubject.next(this.history.slice());
  }

  loadMetadata() {
    if (this.metadataLoaded) {
      return;
    }

    this.metadataLoaded = true;

    forkJoin({
      metadata: this.apiService.getXrayMetadata(),
      modelStatus: this.apiService.getModelStatus(),
    }).subscribe({
      next: ({ metadata, modelStatus }) => {
        this.metadataSubject.next(this.normalizeMetadata(metadata, modelStatus));
      },
      error: () => {
        this.metadataLoaded = false;
      },
    });
  }

  startAnalysis(
    file: File,
    patientId: string,
    scanType: string,
    modelName: string,
    modelDisplayName?: string,
    modelFamily?: string,
    imagePreview?: string | null,
  ) {
    this.draft = {
      patientId,
      scanType,
      modelName,
      modelDisplayName,
      modelFamily,
      imagePreview,
    };
    this.processStateSubject.next({ status: 'processing' });

    const token = this.authService.getCurrentToken();
    const request$ = token
      ? this.apiService.uploadXray(file, patientId, scanType, token, modelName)
      : this.apiService.analyzeXray(file, patientId, scanType, modelName);

    request$.subscribe({
      next: (response) => {
        const currentDraft = this.draft ?? {
          patientId,
          scanType,
          modelName,
          modelDisplayName,
          modelFamily,
          imagePreview,
        };
        const result = this.mapResponseToResult(response, currentDraft);
        this.rememberResult(result);
        this.draft = null;
        this.processStateSubject.next({ status: 'completed' });
      },
      error: (error) => {
        const detail =
          error?.error?.detail ||
          error?.message ||
          'Unable to analyze the image right now.';

        this.processStateSubject.next({
          status: 'error',
          error: detail,
        });
      },
    });
  }

  loadAuthenticatedHistory(): void {
    const token = this.authService.getCurrentToken();
    if (!token) {
      this.history = [];
      this.historySubject.next([]);
      return;
    }

    this.apiService.getAllAnalyses(token).subscribe({
      next: (summaries) => {
        this.history = summaries.map((summary) => this.mapSummaryToResult(summary));
        this.historySubject.next(this.history.slice());
      },
      error: () => {
        this.history = [];
        this.historySubject.next([]);
      },
    });
  }

  loadStoredAnalysis(analysisId: string) {
    const token = this.authService.getCurrentToken();
    if (!token) {
      return throwError(() => new Error('Sign in to view this analysis.'));
    }

    return this.apiService.getAnalysis(analysisId, token).pipe(
      map((response) => this.mapResponseToResult(response, this.makeDraftFromStoredResponse(response))),
      tap((result) => this.rememberResult(result)),
    );
  }

  getDraft(): AnalysisDraft | null {
    return this.draft;
  }

  getMetadata(): AnalysisMetadata | null {
    return this.metadataSubject.value;
  }

  getProcessState(): AnalysisProcessState {
    return this.processStateSubject.value;
  }

  resetProcessState() {
    this.processStateSubject.next({ status: 'idle' });
  }

  setResult(result: AnalysisResult) {
    this.rememberResult(result);
  }

  getResult(): AnalysisResult | null {
    return this.lastResult;
  }

  getHistory(): AnalysisResult[] {
    return this.history.slice();
  }

  clear() {
    this.lastResult = null;
    this.draft = null;
    this.history = [];
    this.historySubject.next([]);
    this.resetProcessState();
  }
}
