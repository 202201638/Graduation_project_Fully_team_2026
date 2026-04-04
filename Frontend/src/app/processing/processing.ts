import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { AnalysisStateService } from '../analysis-state.service';

@Component({
  selector: 'app-processing',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './processing.html',
  styleUrl: './processing.css',
})
export class Processing implements OnInit {
  constructor(
    private router: Router,
    private analysisState: AnalysisStateService,
  ) {}

  ngOnInit() {
    const result = this.analysisState.getResult();
    if (!result) {
      this.router.navigate(['/upload']);
      return;
    }

    setTimeout(() => {
      this.router.navigate(['/result']);
    }, 2000);
  }
}
