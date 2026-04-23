import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ApiBoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface ApiDetectionPrediction {
  label: string;
  class_id: number;
  confidence: number;
  bbox: ApiBoundingBox;
}

export type ApiDiagnosisStatus =
  | 'pneumonia_detected'
  | 'suspected_pneumonia'
  | 'no_pneumonia_detected';

export interface ApiAnalysisResultPayload {
  pneumonia_detected: boolean;
  suspected_pneumonia?: boolean | null;
  diagnosis_status?: ApiDiagnosisStatus | null;
  confidence_score: number;
  findings: string;
  recommendations: string;
  analysis_details: Record<string, unknown>;
  detections: ApiDetectionPrediction[];
  original_image_url?: string | null;
  rendered_image_url?: string | null;
}

export interface ApiAvailableModel {
  key: string;
  display_name: string;
  model_family: string;
  model_type: string;
  task: string;
  weights_file: string;
  available: boolean;
  loaded?: boolean;
  class_names: string[];
  default_conf?: number | null;
  confirmed_conf?: number | null;
  default_imgsz?: number | null;
  input_size?: number | null;
  description?: string | null;
  metrics: Record<string, unknown>;
  primary_metric_label?: string | null;
  primary_metric_value?: number | null;
  secondary_metric_label?: string | null;
  secondary_metric_value?: number | null;
  load_error?: string | null;
}

export interface ApiWebAnalysisResponse {
  analysis_id: string;
  patient_id?: string | null;
  scan_type?: string | null;
  model_name?: string | null;
  model_display_name?: string | null;
  model_family?: string | null;
  image_filename: string;
  result: ApiAnalysisResultPayload;
  status: string;
  processing_time: number;
  created_at: string;
}

export interface ApiPatientSummary {
  id: string;
  patient_id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  phone: string;
  address: string;
  emergency_contact: string;
  created_at: string;
  updated_at: string;
}

export interface ApiPatientResponse extends ApiPatientSummary {
  medical_history: string[];
  allergies: string[];
  medications: string[];
}

export interface ApiAnalysisSummary {
  analysis_id: string;
  patient_id: string;
  scan_type?: string | null;
  image_url?: string | null;
  image_filename?: string | null;
  rendered_image_url?: string | null;
  status: string;
  model_name?: string | null;
  model_display_name?: string | null;
  model_family?: string | null;
  pneumonia_detected?: boolean | null;
  suspected_pneumonia?: boolean | null;
  diagnosis_status?: ApiDiagnosisStatus | null;
  confidence_score?: number | null;
  created_at: string;
}

export interface ApiStoredAnalysisResponse extends ApiWebAnalysisResponse {
  id: string;
  image_url: string;
  error_message?: string | null;
  updated_at: string;
}

export interface ApiModelStatusResponse {
  status: string;
  model_loaded: boolean;
  weights_file: string;
  weights_exists: boolean;
  model_type?: string | null;
  task?: string | null;
  class_names: string[];
  default_conf?: number | null;
  confirmed_conf?: number | null;
  default_imgsz?: number | null;
  default_model_key?: string | null;
  display_name?: string | null;
  model_family?: string | null;
  available_models: ApiAvailableModel[];
  metadata_available: Record<string, boolean>;
  load_error?: string | null;
}

export interface ApiMetadataSummaryResponse {
  manifest: Record<string, unknown>;
  baseline: Record<string, unknown>;
  web_result: Record<string, unknown>;
  demo_result?: Record<string, unknown>;
  available_models: ApiAvailableModel[];
  default_model_key?: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly backendBaseUrl = environment.backendBaseUrl.replace(/\/$/, '');
  private readonly apiBaseUrl = `${this.backendBaseUrl}/api`;

  constructor(private http: HttpClient) {}

  private buildAuthHeaders(token: string): HttpHeaders {
    return new HttpHeaders().set('Authorization', `Bearer ${token}`);
  }

  toAbsoluteUrl(path?: string | null): string | undefined {
    if (!path) {
      return undefined;
    }

    if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:')) {
      return path;
    }

