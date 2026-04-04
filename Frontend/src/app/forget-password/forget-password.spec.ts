import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ForgetPassword } from './forget-password';

describe('ForgetPassword', () => {
  let component: ForgetPassword;
  let fixture: ComponentFixture<ForgetPassword>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ForgetPassword]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ForgetPassword);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
