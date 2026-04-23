import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ProfileService } from '../profile/profile.service';
import { NavbarComponent } from '../shared/navbar/navbar.component';

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
  actionMessage = '';
  readonly betaNotice =
    'Only display profile edits are available in this beta. Security, notification, session, and account-deletion actions are hidden or disabled until backend support is added.';

  constructor(private profileService: ProfileService) {
    this.resetToDefaults();
  }

  onSave(): void {
    this.actionMessage = '';
    this.profileService.updateProfile({
      name: this.displayName,
      role: this.displayRole,
      email: this.email,
      avatarInitials: this.avatarInitials,
    });
    this.actionMessage = 'Display profile settings updated for this browser session.';
  }

  onCancel(): void {
    this.resetToDefaults();
    this.actionMessage = '';
  }

  onDeleteAccount(): void {
    this.actionMessage = 'Account deletion is disabled until a verified backend deletion flow is available.';
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
