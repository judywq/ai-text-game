import { useAuthStore } from '@/stores/auth';
import Cookies from 'js-cookie';

export class EnhancedEventSource {
  private eventSource: EventSource | null = null;
  private url: string;
  private options: { withCredentials: boolean };
  private csrf_key: string;
  private API_BASE_URL: string;
  private listeners: { [key: string]: EventListener[] } = {};

  constructor(path: string) {
    this.API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
    this.url = `${this.API_BASE_URL}${path}`;
    this.options = { withCredentials: true };

    // Use the same CSRF key determination logic
    this.csrf_key = window.location.protocol === 'https:' ? '__Secure-csrftoken' : 'csrftoken';
  }

  connect() {
    // Create the URL with CSRF token as a query parameter
    const csrfToken = Cookies.get(this.csrf_key);
    const url = new URL(this.url);

    if (csrfToken) {
      url.searchParams.append('X-CSRFToken', csrfToken);
    }

    // Create the EventSource
    this.eventSource = new EventSource(url.toString(), this.options);

    // Apply previously registered event listeners
    Object.entries(this.listeners).forEach(([event, listeners]) => {
      listeners.forEach(listener => {
        this.eventSource?.addEventListener(event, listener);
      });
    });

    // Handle connection errors
    this.eventSource.onerror = (event) => {
      console.error('EventSource error:', event);

      // Check if we need to handle authentication issues
      const authStore = useAuthStore();
      if (authStore.isAuthenticated && this.eventSource?.readyState === EventSource.CLOSED) {
        // You might want to implement retry logic or auth checks here
        // Similar to your axios interceptor
      }
    };

    return this;
  }

  addEventListener(type: string, listener: EventListener) {
    // Store listener for reconnection
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(listener);

    // Add to active connection if exists
    this.eventSource?.addEventListener(type, listener);
    return this;
  }

  removeEventListener(type: string, listener: EventListener) {
    // Remove from storage
    if (this.listeners[type]) {
      this.listeners[type] = this.listeners[type].filter(l => l !== listener);
    }

    // Remove from active connection
    this.eventSource?.removeEventListener(type, listener);
    return this;
  }

  close() {
    this.eventSource?.close();
    this.eventSource = null;
    return this;
  }
}

// Usage example:
// const eventSource = new EnhancedEventSource('/api/events').connect();
// eventSource.addEventListener('message', (event) => console.log(event.data));
