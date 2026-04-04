import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  // Authentication endpoints
  login(credentials: { email: string; password: string }): Observable<any> {
    return this.http.post(`${this.baseUrl}/auth/login`, credentials);
  }

  signup(userData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/auth/signup`, userData);
  }

  getCurrentUser(token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get(`${this.baseUrl}/auth/me`, { headers });
  }

  // Patient endpoints
  createPatient(patientData: any, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.post(`${this.baseUrl}/patients/`, patientData, { headers });
  }

  getPatient(token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get(`${this.baseUrl}/patients/`, { headers });
  }

  addMedicalHistory(medicalHistory: string, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.post(`${this.baseUrl}/patients/medical-history`, 
      { medical_history: medicalHistory }, { headers });
  }

  addAllergy(allergy: string, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.post(`${this.baseUrl}/patients/allergies`, 
      { allergy: allergy }, { headers });
  }

  addMedication(medication: string, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.post(`${this.baseUrl}/patients/medications`, 
      { medication: medication }, { headers });
  }

  // X-ray analysis endpoints
  uploadXray(file: File, patientId: string, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_id', patientId);
    
    return this.http.post(`${this.baseUrl}/xray/upload`, formData, { headers });
  }

  getAnalysis(analysisId: string, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get(`${this.baseUrl}/xray/${analysisId}`, { headers });
  }

  getAllAnalyses(token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get(`${this.baseUrl}/xray/`, { headers });
  }

  deleteAnalysis(analysisId: string, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.delete(`${this.baseUrl}/xray/${analysisId}`, { headers });
  }
}
