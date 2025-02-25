import { defineStore } from 'pinia';
import type { Router } from 'vue-router';
import { AuthService } from '@/services/authService';
import type { AuthState } from '@/types/auth';

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    token: null,
  }),

  getters: {
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null,
    currentUser: (state) => state.user,
    isLoading: (state) => state.loading,
    hasError: (state) => state.error !== null
  },

  actions: {
    setLoading(loading: boolean) {
      this.loading = loading;
    },

    setError(error: string | null) {
      this.error = error;
    },

    async login(email: string, password: string, router: Router | null = null) {
      this.setLoading(true);
      this.setError(null);

      try {
        const response = await AuthService.login(email, password);
        this.user = response.user;
        this.token = response.key;
        this.isAuthenticated = true;
        this.saveState();

        if (router) {
          await router.push({ name: "home" });
        }
      } catch (error: any) {
        this.isAuthenticated = false;
        this.user = null;
        this.setError(error.message || 'Login failed');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async logout(router: Router | null = null) {
      this.setLoading(true);
      this.setError(null);

      try {
        await AuthService.logout();
        this.clearState();

        if (router) {
          await router.push({ name: "login" });
        }
      } catch (error: any) {
        // Even if logout fails on server, clear local state
        this.clearState();
        this.setError(error.message || 'Logout failed');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async signup(email: string, password: string, router?: Router) {
      this.setLoading(true);
      this.setError(null);

      try {
        await AuthService.signup(email, password);
        if (router) {
          await router.push({ name: "verify-email" });
        }
      } catch (error: any) {
        this.setError(error.message || 'Registration failed');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async verifyEmail(key: string, router?: Router) {
      this.setLoading(true);
      this.setError(null);

      try {
        const response = await AuthService.verifyEmail(key);
        if (response?.status === 200) {
          if (router) {
            await router.push({ name: "login" });
          }
        }
        return response;
      } catch (error: any) {
        this.setError(error.message || 'Email verification failed');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async fetchUser() {
      this.setLoading(true);
      this.setError(null);

      try {
        const user = await AuthService.fetchUser();
        this.user = user;
        this.isAuthenticated = true;
        this.saveState();

        // Get token from localStorage or cookie if needed
        const token = localStorage.getItem('auth_token');
        this.token = token;
      } catch (error: any) {
        this.clearState();
        this.setError(error.message || 'Failed to fetch user data');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    saveState() {
      localStorage.setItem('authState', JSON.stringify({
        user: this.user,
        isAuthenticated: this.isAuthenticated,
        loading: false,
        error: null,
        token: this.token
      }));
    },

    clearState() {
      this.user = null;
      this.isAuthenticated = false;
      this.error = null;
      this.token = null;
      localStorage.removeItem('authState');
    },

    // Initialize store - call this when app starts
    async initialize() {
      if (this.isAuthenticated) {
        try {
          await this.fetchUser();
        } catch (error) {
          // If fetching user fails, clear the state
          this.clearState();
        }
      }
    }
  }
});
