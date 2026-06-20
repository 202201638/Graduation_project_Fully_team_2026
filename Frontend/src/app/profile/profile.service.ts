import { Injectable, signal } from '@angular/core';

export interface UserProfile {
  name: string;
  role: string;
  email: string;
  avatarInitials: string;
}

@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly storageKey = 'mediscan_user_profile';
  private readonly defaultProfile: UserProfile = {
    name: 'Guest User',
    role: 'Guest',
    email: '',
    avatarInitials: 'GU',
  };

  // Signal-backed so any template reading profile.* through a getter becomes reactive:
  // when the authenticated user loads asynchronously, the navbar/avatar/name update without
  // needing a click (the app runs zoneless - see app.config.ts).
  private readonly _profile = signal<UserProfile>({ ...this.defaultProfile });

  constructor() {
    this.loadFromStorage();
  }

  get profile(): UserProfile {
    return this._profile();
  }

  updateProfile(update: Partial<UserProfile>): void {
    this._profile.set({ ...this._profile(), ...update });
    this.saveToStorage();
  }

  resetProfile(): void {
    this._profile.set({ ...this.defaultProfile });
    this.saveToStorage();
  }

  private loadFromStorage(): void {
    try {
      if (typeof window === 'undefined' || !window.localStorage) {
        return;
      }

      const raw = window.localStorage.getItem(this.storageKey);
      if (!raw) {
        return;
      }

      const parsed = JSON.parse(raw) as Partial<UserProfile> | null;
      if (!parsed) {
        return;
      }

      this._profile.set({ ...this._profile(), ...parsed });
    } catch {
      // Ignore storage errors and fall back to defaults
    }
  }

  private saveToStorage(): void {
    try {
      if (typeof window === 'undefined' || !window.localStorage) {
        return;
      }

      window.localStorage.setItem(this.storageKey, JSON.stringify(this._profile()));
    } catch {
      // Ignore storage errors
    }
  }
}
