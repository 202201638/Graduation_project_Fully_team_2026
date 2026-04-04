import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
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
export class Profile {
  name = '';
  role = '';
  email = '';
  avatarInitials = '';

  // Editing properties
  isEditing = false;
  editName = '';
  editRole = '';
  editEmail = '';
  editInitials = '';

  clinic = {
    name: 'Mediscan Diagnostics Center',
    address: '123 Health Ave, Medical City, MC 10001',
    phone: '(555) 123-4567',
  };

  stats: ProfileStat[] = [
    {
      label: 'Cases Analyzed',
      value: '4,567',
      description: 'Total X-ray cases you have reviewed.',
    },
    {
      label: 'Positive Cases Identified',
      value: '1,234',
      description: 'Cases flagged with potential issues.',
    },
    {
      label: 'Accuracy Rate',
      value: '98.5%',
      description: 'Average diagnostic accuracy over the last 30 days.',
    },
  ];

  activity: ActivityItem[] = [
    {
      title: 'Analyzed X-ray for Patient ID 7830',
      time: '2 hours ago',
    },
    {
      title: 'Updated personal contact details',
      time: 'Yesterday',
    },
    {
      title: 'Reviewed patient history for ID 1234',
      time: '2 days ago',
    },
    {
      title: 'Completed AI model training session',
      time: '3 days ago',
    },
    {
      title: 'Added new patient record for ID 5678',
      time: '1 week ago',
    },
    {
      title: 'Consulted on complex case with Dr. Emily White',
      time: '1 week ago',
    },
  ];

  constructor(private profileService: ProfileService) {
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
      avatarInitials: this.avatarInitials
    });

    this.isEditing = false;
    console.log('Profile saved:', {
      name: this.name,
      role: this.role,
      email: this.email,
      avatarInitials: this.avatarInitials
    });
  }
}
