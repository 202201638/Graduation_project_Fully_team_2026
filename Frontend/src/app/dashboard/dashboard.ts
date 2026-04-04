import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../shared/navbar/navbar.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {
  stats = [
    {
      label: 'Cases Analyzed Today',
      value: '27',
      description: 'Total X-ray scans processed.',
      accent: 'blue',
    },
    {
      label: 'Pneumonia Positive Cases',
      value: '15%',
      description: 'Percentage of scans indicating pneumonia.',
      accent: 'amber',
    },
    {
      label: 'Average Diagnostic Accuracy',
      value: '96.2%',
      description: "AI model's average confidence score.",
      accent: 'green',
    },
  ];

  activities = [
    {
      name: 'Sophia Chen',
      timestamp: '2025-10-28, 14:30',
      diagnosis: 'Pneumonia Detected',
      confidence: '91%',
      statusLabel: 'Pneumonia Detected',
      statusVariant: 'danger',
    },
    {
      name: 'Michael Adams',
      timestamp: '2025-10-28, 11:15',
      diagnosis: 'Diagnostic: Healthy',
      confidence: '95%',
      statusLabel: 'Healthy',
      statusVariant: 'success',
    },
    {
      name: 'Emily White',
      timestamp: '2025-10-25, 08:00',
      diagnosis: 'Diagnostic: Healthy',
      confidence: '88%',
      statusLabel: 'Healthy',
      statusVariant: 'success',
    },
    {
      name: 'Daniel Lee',
      timestamp: '2025-10-25, 08:30',
      diagnosis: 'Diagnostic: Healthy',
      confidence: '98%',
      statusLabel: 'Healthy',
      statusVariant: 'success',
    },
    {
      name: 'Olivia Taylor',
      timestamp: '2025-10-24, 16:45',
      diagnosis: 'Pneumonia Detected',
      confidence: '95%',
      statusLabel: 'Pneumonia Detected',
      statusVariant: 'danger',
    },
    {
      name: 'James Brown',
      timestamp: '2025-10-24, 10:30',
      diagnosis: 'Diagnostic: Healthy',
      confidence: '97%',
      statusLabel: 'Healthy',
      statusVariant: 'success',
    },
  ];
}
