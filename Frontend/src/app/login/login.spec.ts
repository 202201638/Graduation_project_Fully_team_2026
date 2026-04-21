import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { AuthService } from '../shared/auth.service';
import { Login } from './login';

describe('Login', () => {
  let component: Login;
  let fixture: ComponentFixture<Login>;
  let authService: {
    login: ReturnType<typeof vi.fn>;
    setSession: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    authService = {
      login: vi.fn(() => of({ access_token: 'token', user: null })),
      setSession: vi.fn(() => undefined),
    };

    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: authService,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('shows required field errors immediately after submit', async () => {
    const form: HTMLFormElement = fixture.nativeElement.querySelector('form');
    form.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Email is required.');
    expect(text).toContain('Password is required.');
    expect(authService.login).not.toHaveBeenCalled();
  });

  it('shows backend login errors immediately after submit', async () => {
    authService.login.mockReturnValue(
      throwError(() => ({ error: { detail: 'Invalid email or password' } })),
    );

    const emailInput: HTMLInputElement = fixture.nativeElement.querySelector('#login-email');
    const passwordInput: HTMLInputElement = fixture.nativeElement.querySelector('#login-password');
    emailInput.value = 'test@example.com';
    emailInput.dispatchEvent(new Event('input'));
    passwordInput.value = 'wrong-password';
    passwordInput.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    await fixture.whenStable();

    const form: HTMLFormElement = fixture.nativeElement.querySelector('form');
    form.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('Invalid email or password');
  });
});
