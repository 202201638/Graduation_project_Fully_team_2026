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


export const routes: Routes = [
  { path: '', component: Intro },
  { path: 'intro', component: Intro },
  { path: 'welcome', component: Welcome },
  { path: 'login', component: Login },
  { path: 'Login', redirectTo: 'login', pathMatch: 'full' },
  { path: 'dashboard', component: Dashboard },
  { path: 'upload', component: Upload },
  { path: 'processing', component: Processing },
  { path: 'result', component: Result },
  { path: 'records', component: PatientRecords },
  { path: 'admin', component: AdminPanel },
  { path: 'settings', component: Settings },
  { path: 'profile', component: Profile },
  { path: 'signup', component: Signup },
  { path: 'forget-password', component: ForgetPassword },
];