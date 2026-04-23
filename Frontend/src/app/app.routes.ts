import { Routes } from '@angular/router';
import { Welcome } from './welcome/welcome';
import { Intro } from './intro/intro';
import { Login } from './login/login';
import { Signup } from './signup/signup';
import { ForgetPassword } from './forget-password/forget-password';
import { Dashboard } from './dashboard/dashboard';
import { Upload } from './upload/upload';
import { Processing } from './processing/processing';
import { Result } from './result/result';
import { PatientRecords } from './patient-records/patient-records';
import { AdminPanel } from './admin-panel/admin-panel';
import { Settings } from './settings/settings';
import { Profile } from './profile/profile';
import { Logout } from './logout/logout';
import { authGuard } from './auth.guard';
import { guestGuard } from './guest.guard';

export const routes: Routes = [
  { path: '', component: Intro },
  { path: 'intro', component: Intro },
  { path: 'welcome', component: Welcome },
  { path: 'login', component: Login, canActivate: [guestGuard] },
  { path: 'Login', redirectTo: 'login', pathMatch: 'full' },
  { path: 'signup', component: Signup, canActivate: [guestGuard] },
  { path: 'forget-password', component: ForgetPassword, canActivate: [guestGuard] },
  { path: 'logout', component: Logout },
  { path: 'dashboard', component: Dashboard, canActivate: [authGuard] },
  { path: 'upload', component: Upload, canActivate: [authGuard] },
  { path: 'processing', component: Processing, canActivate: [authGuard] },
  { path: 'result/:analysisId', component: Result, canActivate: [authGuard] },
  { path: 'result', component: Result, canActivate: [authGuard] },
  { path: 'records', component: PatientRecords, canActivate: [authGuard] },
  { path: 'admin', component: AdminPanel, canActivate: [authGuard] },
  { path: 'settings', component: Settings, canActivate: [authGuard] },
  { path: 'profile', component: Profile, canActivate: [authGuard] },
];
