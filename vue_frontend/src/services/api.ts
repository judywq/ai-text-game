import axios from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import Cookies from 'js-cookie';
import { retry } from '@/lib/retry';
import { useAuthStore } from '@/stores/auth';
import router from '@/router';
import { AxiosError } from 'axios';

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL;
console.debug('api.ts initialization - API_BASE_URL:', { API_BASE_URL });

let csrf_key = 'csrftoken';
if (window.location.protocol === 'https:') {
  // If https, set csrf_key to '__Secure-csrftoken'
  csrf_key = '__Secure-csrftoken';
}

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      if (config.headers) {
        config.headers['Authorization'] = `Token ${token}`;
      }
    }
    // Keep existing CSRF token logic
    const csrfToken = Cookies.get(csrf_key);
    if (csrfToken && config.headers) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error: any) => Promise.reject(error)
);

interface ApiFieldError {
  [key: string]: string[];
}

export interface ApiErrorResponse {
  non_field_errors?: string[];
  [key: string]: any;
}

export interface ApiError {
  message: string;
  code: string;
  fieldErrors?: Record<string, string>;
  nonFieldError?: string;
}

function handleApiError(error: AxiosError<ApiErrorResponse>): ApiError {
  if (error.response) {
    const { data } = error.response;
    const fieldErrors: Record<string, string> = {};
    let nonFieldError: string | undefined;

    // Handle non-field errors
    if (data.non_field_errors?.length) {
      nonFieldError = data.non_field_errors[0];
    }

    const nonFieldErrorKeys = [
      'non_field_errors',
      'detail',
      'error'
    ]

    // Handle field-specific errors
    Object.entries(data).forEach(([key, value]) => {
      if (nonFieldErrorKeys.includes(key)) {
        if (Array.isArray(value)) {
          nonFieldError = value[0];
        } else {
          nonFieldError = value;
        }
      }
      else {
        if (Array.isArray(value)) {
          fieldErrors[key] = value[0];
        } else {
          fieldErrors[key] = value;
        }
      }
    });

    return {
      message: nonFieldError || 'An error occurred',
      code: error.response.status.toString(),
      fieldErrors: Object.keys(fieldErrors).length > 0 ? fieldErrors : undefined,
      nonFieldError
    };
  }

  if (error.request) {
    return {
      message: 'No response from server',
      code: 'NETWORK_ERROR',
      nonFieldError: 'Network error. Please try again.'
    };
  }

  return {
    message: error.message || 'An unexpected error occurred',
    code: 'REQUEST_ERROR',
    nonFieldError: 'An unexpected error occurred. Please try again.'
  };
}

api.interceptors.response.use(
  response => response,
  async error => {
    const config = error.config;

    if (error.response && error.response.status === 403) {
      const { detail } = error.response.data;
      // If the error is due to missing credentials, log the user out
      // The server will return a 403 status code with a detail message
      //  like "Authentication credentials were not provided."
      if (detail && detail.includes('credentials')) {
        const authStore = useAuthStore();
        await authStore.logout();
        router.push({ name: 'login' });
      }
    }

    throw handleApiError(error);
  }
);

export default api;
