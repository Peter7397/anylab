// Backend Health Check Service
// Prevents infinite polling when backend is down

class BackendHealthService {
  private isHealthy: boolean = true;
  private lastCheck: number = 0;
  private checkInterval: number = 30000; // Check every 30 seconds
  private consecutiveFailures: number = 0;
  private maxFailures: number = 2; // After 2 failures, mark as down
  private healthCheckPromise: Promise<boolean> | null = null;

  /**
   * Check if backend is healthy
   * Uses caching to avoid excessive requests
   */
  async checkHealth(): Promise<boolean> {
    const now = Date.now();
    
    // If we checked recently and it was healthy, return cached result
    if (this.isHealthy && (now - this.lastCheck) < 5000) {
      return true;
    }

    // If we already have a health check in progress, wait for it
    if (this.healthCheckPromise) {
      return this.healthCheckPromise;
    }

    // Perform health check
    this.healthCheckPromise = this.performHealthCheck();
    
    try {
      const result = await this.healthCheckPromise;
      return result;
    } finally {
      this.healthCheckPromise = null;
    }
  }

  private async performHealthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
      
      const response = await fetch(`${window.location.protocol}//${window.location.hostname}:8001/api/health/`, {
        method: 'GET',
        signal: controller.signal,
        cache: 'no-cache',
      });
      
      clearTimeout(timeoutId);

      if (response.ok) {
        this.isHealthy = true;
        this.consecutiveFailures = 0;
        this.lastCheck = Date.now();
        return true;
      } else {
        this.consecutiveFailures++;
        if (this.consecutiveFailures >= this.maxFailures) {
          this.isHealthy = false;
        }
        this.lastCheck = Date.now();
        return false;
      }
    } catch (error) {
      this.consecutiveFailures++;
      if (this.consecutiveFailures >= this.maxFailures) {
        this.isHealthy = false;
      }
      this.lastCheck = Date.now();
      return false;
    }
  }

  /**
   * Get current health status (cached)
   */
  getHealthStatus(): boolean {
    return this.isHealthy;
  }

  /**
   * Mark backend as healthy (after successful connection)
   */
  markHealthy(): void {
    this.isHealthy = true;
    this.consecutiveFailures = 0;
    this.lastCheck = Date.now();
  }

  /**
   * Mark backend as unhealthy
   */
  markUnhealthy(): void {
    this.isHealthy = false;
    this.lastCheck = Date.now();
  }

  /**
   * Start periodic health checks
   */
  startHealthChecks(): void {
    setInterval(() => {
      this.checkHealth().catch(() => {
        // Silently handle errors in background checks
      });
    }, this.checkInterval);
  }
}

export const backendHealth = new BackendHealthService();

// Start health checks when module loads
if (typeof window !== 'undefined') {
  backendHealth.startHealthChecks();
}

