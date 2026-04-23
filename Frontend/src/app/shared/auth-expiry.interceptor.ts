import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

const TOKEN_STORAGE_KEY = 'auth_token';

export const authExpiryInterceptor: HttpInterceptorFn = (req, next) =>
  next(req).pipe(
    catchError((error: unknown) => {
      if (
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        req.headers.has('Authorization') &&
        typeof window !== 'undefined' &&
        window.localStorage
      ) {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);

        if (!window.location.pathname.includes('/login')) {
          window.location.assign('/login');
        }
      }

      return throwError(() => error);
    }),
  );
