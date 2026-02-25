/**
 * API retry utility with exponential backoff
 * Automatically retries failed requests with increasing delays
 */

export interface RetryConfig {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  retryableStatuses?: number[];
}

const DEFAULT_CONFIG: Required<RetryConfig> = {
  maxRetries: 3,
  initialDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffMultiplier: 2,
  retryableStatuses: [408, 429, 500, 502, 503, 504], // Timeout, Rate limit, Server errors
};

/**
 * Sleep for a specified duration
 */
const sleep = (ms: number): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));

/**
 * Calculate delay with exponential backoff and jitter
 */
const calculateDelay = (
  attempt: number,
  initialDelay: number,
  maxDelay: number,
  backoffMultiplier: number
): number => {
  const exponentialDelay = initialDelay * Math.pow(backoffMultiplier, attempt);
  const delayWithJitter = exponentialDelay * (0.5 + Math.random() * 0.5); // Add 0-50% jitter
  return Math.min(delayWithJitter, maxDelay);
};

/**
 * Check if an error is retryable
 */
const isRetryable = (error: unknown, retryableStatuses: number[]): boolean => {
  if (error instanceof Response) {
    return retryableStatuses.includes(error.status);
  }
  
  // Network errors are retryable
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return true;
  }
  
  return false;
};

/**
 * Fetch with automatic retry and exponential backoff
 */
export async function fetchWithRetry(
  url: string,
  options?: RequestInit,
  config: RetryConfig = {}
): Promise<Response> {
  const {
    maxRetries,
    initialDelay,
    maxDelay,
    backoffMultiplier,
    retryableStatuses,
  } = { ...DEFAULT_CONFIG, ...config };

  let lastError: unknown;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);
      
      // If response is not OK and is retryable, throw it to retry
      if (!response.ok && isRetryable(response, retryableStatuses) && attempt < maxRetries) {
        lastError = response;
        const delay = calculateDelay(attempt, initialDelay, maxDelay, backoffMultiplier);
        console.warn(
          `Request failed with status ${response.status}. ` +
          `Retrying in ${Math.round(delay)}ms... (Attempt ${attempt + 1}/${maxRetries})`
        );
        await sleep(delay);
        continue;
      }
      
      return response;
    } catch (error) {
      lastError = error;
      
      if (!isRetryable(error, retryableStatuses) || attempt >= maxRetries) {
        throw error;
      }
      
      const delay = calculateDelay(attempt, initialDelay, maxDelay, backoffMultiplier);
      console.warn(
        `Network error occurred. ` +
        `Retrying in ${Math.round(delay)}ms... (Attempt ${attempt + 1}/${maxRetries})`
      );
      await sleep(delay);
    }
  }

  throw lastError;
}

/**
 * Wrapper for JSON API calls with retry
 */
export async function apiCall<T>(
  url: string,
  options?: RequestInit,
  config?: RetryConfig
): Promise<T> {
  const response = await fetchWithRetry(url, options, config);
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`API call failed: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}
