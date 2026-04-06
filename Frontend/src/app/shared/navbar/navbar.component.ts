import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../auth.service';
import { ProfileService } from '../../profile/profile.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent {
  constructor(
    private router: Router,
    private authService: AuthService,
    private profileService: ProfileService,
  ) {}

  isActive(route: string): boolean {
    return this.router.url === route;
  }

  get displayName(): string {
    return this.profileService.profile.name;
  }

  get avatarInitials(): string {
    return this.profileService.profile.avatarInitials;
  }

  get isAuthenticated(): boolean {
    return this.authService.isAuthenticated();
  }
}