    return `${this.backendBaseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  }

  // Authentication endpoints
  login(credentials: { email: string; password: string }): Observable<any> {
    return this.http.post(`${this.apiBaseUrl}/auth/login`, credentials);
  }

  signup(userData: any): Observable<any> {
    return this.http.post(`${this.apiBaseUrl}/auth/signup`, userData);
  }

  getCurrentUser(token: string): Observable<any> {
    return this.http.get(`${this.apiBaseUrl}/auth/me`, {
      headers: this.buildAuthHeaders(token),
    });
  }

  // Patient endpoints
  createPatient(patientData: any, token: string): Observable<ApiPatientResponse> {
    return this.http.post<ApiPatientResponse>(`${this.apiBaseUrl}/patients/`, patientData, {
      headers: this.buildAuthHeaders(token),
    });
  }

  getPatient(token: string): Observable<ApiPatientResponse> {
    return this.http.get<ApiPatientResponse>(`${this.apiBaseUrl}/patients/`, {
      headers: this.buildAuthHeaders(token),
    });
  }

  getPatients(token: string): Observable<ApiPatientSummary[]> {
    return this.http.get<ApiPatientSummary[]>(`${this.apiBaseUrl}/patients/list`, {
      headers: this.buildAuthHeaders(token),
    });
  }

  addMedicalHistory(medicalHistory: string, token: string): Observable<any> {
    return this.http.post(
      `${this.apiBaseUrl}/patients/medical-history`,
      { medical_history: medicalHistory },
      { headers: this.buildAuthHeaders(token) },
    );
  }

  addAllergy(allergy: string, token: string): Observable<any> {
    return this.http.post(
      `${this.apiBaseUrl}/patients/allergies`,
      { allergy },
      { headers: this.buildAuthHeaders(token) },
    );
  }

  addMedication(medication: string, token: string): Observable<any> {
    return this.http.post(
      `${this.apiBaseUrl}/patients/medications`,
      { medication },
      { headers: this.buildAuthHeaders(token) },
    );
  }

  // X-ray analysis endpoints
  uploadXray(
    file: File,
    patientId: string,
    scanType: string,
    token: string,
    modelName?: string,
  ): Observable<ApiStoredAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_id', patientId);
    formData.append('scan_type', scanType);
    if (modelName) {
      formData.append('model_name', modelName);
    }

    return this.http.post<ApiStoredAnalysisResponse>(`${this.apiBaseUrl}/xray/upload`, formData, {
      headers: this.buildAuthHeaders(token),
    });
  }

  analyzeXray(
    file: File,
    patientId?: string,
    scanType?: string,
    modelName?: string,
  ): Observable<ApiWebAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);

    if (patientId) {
      formData.append('patient_id', patientId);
    }

    if (scanType) {
      formData.append('scan_type', scanType);
    }

    if (modelName) {
      formData.append('model_name', modelName);
    }

    return this.http.post<ApiWebAnalysisResponse>(`${this.apiBaseUrl}/xray/analyze`, formData);
  }

  getModelStatus(): Observable<ApiModelStatusResponse> {
    return this.http.get<ApiModelStatusResponse>(`${this.apiBaseUrl}/xray/status`);
  }

  getXrayMetadata(): Observable<ApiMetadataSummaryResponse> {
    return this.http.get<ApiMetadataSummaryResponse>(`${this.apiBaseUrl}/xray/metadata`);
  }

  getAnalysis(analysisId: string, token: string): Observable<ApiStoredAnalysisResponse> {
    return this.http.get<ApiStoredAnalysisResponse>(`${this.apiBaseUrl}/xray/${analysisId}`, {
      headers: this.buildAuthHeaders(token),
    });
  }

  getAllAnalyses(token: string): Observable<ApiAnalysisSummary[]> {
    return this.http.get<ApiAnalysisSummary[]>(`${this.apiBaseUrl}/xray/`, {
      headers: this.buildAuthHeaders(token),
    });
  }

  deleteAnalysis(analysisId: string, token: string): Observable<any> {
    return this.http.delete(`${this.apiBaseUrl}/xray/${analysisId}`, {
      headers: this.buildAuthHeaders(token),
    });
  }
}
