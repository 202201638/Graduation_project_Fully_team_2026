import { Component, OnInit } from '@angular/core';
import { AuthService } from '../shared/auth.service';

@Component({
  selector: 'app-logout',
  standalone: true,
  template: '',
})
export class Logout implements OnInit {
  constructor(
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    this.authService.logout();
  }
}
