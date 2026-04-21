import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, NgForm, NgModel } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';

import { AuthService } from '../shared/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [RouterModule, CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  email = '';
  password = '';
  isLoading = false;
  errorMessage = '';

  constructor(
    private router: Router,
    private authService: AuthService,
  ) {}

  onSubmit(form: NgForm): void {
    this.errorMessage = '';

    if (form.invalid) {
      form.control.markAllAsTouched();
      return;
    }

    this.isLoading = true;

    this.authService
      .login({
        email: this.email,
        password: this.password,
      })
      .subscribe({
        next: (response) => {
          this.authService.setSession(response.access_token, response.user);
          this.router.navigate(['/dashboard']);
          this.isLoading = false;
        },
        error: (error) => {
          this.errorMessage = error?.error?.detail || 'Invalid email or password';
          this.isLoading = false;
          console.error('Login error:', error);
        },
      });
  }

  shouldShowFieldError(form: NgForm, control: NgModel | null | undefined): boolean {
    return Boolean(control?.invalid && (control.touched || form.submitted));
  }

  getEmailError(control: NgModel | null | undefined): string {
    if (control?.errors?.['required']) {
      return 'Email is required.';
    }

    if (control?.errors?.['email']) {
      return 'Please enter a valid email address.';
    }

    return '';
  }

  getPasswordError(control: NgModel | null | undefined): string {
    if (control?.errors?.['required']) {
      return 'Password is required.';
    }

    return '';
  }

  clearErrorMessage(): void {
    if (this.errorMessage) {
      this.errorMessage = '';
    }
  }
}
