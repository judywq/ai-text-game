export interface User {
  pk: number;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}
