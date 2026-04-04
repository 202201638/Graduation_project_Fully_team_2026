import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../shared/navbar/navbar.component';

interface DoctorRow {
  id: string;
  name: string;
  email: string;
  role: string;
  status: 'active' | 'inactive' | 'suspended';
}

@Component({
  selector: 'app-admin-panel',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, NavbarComponent],
  templateUrl: './admin-panel.html',
  styleUrl: './admin-panel.css',
})
export class AdminPanel implements OnInit {
  search = '';
  statusFilter = 'all'; // all | active | inactive | suspended

  activeTab: 'doctors' | 'stats' | 'config' | 'audit' = 'doctors';

  newDoctorName = '';
  newDoctorEmail = '';
  newDoctorRole = 'Doctor';
  newDoctorStatus: 'active' | 'inactive' | 'suspended' = 'active';

  systemStats = [
    { label: 'Total scans processed', value: 1284, description: 'All-time scans analyzed by MediScan AI.' },
    { label: 'Scans in last 24 hours', value: 42, description: 'Recent workload across all doctors.' },
    { label: 'Active doctors', value: 18, description: 'Doctors with activity in the last 7 days.' },
    { label: 'System health', value: 'Operational', description: 'All services are running normally.' },
  ];

  maintenanceMode = false;
  autoUpdates = true;
  errorTracking = true;

  auditLogs = [
    {
      timestamp: '2025-10-28 09:15',
      actor: 'Dr. Alice Smith',
      action: 'Updated system configuration',
      status: 'Success',
    },
    {
      timestamp: '2025-10-27 16:42',
      actor: 'Dr. Bob Johnson',
      action: 'Created new doctor account',
      status: 'Success',
    },
    {
      timestamp: '2025-10-26 11:03',
      actor: 'System',
      action: 'Applied security patch 1.2.3',
      status: 'Success',
    },
    {
      timestamp: '2025-10-25 08:30',
      actor: 'Dr. Carol White',
      action: 'Attempted role change without permission',
      status: 'Denied',
    },
  ];

  doctors: DoctorRow[] = [
    {
      id: 'D001',
      name: 'Dr. Alice Smith',
      email: 'alice.smith@mediscan.com',
      role: 'Admin',
      status: 'active',
    },
    {
      id: 'D002',
      name: 'Dr. Bob Johnson',
      email: 'bob.j@mediscan.com',
      role: 'Doctor',
      status: 'active',
    },
    {
      id: 'D003',
      name: 'Dr. Carol White',
      email: 'carol.w@mediscan.com',
      role: 'Doctor',
      status: 'inactive',
    },
    {
      id: 'D004',
      name: 'Dr. David Green',
      email: 'david.g@mediscan.com',
      role: 'Doctor',
      status: 'active',
    },
    {
      id: 'D005',
      name: 'Dr. Emily Brown',
      email: 'emily.b@mediscan.com',
      role: 'Doctor',
      status: 'active',
    },
  ];

  filtered: DoctorRow[] = [];

  ngOnInit() {
    this.applyFilters();
  }

  setTab(tab: 'doctors' | 'stats' | 'config' | 'audit') {
    this.activeTab = tab;
  }

  get activeTabTitle(): string {
    switch (this.activeTab) {
      case 'stats':
        return 'System Statistics';
      case 'config':
        return 'Configuration & Updates';
      case 'audit':
        return 'Audit Logs';
      default:
        return 'Doctor Accounts';
    }
  }

  getStatusLabel(row: DoctorRow): string {
    if (row.status === 'active') return 'Active';
    if (row.status === 'inactive') return 'Disabled';
    return 'Suspended';
  }

  applyFilters() {
    const searchLower = this.search.trim().toLowerCase();

    this.filtered = this.doctors.filter((d) => {
      const matchesSearch =
        !searchLower ||
        d.name.toLowerCase().includes(searchLower) ||
        d.email.toLowerCase().includes(searchLower);

      const matchesStatus =
        this.statusFilter === 'all' ? true : d.status === (this.statusFilter as any);

      return matchesSearch && matchesStatus;
    });
  }

  onSearchChange() {
    this.applyFilters();
  }

  onStatusChange() {
    this.applyFilters();
  }

  addDoctor() {
    const name = this.newDoctorName.trim();
    const email = this.newDoctorEmail.trim();

    if (!name || !email) {
      return;
    }

    const index = this.doctors.length + 1;
    const newDoctor: DoctorRow = {
      id: `D${index.toString().padStart(3, '0')}`,
      name,
      email,
      role: this.newDoctorRole,
      status: this.newDoctorStatus,
    };
    this.doctors = [...this.doctors, newDoctor];
    this.newDoctorName = '';
    this.newDoctorEmail = '';
    this.newDoctorRole = 'Doctor';
    this.newDoctorStatus = 'active';
    this.applyFilters();
  }

  toggleStatus(row: DoctorRow) {
    const nextStatus = row.status === 'active' ? 'inactive' : 'active';
    this.doctors = this.doctors.map((d) =>
      d.id === row.id ? { ...d, status: nextStatus } : d,
    );
    this.applyFilters();
  }

  removeDoctor(row: DoctorRow) {
    this.doctors = this.doctors.filter((d) => d.id !== row.id);
    this.applyFilters();
  }
}
