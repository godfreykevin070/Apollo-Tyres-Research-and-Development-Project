export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'manager' | 'engineer';
  created_at: string;
  last_login?: string;
  project_count?: number;
}

export interface Project {
  id: number;
  project_name: string;
  region: string;
  department: string;
  tyre_size: string;
  protocol: string;
  status: 'Not Started' | 'In Progress' | 'Completed' | 'Archived';
  created_at: string;
  completed_at?: string;
  user_email: string;
  user_name?: string;
  inputs?: Record<string, any>;
}

export interface ActivityLog {
  id: number;
  user_email: string;
  user_name: string;
  activity_type: string;
  action: string;
  description: string;
  status: 'success' | 'failed' | 'warning';
  ip_address?: string;
  browser?: string;
  device_type?: string;
  project_name?: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  token: string;
  user: User;
  message?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
}