import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { AnalysisStateService } from '../analysis-state.service';
import { ProfileService } from '../profile/profile.service';
import { ApiService } from '../shared/api.service';
import { AuthService } from '../shared/auth.service';
import { Upload } from './upload';

describe('Upload', () => {
  let component: Upload;
  let fixture: ComponentFixture<Upload>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Upload],
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: {
            isAuthenticated: () => false,
            getCurrentToken: () => null,
          },
        },
        {
          provide: ProfileService,
          useValue: {
            profile: {
              avatarInitials: 'GU',
            },
          },
        },
        {
          provide: AnalysisStateService,
          useValue: {
            metadata$: of(null),
            history$: of([]),
            getDraft: () => null,
            getMetadata: () => null,
            loadMetadata: () => undefined,
            loadAuthenticatedHistory: () => undefined,
            getHistory: () => [],
            resetProcessState: () => undefined,
            startAnalysis: () => undefined,
          },
        },
        {
          provide: ApiService,
          useValue: {
            getPatients: () => of([]),
            createPatient: () => of({}),
          },
        },
      ],
    })
    .compileComponents();

    fixture = TestBed.createComponent(Upload);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
