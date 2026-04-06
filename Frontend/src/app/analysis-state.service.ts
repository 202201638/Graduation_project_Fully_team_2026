import { Injectable } from '@angular/core';
import { BehaviorSubject, forkJoin } from 'rxjs';
import {
  ApiAvailableModel,
  ApiDetectionPrediction,
  ApiDiagnosisStatus,
  ApiMetadataSummaryResponse,
  ApiModelStatusResponse,
  ApiService,
  ApiWebAnalysisResponse,
} from './shared/api.service';

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
  private processStateSubject = new BehaviorSubject<AnalysisProcessState>({ status: 'idle' });

  readonly metadata$ = this.metadataSubject.asObservable();
  readonly processState$ = this.processStateSubject.asObservable();

  constructor(private apiService: ApiService) {}

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
        'yolo_best.pt',
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

    this.apiService.analyzeXray(file, patientId, scanType, modelName).subscribe({
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
        this.lastResult = result;
        this.history = [result, ...this.history];
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
    this.lastResult = result;
    this.history = [result, ...this.history];
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
    this.resetProcessState();
  }
}
