import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AnalysisResult, AnalysisStateService } from '../analysis-state.service';
import { ProfileService } from './profile.service';
import { NavbarComponent } from '../shared/navbar/navbar.component';

interface ProfileStat {
  label: string;
  value: string;
  description: string;
}

interface ActivityItem {
  title: string;
  time: string;
}

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, NavbarComponent],
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})
export class Profile implements OnInit, OnDestroy {
  name = '';
  role = '';
  email = '';
  avatarInitials = '';
  activity: ActivityItem[] = [];
  stats: ProfileStat[] = this.buildStats([]);
  private readonly subscriptions = new Subscription();

  // Editing properties
  isEditing = false;
  editName = '';
  editRole = '';
  editEmail = '';
  editInitials = '';

  clinic = {
    name: '',
    address: '',
    phone: '',
  };

  constructor(
    private profileService: ProfileService,
    private analysisState: AnalysisStateService,
  ) {
    const profile = this.profileService.profile;
    this.name = profile.name;
    this.role = profile.role;
    this.email = profile.email;
    this.avatarInitials = profile.avatarInitials;

    // Initialize edit fields with current values
    this.editName = this.name;
    this.editRole = this.role;
    this.editEmail = this.email;
    this.editInitials = this.avatarInitials;
  }

  ngOnInit(): void {
    this.subscriptions.add(
      this.analysisState.history$.subscribe((history) => {
        this.stats = this.buildStats(history);
        this.activity = history.slice(0, 6).map((item) => ({
          title: `${item.diagnosis} for patient ${item.patientId || 'Unknown'}`,
          time: this.formatTime(item.date),
        }));
      }),
    );

    this.analysisState.loadAuthenticatedHistory();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  toggleEditMode() {
    if (this.isEditing) {
      this.saveProfile();
    } else {
      this.startEdit();
    }
  }

  startEdit() {
    this.isEditing = true;
    this.editName = this.name;
    this.editRole = this.role;
    this.editEmail = this.email;
    this.editInitials = this.avatarInitials;
  }

  cancelEdit() {
    this.isEditing = false;
    this.editName = '';
    this.editRole = '';
    this.editEmail = '';
    this.editInitials = '';
  }

  saveProfile() {
    if (this.editName.trim()) {
      this.name = this.editName.trim();
    }
    if (this.editRole.trim()) {
      this.role = this.editRole.trim();
    }
    if (this.editEmail.trim()) {
      this.email = this.editEmail.trim();
    }
    if (this.editInitials.trim()) {
      this.avatarInitials = this.editInitials.trim().substring(0, 3);
    }

    // Update the profile service
    this.profileService.updateProfile({
      name: this.name,
      role: this.role,
      email: this.email,
      avatarInitials: this.avatarInitials,
    });

    this.isEditing = false;
  }

  private buildStats(history: AnalysisResult[]): ProfileStat[] {
    const positiveCount = history.filter(
      (item) => item.statusVariant === 'danger' || item.statusVariant === 'warning',
    ).length;
    const averageConfidence = history.length
      ? Math.round(
          history.reduce((total, item) => total + item.confidence, 0) / history.length,
        )
      : 0;

    return [
      {
        label: 'Saved Analyses',
        value: String(history.length),
        description: 'Authenticated X-ray analyses saved to your account.',
      },
      {
        label: 'Flagged Cases',
        value: String(positiveCount),
        description: 'Saved cases marked as suspected or detected pneumonia.',
      },
      {
        label: 'Average Confidence',
        value: history.length ? `${averageConfidence}%` : 'N/A',
        description: 'Average confidence across your saved analyses.',
      },
    ];
  }

  private formatTime(dateValue: string): string {
    const date = new Date(dateValue);
    if (Number.isNaN(date.getTime())) {
      return dateValue;
    }

    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }
}
