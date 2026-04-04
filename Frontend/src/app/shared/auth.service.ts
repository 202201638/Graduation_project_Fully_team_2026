import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private tokenSubject = new BehaviorSubject<string | null>(null);
  private userSubject = new BehaviorSubject<any | null>(null);

  token$ = this.tokenSubject.asObservable();
  user$ = this.userSubject.asObservable();

  constructor(private apiService: ApiService) {
    // Load token from localStorage on init (only in browser)
    if (typeof window !== 'undefined' && window.localStorage) {
      const savedToken = localStorage.getItem('auth_token');
      if (savedToken) {
        this.tokenSubject.next(savedToken);
        this.loadCurrentUser();
      }
    }
  }

  login(credentials: { email: string; password: string }) {
    return this.apiService.login(credentials);
  }

  signup(userData: any) {
    return this.apiService.signup(userData);
  }

  setToken(token: string) {
    // Only access localStorage in browser environment
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem('auth_token', token);
    }
    this.tokenSubject.next(token);
    this.loadCurrentUser();
  }

  private loadCurrentUser() {
    const token = this.tokenSubject.value;
    if (token) {
      this.apiService.getCurrentUser(token).subscribe({
        next: (user) => {
          this.userSubject.next(user);
        },
        error: () => {
          this.logout();
        }
      });
    }
  }

  logout() {
    // Only access localStorage in browser environment
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.removeItem('auth_token');
    }
    this.tokenSubject.next(null);
    this.userSubject.next(null);
  }

  isAuthenticated(): boolean {
    return !!this.tokenSubject.value;
  }

  getCurrentToken(): string | null {
    return this.tokenSubject.value;
  }

  getCurrentUser() {
    return this.userSubject.value;
  }
}
