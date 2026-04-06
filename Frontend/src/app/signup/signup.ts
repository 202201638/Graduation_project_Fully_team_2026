import { Component } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { switchMap } from 'rxjs';
import { AuthService } from '../shared/auth.service';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [RouterModule, CommonModule, FormsModule],
  templateUrl: './signup.html',
  styleUrl: './signup.css',
})
export class Signup {
  firstName = '';
  lastName = '';
  email = '';
  hospital = '';
  password = '';
  confirmPassword = '';
  isLoading = false;
  errorMessage = '';

  constructor(
    private router: Router,
    private authService: AuthService,
  ) {}

  onSubmit(event: Event) {
    event.preventDefault();

    const firstName = this.firstName.trim();
    const lastName = this.lastName.trim();
    const email = this.email.trim();

    if (!firstName || !lastName || !email || !this.password || !this.confirmPassword) {
      this.errorMessage = 'Please fill in all required fields.';
      return;
    }

    if (this.password.length < 8) {
      this.errorMessage = 'Password must be at least 8 characters.';
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    const fullName = `${firstName} ${lastName}`.trim();

    this.authService
      .signup({
        email,
        full_name: fullName,
        password: this.password,
        role: 'patient',
      })
      .pipe(
        switchMap(() =>
          this.authService.login({
            email,
            password: this.password,
          }),
        ),
      )
      .subscribe({
        next: (response) => {
          this.authService.setSession(response.access_token, response.user);
          this.router.navigate(['/dashboard']);
          this.isLoading = false;
        },
        error: (error) => {
          this.errorMessage = error?.error?.detail || 'Unable to create your account.';
          this.isLoading = false;
          console.error('Signup error:', error);
        },
      });
  }
}
