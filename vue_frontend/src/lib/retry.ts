// src/utils/retry.ts

interface RetryConfig {
  retries?: number;
  delay?: number;
  maxDelay?: number;
  backoff?: boolean;
  shouldRetry?: (error: any) => boolean;
  onRetry?: (error: any, attempt: number) => void;
}

const defaultConfig: Required<RetryConfig> = {
  retries: 3,
  delay: 1000,
  maxDelay: 5000,
  backoff: true,
  shouldRetry: (error) => {
    // Don't retry on client errors (4xx)
    if (error.response?.status >= 400 && error.response?.status < 500) {
      return false;
    }
    // Retry on network errors or server errors (5xx)
    return !error.response || error.response.status >= 500;
  },
  onRetry: () => {}
};

const calculateDelay = (attempt: number, config: Required<RetryConfig>): number => {
  if (!config.backoff) {
    return config.delay;
  }
  const exponentialDelay = config.delay * Math.pow(2, attempt - 1);
  return Math.min(exponentialDelay, config.maxDelay);
};

const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

export async function retry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = {}
): Promise<T> {
  const finalConfig = { ...defaultConfig, ...config };
  let lastError: any;

  for (let attempt = 1; attempt <= finalConfig.retries + 1; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      lastError = error;

      // If it's the last attempt or we shouldn't retry, throw the error
      if (attempt > finalConfig.retries || !finalConfig.shouldRetry(error)) {
        throw error;
      }

      // Call onRetry callback
      finalConfig.onRetry(error, attempt);

      // Wait before next retry
      await sleep(calculateDelay(attempt, finalConfig));
    }
  }

  throw lastError;
}

// Modified retry strategies
export const retryStrategies = {
  networkErrors: {
    shouldRetry: (error: any) => {
      return error.isAxiosError && !error.response;
    }
  },

  serverErrors: {
    shouldRetry: (error: any) => {
      // Only retry on 5xx errors
      return error.response && error.response.status >= 500 && error.response.status < 600;
    }
  },

  statusCodes: (codes: number[]) => ({
    shouldRetry: (error: any) => {
      return error.response && codes.includes(error.response.status);
    }
  })
};

// Example of proper usage with Axios interceptors
/*
import axios from 'axios';

const api = axios.create({
  // your config
});

api.interceptors.response.use(
  response => response,
  async error => {
    const config = error.config;

    // Prevent infinite loops by checking if request was already retried
    if (config && !config.__isRetry) {
      config.__isRetry = true;
      try {
        return await retry(() => api(config));
      } catch (retryError) {
        // If retry fails, throw the error
        throw retryError;
      }
    }

    // If request was already retried or shouldn't be retried, throw the error
    throw error;
  }
);
*/
