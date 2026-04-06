import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Router } from '@angular/router';
import { ApiService } from './api.service';
import { ProfileService } from '../profile/profile.service';

export interface AuthUser {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly tokenStorageKey = 'auth_token';
  private tokenSubject = new BehaviorSubject<string | null>(null);
  private userSubject = new BehaviorSubject<AuthUser | null>(null);

  token$ = this.tokenSubject.asObservable();
  user$ = this.userSubject.asObservable();

  constructor(
    private apiService: ApiService,
    private profileService: ProfileService,
    private router: Router,
  ) {
    if (typeof window !== 'undefined' && window.localStorage) {
      const savedToken = window.localStorage.getItem(this.tokenStorageKey);
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

  setSession(token: string, user?: AuthUser | null) {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(this.tokenStorageKey, token);
    }

    this.tokenSubject.next(token);

    if (user) {
      this.userSubject.next(user);
      this.syncProfile(user);
      return;
    }

    this.loadCurrentUser();
  }

  setToken(token: string) {
    this.setSession(token);
  }

  private loadCurrentUser() {
    const token = this.tokenSubject.value;
    if (!token) {
      return;
    }

    this.apiService.getCurrentUser(token).subscribe({
      next: (user) => {
        const authUser: AuthUser = {
          user_id: user.user_id,
          email: user.email,
          full_name: user.full_name,
          role: user.role,
        };

        this.userSubject.next(authUser);
        this.syncProfile(authUser);
      },
      error: () => {
        this.logout();
      }
    });
  }

  logout(redirectToLogin = true) {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.removeItem(this.tokenStorageKey);
    }

    this.tokenSubject.next(null);
    this.userSubject.next(null);
    this.profileService.resetProfile();

    if (redirectToLogin) {
      this.router.navigateByUrl('/login');
    }
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

  private syncProfile(user: AuthUser): void {
    this.profileService.updateProfile({
      name: user.full_name,
      role: this.formatRole(user.role),
      email: user.email,
      avatarInitials: this.makeInitials(user.full_name),
    });
  }

  private formatRole(role: string): string {
    if (!role) {
      return 'User';
    }

    return role.charAt(0).toUpperCase() + role.slice(1);
  }

  private makeInitials(fullName: string): string {
    const parts = fullName
      .split(' ')
      .map((part) => part.trim())
      .filter(Boolean)
      .slice(0, 2);

    if (!parts.length) {
      return 'US';
    }

    return parts.map((part) => part[0].toUpperCase()).join('');
  }
}
