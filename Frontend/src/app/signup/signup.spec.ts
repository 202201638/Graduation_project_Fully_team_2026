import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AuthService } from '../shared/auth.service';
import { Signup } from './signup';

describe('Signup', () => {
  let component: Signup;
  let fixture: ComponentFixture<Signup>;
  let authService: {
    signup: ReturnType<typeof vi.fn>;
    login: ReturnType<typeof vi.fn>;
    setSession: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    authService = {
      signup: vi.fn(() => of({})),
      login: vi.fn(() => of({ access_token: 'token', user: null })),
      setSession: vi.fn(() => undefined),
    };

    await TestBed.configureTestingModule({
      imports: [Signup],
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: authService,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Signup);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('shows required signup errors immediately after submit', async () => {
    const form: HTMLFormElement = fixture.nativeElement.querySelector('form');
    form.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('First name is required.');
    expect(text).toContain('Last name is required.');
    expect(text).toContain('Email is required.');
    expect(text).toContain('Password is required.');
    expect(text).toContain('Please confirm your password.');
    expect(authService.signup).not.toHaveBeenCalled();
  });

  it('shows password mismatch immediately after submit', async () => {
    const firstNameInput: HTMLInputElement = fixture.nativeElement.querySelector('#signup-first-name');
    const lastNameInput: HTMLInputElement = fixture.nativeElement.querySelector('#signup-last-name');
    const emailInput: HTMLInputElement = fixture.nativeElement.querySelector('#signup-email');
    const passwordInput: HTMLInputElement = fixture.nativeElement.querySelector('#signup-password');
    const confirmPasswordInput: HTMLInputElement = fixture.nativeElement.querySelector('#signup-confirm');

    firstNameInput.value = 'John';
    firstNameInput.dispatchEvent(new Event('input'));
    lastNameInput.value = 'Doe';
    lastNameInput.dispatchEvent(new Event('input'));
    emailInput.value = 'john@example.com';
    emailInput.dispatchEvent(new Event('input'));
    passwordInput.value = 'password123';
    passwordInput.dispatchEvent(new Event('input'));
    confirmPasswordInput.value = 'password456';
    confirmPasswordInput.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    await fixture.whenStable();

    const form: HTMLFormElement = fixture.nativeElement.querySelector('form');
    form.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('Passwords do not match.');
    expect(authService.signup).not.toHaveBeenCalled();
  });
});
