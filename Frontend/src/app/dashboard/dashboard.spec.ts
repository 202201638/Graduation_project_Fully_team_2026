import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { AnalysisStateService } from '../analysis-state.service';
import { AuthService } from '../shared/auth.service';
import { ProfileService } from '../profile/profile.service';
import { Dashboard } from './dashboard';

describe('Dashboard', () => {
  let component: Dashboard;
  let fixture: ComponentFixture<Dashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Dashboard],
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: {
            isAuthenticated: () => false,
          },
        },
        {
          provide: AnalysisStateService,
          useValue: {
            history$: of([]),
            loadAuthenticatedHistory: () => undefined,
          },
        },
        {
          provide: ProfileService,
          useValue: {
            profile: {
              name: 'Guest User',
              avatarInitials: 'GU',
            },
          },
        },
      ],
    })
    .compileComponents();

    fixture = TestBed.createComponent(Dashboard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
