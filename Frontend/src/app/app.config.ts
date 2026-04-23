import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { ProfileService } from './profile/profile.service';
import { ApiService } from './shared/api.service';
import { AuthService } from './shared/auth.service';
import { authExpiryInterceptor } from './shared/auth-expiry.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes), 
    provideClientHydration(withEventReplay()),
    provideHttpClient(withInterceptors([authExpiryInterceptor])),
    ProfileService,
    ApiService,
    AuthService
  ]
};
