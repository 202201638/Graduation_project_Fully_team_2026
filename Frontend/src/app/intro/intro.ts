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
      icon: 'CL',
      title: 'Welcome to Mediscan AI',
      subtitle: 'Your smart assistant for faster, more confident chest X-ray diagnosis.',
    },
    {
      icon: 'AI',
      title: 'Fast AI Analysis',
      subtitle: 'Upload chest X-rays and receive AI-supported pneumonia scores in seconds.',
    },
    {
      icon: 'ROI',
      title: 'Detection Insights',
      subtitle: 'See confidence scores and localization boxes when the selected model supports detection.',
    },
    {
      icon: 'EHR',
      title: 'Smart Patient Records',
      subtitle: 'Keep scans, AI results, and patient history together in a clean, secure dashboard.',
    },
    {
      icon: 'DR',
      title: 'Built for Doctors',
      subtitle: 'Designed to support your clinical judgement, not replace it.',
    },
    {
      icon: 'SEC',
      title: 'Secure & Private',
      subtitle: 'Use authenticated history and keep each doctor account scoped to its own patients.',
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
      // Ignore storage errors and show intro normally.
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
      // Ignore storage errors.
    }

    this.router.navigateByUrl('/welcome');
  }
}
