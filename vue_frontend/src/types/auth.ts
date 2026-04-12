import type { NativeLanguageCode } from '@/constants/nativeLanguage'

export interface User {
  pk: number;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  must_change_password: boolean;
  /** Present after backend supports it; may be missing in older cached auth state. */
  native_language?: NativeLanguageCode | null;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}
