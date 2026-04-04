import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';

interface IntroSlide {
  icon: string;
  title: string;
  subtitle: string;
}

@Component({
  selector: 'app-intro',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './intro.html',
  styleUrl: './intro.css',
})
export class Intro implements OnInit {
  slides: IntroSlide[] = [
    {
      icon: '🏥',
      title: 'Welcome to Mediscan AI',
      subtitle: 'Your smart assistant for faster, more confident chest X-ray diagnosis.',
    },
    {
      icon: '⚡',
      title: 'Fast AI Analysis',
      subtitle: 'Upload chest X-rays and receive AI-supported pneumonia scores in seconds.',
    },
    {
      icon: '🎯',
      title: 'High-Accuracy Insights',
      subtitle: 'See confidence scores and visual heatmaps that highlight suspicious regions.',
    },
    {
      icon: '📁',
      title: 'Smart Patient Records',
      subtitle: 'Keep scans, AI results, and patient history together in a clean, secure dashboard.',
    },
    {
      icon: '🤝',
      title: 'Built for Doctors',
      subtitle: 'Designed to support your clinical judgement, not replace it.',
    },
    {
      icon: '🔐',
      title: 'Secure & Private',
      subtitle: 'Data is handled with care and can be anonymized for safer collaboration.',
    },
  ];

  currentIndex = 0;
  private readonly storageKey = 'mediscan_intro_completed';

  constructor(private router: Router) {}

  ngOnInit(): void {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const completed = window.localStorage.getItem(this.storageKey);
        const url = this.router.url || '/';
        const isRoot = url === '/' || url === '';

        // Only auto-skip when user lands on the root path and has already seen the intro.
        if (completed === 'true' && isRoot) {
          this.router.navigateByUrl('/welcome');
        }
      }
    } catch {
      // Ignore storage errors and show intro normally
    }
  }

  get isLastStep(): boolean {
    return this.currentIndex === this.slides.length - 1;
  }

  next(): void {
    if (!this.isLastStep) {
      this.currentIndex++;
      return;
    }

    this.finish();
  }

  skip(): void {
    this.finish();
  }

  selectStep(index: number): void {
    if (index < 0 || index >= this.slides.length) {
      return;
    }
    this.currentIndex = index;
  }

  private finish(): void {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(this.storageKey, 'true');
      }
    } catch {
      // Ignore storage errors
    }

    this.router.navigateByUrl('/welcome');
  }
}
