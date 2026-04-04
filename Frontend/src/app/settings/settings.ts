import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ProfileService } from '../profile/profile.service';
import { NavbarComponent } from '../shared/navbar/navbar.component';

interface ActiveSession {
  device: string;
  location: string;
  browser: string;
  lastActive: string;
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, NavbarComponent],
  templateUrl: './settings.html',
  styleUrl: './settings.css',
})
export class Settings {
  displayName = '';
  displayRole = '';
  avatarInitials = '';
  email = '';
  emailNotifications = true;
  smsNotifications = false;
  shareAnonymizedData = false;
  twoFactorAuth = true;
  appTheme: 'system' | 'light' | 'dark' = 'system';
  language = 'en';

  activeSessions: ActiveSession[] = [
    {
      device: 'Desktop - Chrome',
      location: 'New York, USA',
      browser: 'Chrome 120.0',
      lastActive: 'Last active 2 hours ago',
    },
    {
      device: 'Mobile - Safari',
      location: 'Los Angeles, USA',
      browser: 'Safari iOS 16.4',
      lastActive: 'Last active 26 minutes ago',
    },
  ];

  constructor(private profileService: ProfileService) {
    this.resetToDefaults();
  }

  onSave(): void {
    this.profileService.updateProfile({
      name: this.displayName,
      role: this.displayRole,
      email: this.email,
      avatarInitials: this.avatarInitials,
    });

    console.log('Settings saved', {
      name: this.displayName,
      role: this.displayRole,
      email: this.email,
      emailNotifications: this.emailNotifications,
      smsNotifications: this.smsNotifications,
      shareAnonymizedData: this.shareAnonymizedData,
      twoFactorAuth: this.twoFactorAuth,
      appTheme: this.appTheme,
      language: this.language,
    });
  }

  onCancel(): void {
    this.resetToDefaults();
  }

  onDeleteAccount(): void {
    alert('Account deletion is not implemented in this demo.');
  }

  private resetToDefaults(): void {
    const profile = this.profileService.profile;
    this.displayName = profile.name;
    this.displayRole = profile.role;
    this.avatarInitials = profile.avatarInitials;
    this.email = profile.email;
    this.emailNotifications = true;
    this.smsNotifications = false;
    this.shareAnonymizedData = false;
    this.twoFactorAuth = true;
    this.appTheme = 'system';
    this.language = 'en';
  }
}
