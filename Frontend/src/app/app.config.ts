import {
  ApplicationConfig,
  provideBrowserGlobalErrorListeners,
  provideZonelessChangeDetection,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { ProfileService } from './profile/profile.service';
import { ApiService } from './shared/api.service';
import { AuthService } from './shared/auth.service';
import { authExpiryInterceptor } from './shared/auth-expiry.interceptor';

// This app is zoneless (no zone.js). Angular does NOT auto-run change detection after
// async work (HTTP callbacks, timers, promises). After mutating view state in such a
// callback, trigger CD explicitly: read a signal in the template, use the async pipe, or
// call ChangeDetectorRef.markForCheck(). Otherwise the view only refreshes on the next
// DOM event (e.g. a click).
export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideClientHydration(withEventReplay()),
    provideHttpClient(withInterceptors([authExpiryInterceptor])),
    ProfileService,
    ApiService,
    AuthService
  ]
};
