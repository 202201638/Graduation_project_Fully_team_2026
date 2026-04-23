import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, NgForm, NgModel } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
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

  onSubmit(form: NgForm): void {
    const firstName = this.firstName.trim();
    const lastName = this.lastName.trim();
    const email = this.email.trim();
    this.errorMessage = '';

    if (form.invalid || this.password !== this.confirmPassword) {
      form.control.markAllAsTouched();
      return;
    }

    this.isLoading = true;

    const fullName = `${firstName} ${lastName}`.trim();

    this.authService
      .signup({
        email,
        full_name: fullName,
        password: this.password,
        role: 'doctor',
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

  shouldShowFieldError(form: NgForm, control: NgModel | null | undefined): boolean {
    return Boolean(control?.invalid && (control.touched || form.submitted));
  }

  shouldShowPasswordMismatch(form: NgForm, confirmControl: NgModel | null | undefined): boolean {
    return Boolean(
      this.password &&
        this.confirmPassword &&
        this.password !== this.confirmPassword &&
        (form.submitted || confirmControl?.touched),
    );
  }

  getRequiredFieldError(control: NgModel | null | undefined, label: string): string {
    if (control?.errors?.['required']) {
      return `${label} is required.`;
    }

    return '';
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

    if (control?.errors?.['minlength']) {
      return 'Password must be at least 8 characters.';
    }

    return '';
  }

  getConfirmPasswordError(control: NgModel | null | undefined): string {
    if (control?.errors?.['required']) {
      return 'Please confirm your password.';
    }

    return '';
  }

  clearErrorMessage(): void {
    if (this.errorMessage) {
      this.errorMessage = '';
    }
  }
}
