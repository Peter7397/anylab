// API Service Layer for AnyLab Frontend
// This file handles all API communication with the Django backend

// Auto-detect API base URL based on current hostname
// This ensures the frontend always connects to the backend on the same network interface
// CHANGED: Port 8001 to avoid conflict with 7English (port 8000)
const getApiBaseUrl = () => {
  // Always detect based on current hostname to match the network interface
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  const port = '8000';  // Backend port (Docker exposes on 8000)
  
  // Helper function to check if hostname is an IP address
  const isIPAddress = (host: string): boolean => {
    // IPv4 pattern
    const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    // IPv6 pattern (simplified - checks for colons)
    const ipv6Pattern = /^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$/;
    return ipv4Pattern.test(host) || ipv6Pattern.test(host);
  };
  
  // If accessing via localhost/127.0.0.1, use localhost for backend
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//localhost:${port}/api`;
  }
  
  // If accessing via domain name (not IP address), use same domain without port
  // This works for production with Cloudflare - Nginx will handle routing /api/* to backend
  // Examples: anylab.dpdns.org, www.anylab.com, anylab.example.com
  if (!isIPAddress(hostname)) {
    // Domain name detected - use same domain (Nginx reverse proxy will route to backend)
    return `${protocol}//${hostname}/api`;
  }
  
  // Otherwise use the same hostname with port (for LAN access via IP address)
  // This ensures if you access via 192.168.1.216:3000, it connects to 192.168.1.216:8001
  return `${protocol}//${hostname}:${port}/api`;
};

// HARDCODED: API configuration - no environment variables needed
const API_BASE_URL = getApiBaseUrl();
const JWT_STORAGE_KEY = 'anylab_token';  // HARDCODED: JWT storage key
const REFRESH_TOKEN_KEY = 'anylab_refresh_token';  // HARDCODED: Refresh token key

// Types
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  message?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  employee_id?: string;
  department?: string;
  position?: string;
  phone?: string;
  is_active: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
}

export interface System {
  id: string;
  name: string;
  ip: string;
  os: string;
  lastLogin: string;
  status: 'online' | 'warning' | 'offline';
}

export interface MergedPermissions {
  features?: Record<string, boolean>;
  api?: Record<string, boolean>;
  routes?: string[];
}

export interface MyPermissionsResponse {
  permissions: MergedPermissions;
}

export interface MaintenanceTask {
  id: string;
  title: string;
  description: string;
  scheduled_date: string;
  status: 'pending' | 'in-progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assigned_to?: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  source: string;
  details?: any;
}

// API Client Class
class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  // Get auth token from localStorage
  private getAuthToken(): string | null {
    return localStorage.getItem(JWT_STORAGE_KEY);
  }

  // Set auth token in localStorage
  private setAuthToken(token: string): void {
    console.log('API setAuthToken - Storing token with key:', JWT_STORAGE_KEY);
    localStorage.setItem(JWT_STORAGE_KEY, token);
    const stored = localStorage.getItem(JWT_STORAGE_KEY);
    console.log('API setAuthToken - Verification - token stored:', !!stored, stored ? stored.substring(0, 50) + '...' : 'none');
  }

  // Remove auth token from localStorage
  private removeAuthToken(): void {
    localStorage.removeItem(JWT_STORAGE_KEY);
  }

  // Get refresh token from localStorage
  private getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  // Set refresh token in localStorage
  private setRefreshToken(token: string): void {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  }

  // Remove refresh token from localStorage
  private removeRefreshToken(): void {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  // Create headers for API requests
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = this.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Add Accept-Language header based on user's language preference
// Default to Chinese (zh-CN) if no language is set
    const language = localStorage.getItem('anylab_language') || 'zh-CN';
    headers['Accept-Language'] = language;

    return headers;
  }

  // Make API request
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    // Check if token is expired before making request
    const token = this.getAuthToken();
    if (token && this.isTokenExpired(token)) {
      // Try to refresh token proactively
      const refreshed = await this.refreshToken();
      if (!refreshed) {
        throw new Error('Authentication required');
      }
    }
    
    // Only set default headers if no headers are provided
    const config: RequestInit = {
      ...options,
    };
    
    // Only add default headers if they're not already set
    if (!config.headers) {
      config.headers = this.getHeaders();
    }

    try {
      const response = await fetch(url, config);
      
      // Check content type before parsing
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // Non-JSON response (e.g., HTML error pages)
        const text = await response.text();
        console.error('Non-JSON response:', text.substring(0, 200));
        throw new Error(`Server returned non-JSON response (${response.status} ${response.statusText})`);
      }

      if (!response.ok) {
        if (response.status === 401) {
          const refreshed = await this.refreshToken();
          if (refreshed) {
            return this.request(endpoint, options);
          } else {
            // Do not auto-redirect; let callers decide how to handle auth state
            throw new Error('Authentication required');
          }
        }
        throw new Error(data.message || data.error || `HTTP ${response.status}`);
      }

      return {
        data,
        status: response.status,
        message: data.message,
      };
    } catch (error: any) {
      console.error('API request failed:', error);
      
      // If it's a network/connection error, mark backend as unhealthy
      if (error?.message?.includes('Failed to fetch') || 
          error?.message?.includes('NetworkError') ||
          error?.name === 'TypeError') {
        // Import backendHealth only when needed to avoid circular dependency
        import('./backendHealth').then(({ backendHealth }) => {
          backendHealth.markUnhealthy();
        }).catch(() => {
          // Ignore import errors
        });
      }
      
      throw error;
    }
  }

  // Generic HTTP methods
  async get<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const config: RequestInit = { ...options, method: 'POST' };
    
    if (data) {
      if (data instanceof FormData) {
        // For FormData, don't set Content-Type header
        config.body = data;
        // Set headers without Content-Type for FormData
        const headers: HeadersInit = {};
        const token = this.getAuthToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        config.headers = headers;
      } else {
        config.body = JSON.stringify(data);
        // Set default headers for JSON requests
        if (!config.headers) {
          config.headers = this.getHeaders();
        }
      }
    } else {
      // Set default headers for requests without body
      if (!config.headers) {
        config.headers = this.getHeaders();
      }
    }
    
    return this.request<T>(endpoint, config);
  }

  async put<T>(endpoint: string, data?: any, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const config: RequestInit = { ...options, method: 'PUT' };
    
    if (data) {
      config.body = JSON.stringify(data);
    }
    
    return this.request<T>(endpoint, config);
  }

  async delete<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  // Check if JWT token is expired
  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      // Consider token expired if less than 1 minute until expiration
      return exp - now < 60000;
    } catch (e) {
      // If we can't parse token, consider it invalid/expired
      return true;
    }
  }

  // Refresh authentication token
  private async refreshToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await this.publicRequest<{ access: string }>('/token/refresh/', {
        method: 'POST',
        body: JSON.stringify({ refresh: refreshToken }),
      });

      this.setAuthToken(response.data.access);
      
      // Notify AuthContext that token was refreshed
      // Use dynamic import to avoid circular dependency
      import('../context/AuthContext').then(({ notifyAuthTokenRefreshed }) => {
        notifyAuthTokenRefreshed();
      }).catch(() => {
        // AuthContext might not be loaded yet, that's okay
      });
      
        return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  // Public API request (no auth headers) for endpoints like login, token refresh, etc.
  private async publicRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    };

    try {
      const response = await fetch(url, config);
      
      // Check content type before parsing
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // Non-JSON response (e.g., HTML error pages)
        const text = await response.text();
        console.error('Non-JSON response:', text.substring(0, 200));
        throw new Error(`Server returned non-JSON response (${response.status} ${response.statusText})`);
      }

      if (!response.ok) {
        // For public requests, don't try to refresh token
        throw new Error(data.detail || data.message || data.error || `HTTP ${response.status}`);
      }

      return {
        data,
        status: response.status,
        message: data.message,
      };
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication Methods
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    console.log('API login - Making login request...');
    const response = await this.publicRequest<AuthTokens>('/token/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    console.log('API login - Response received:', {
      hasAccess: !!response.data.access,
      hasRefresh: !!response.data.refresh,
      accessLength: response.data.access?.length,
      refreshLength: response.data.refresh?.length
    });

    this.setAuthToken(response.data.access);
    this.setRefreshToken(response.data.refresh);

    // Verify tokens were stored
    const storedToken = localStorage.getItem(JWT_STORAGE_KEY);
    const storedRefresh = localStorage.getItem(REFRESH_TOKEN_KEY);
    console.log('API login - Storage verification:', {
      tokenStored: !!storedToken,
      refreshStored: !!storedRefresh
    });

    return response.data;
  }

  logout(): void {
    this.removeAuthToken();
    this.removeRefreshToken();
    // Redirect to login page
    window.location.href = '/login';
  }

  async getMyPermissions(): Promise<MergedPermissions> {
    console.log('API getMyPermissions - Making request to /users/me/permissions/');
    console.log('API getMyPermissions - Token:', this.getAuthToken() ? 'present' : 'missing');
    const response = await this.request<MyPermissionsResponse>('/users/me/permissions/');
    console.log('API getMyPermissions - Raw response:', response);
    const permissions = response.data.permissions || {};
    console.log('API getMyPermissions - Extracted permissions:', permissions);
    return permissions;
  }

  async getCurrentUser(): Promise<User> {
    console.log('API getCurrentUser - Making request to /users/profile/');
    console.log('API getCurrentUser - Token:', this.getAuthToken() ? 'present' : 'missing');
    const response = await this.request<{ user: User }>('/users/profile/');
    console.log('API getCurrentUser - Raw response:', response);
    const user = (response.data as any).user as User;
    console.log('API getCurrentUser - Extracted user:', user);
    if (!user) {
      console.error('API getCurrentUser - No user in response!', response.data);
      throw new Error('Failed to get user profile: user data is missing');
    }
    return user;
  }

  async updateCurrentUser(userData: Partial<User>): Promise<User> {
    const response = await this.request<{ user: User }>('/users/profile/', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
    return (response.data as any).user as User;
  }

  // Health Check
  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseURL}/health/`);
    return response.json();
  }

  // Enhanced Health Checks
  async getDetailedHealthCheck(): Promise<any> {
    const response = await this.request('/ai/health/detailed/');
    return response.data;
  }

  async getProcessorHealth(): Promise<any> {
    const response = await this.request('/ai/health/processors/');
    return response.data;
  }

  // Metrics Dashboard API
  async getProcessingMetrics(hours: number = 24, includeSystem: boolean = true): Promise<any> {
    const queryParams = new URLSearchParams();
    queryParams.append('hours', hours.toString());
    queryParams.append('include_system', includeSystem.toString());
    const response = await this.request(`/ai/metrics/processing/?${queryParams.toString()}`);
    return response.data;
  }

  async getProcessingTimeline(hours: number = 24, interval: number = 1): Promise<any> {
    const queryParams = new URLSearchParams();
    queryParams.append('hours', hours.toString());
    queryParams.append('interval', interval.toString());
    const response = await this.request(`/ai/metrics/processing/timeline/?${queryParams.toString()}`);
    return response.data;
  }

  async getErrorSummary(hours: number = 24, limit: number = 20): Promise<any> {
    const queryParams = new URLSearchParams();
    queryParams.append('hours', hours.toString());
    queryParams.append('limit', limit.toString());
    const response = await this.request(`/ai/metrics/errors/?${queryParams.toString()}`);
    return response.data;
  }

  // Users API
  async getUsers(): Promise<User[]> {
    const response = await this.request<{users: User[]}>('/users/');
    // Backend returns {users: [...]} format
    return response.data.users || [];
  }

  async createUser(userData: Partial<User>): Promise<User> {
    const response = await this.request<User>('/users/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    return response.data;
  }

  async updateUser(id: number, userData: Partial<User>): Promise<User> {
    const response = await this.request<User>(`/users/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
    return response.data;
  }

  async resetUserPassword(userId: number, password: string): Promise<void> {
    await this.request(`/users/${userId}/reset_password/`, {
      method: 'POST',
      body: JSON.stringify({ password })
    });
  }

  async deleteUser(id: number): Promise<void> {
    await this.request(`/users/${id}/`, {
      method: 'DELETE',
    });
  }

  // Roles API
  async getRoles(): Promise<any[]> {
    const response = await this.request<any[]>('/users/roles/');
    // Backend returns array directly
    return Array.isArray(response.data) ? response.data : [];
  }

  async createRole(roleData: any): Promise<any> {
    const response = await this.request('/users/roles/', {
      method: 'POST',
      body: JSON.stringify(roleData),
    });
    return response.data;
  }

  async updateRole(id: number, roleData: any): Promise<any> {
    const response = await this.request(`/users/roles/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(roleData),
    });
    return response.data;
  }

  async deleteRole(id: number): Promise<void> {
    await this.request(`/users/roles/${id}/`, {
      method: 'DELETE',
    });
  }

  async assignRole(userId: number, roleId: number): Promise<any> {
    const response = await this.request('/users/roles/assign/', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, role_id: roleId }),
    });
    return response.data;
  }

  async removeRole(userId: number, roleId: number): Promise<void> {
    await this.request('/users/roles/remove/', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, role_id: roleId }),
    });
  }

  async getUserRoles(userId: number): Promise<any[]> {
    const response = await this.request<any[]>(`/users/${userId}/roles/`);
    // Backend returns array directly
    return Array.isArray(response.data) ? response.data : [];
  }

  // Analytics API
  async getUserStatistics(): Promise<any> {
    const response = await this.request('/ai/analytics/user/stats/');
    return response.data;
  }

  async getContributionAnalytics(): Promise<any> {
    const response = await this.request('/ai/analytics/user/contributions/');
    return response.data;
  }

  async getPerformanceAnalytics(): Promise<any> {
    const response = await this.request('/ai/analytics/performance/');
    return response.data;
  }

  async getDocumentAnalytics(): Promise<any> {
    const response = await this.request('/ai/analytics/documents/');
    return response.data;
  }

  async getUserBehaviorStats(): Promise<any> {
    const response = await this.request('/ai/analytics/user/behavior/');
    return response.data;
  }

  // Document Processing API
  async processVideo(file: File, title?: string, description?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (description) formData.append('description', description);

    const token = this.getAuthToken();
    const response = await fetch(`${this.baseURL}/ai/process/video/process/`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    return await response.json();
  }

  async processImage(file: File, title?: string, description?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (description) formData.append('description', description);

    const token = this.getAuthToken();
    const response = await fetch(`${this.baseURL}/ai/process/image/process/`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    return await response.json();
  }

  async getVideoTranscripts(): Promise<any> {
    const response = await this.request('/ai/process/video/transcripts/');
    return response.data;
  }

  async getOCRResults(): Promise<any> {
    const response = await this.request('/ai/process/image/ocr-results/');
    return response.data;
  }

  // Scraper API - SSB
  async scrapeSSB(config: any = {}): Promise<any> {
    const response = await this.request('/ai/ssb/scrape/database/', {
      method: 'POST',
      body: JSON.stringify({ config }),
    });
    return response.data;
  }

  async scrapeSSBHelpPortal(config: any = {}): Promise<any> {
    const response = await this.request('/ai/ssb/scrape/help-portal/', {
      method: 'POST',
      body: JSON.stringify({ config }),
    });
    return response.data;
  }

  async getSSBStatus(): Promise<any> {
    const response = await this.request('/ai/ssb/status/');
    return response.data;
  }

  async triggerSSBScraping(config: any = {}): Promise<any> {
    const response = await this.request('/ai/ssb/trigger/', {
      method: 'POST',
      body: JSON.stringify({ config }),
    });
    return response.data;
  }

  // importSSBFile removed - now using standard uploadDocument() for all files

  async scheduleSSB(config: any): Promise<any> {
    const response = await this.request('/ai/ssb/schedule/', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.data;
  }

  // Scraper API - GitHub
  async scanGitHubRepos(config: any): Promise<any> {
    const response = await this.request('/ai/github/scan/repositories/', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.data;
  }

  async scanGitHubFiles(config: any): Promise<any> {
    const response = await this.request('/ai/github/scan/files/', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.data;
  }

  async getGitHubStatus(): Promise<any> {
    const response = await this.request('/ai/github/status/');
    return response.data;
  }

  async scheduleGitHub(config: any): Promise<any> {
    const response = await this.request('/ai/github/schedule/', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.data;
  }

  async getGitHubAnalytics(): Promise<any> {
    const response = await this.request('/ai/github/analytics/');
    return response.data;
  }

  // Scraper API - Forum
  async scrapeForumPosts(config: any): Promise<any> {
    const response = await this.request('/ai/forum/scrape/posts/', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.data;
  }

  async getForumStatus(): Promise<any> {
    const response = await this.request('/ai/forum/status/');
    return response.data;
  }

  async scheduleForum(config: any): Promise<any> {
    const response = await this.request('/ai/forum/schedule/', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.data;
  }

  async getForumAnalytics(): Promise<any> {
    const response = await this.request('/ai/forum/analytics/');
    return response.data;
  }

  // Scraper API - HTML
  async parseHTMLURL(url: string, config: any = {}): Promise<any> {
    const response = await this.request('/ai/html/parse/url/', {
      method: 'POST',
      body: JSON.stringify({ url, ...config }),
    });
    return response.data;
  }

  async parseHTMLText(html: string, config: any = {}): Promise<any> {
    const response = await this.request('/ai/html/parse/text/', {
      method: 'POST',
      body: JSON.stringify({ html, ...config }),
    });
    return response.data;
  }

  async getHTMLStatus(): Promise<any> {
    const response = await this.request('/ai/html/status/');
    return response.data;
  }

  async scheduleHTML(config: any): Promise<any> {
    const response = await this.request('/ai/html/schedule/', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.data;
  }

  async getHTMLAnalytics(): Promise<any> {
    const response = await this.request('/ai/html/analytics/');
    return response.data;
  }

  // Monitoring API
  async getSystems(): Promise<System[]> {
    const response = await this.request<System[]>('/monitoring/systems/');
    return response.data;
  }

  async getSystemMetrics(systemId: string): Promise<any> {
    const response = await this.request(`/monitoring/systems/${systemId}/metrics/`);
    return response.data;
  }

  async getLogs(filters?: any): Promise<LogEntry[]> {
    const queryParams = new URLSearchParams(filters).toString();
    const endpoint = `/monitoring/logs/${queryParams ? `?${queryParams}` : ''}`;
    const response = await this.request<LogEntry[]>(endpoint);
    return response.data;
  }

  // Maintenance API
  async getMaintenanceTasks(): Promise<MaintenanceTask[]> {
    const response = await this.request<MaintenanceTask[]>('/maintenance/tasks/');
    return response.data;
  }

  async createMaintenanceTask(taskData: Partial<MaintenanceTask>): Promise<MaintenanceTask> {
    const response = await this.request<MaintenanceTask>('/maintenance/tasks/', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
    return response.data;
  }

  async updateMaintenanceTask(id: string, taskData: Partial<MaintenanceTask>): Promise<MaintenanceTask> {
    const response = await this.request<MaintenanceTask>(`/maintenance/tasks/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(taskData),
    });
    return response.data;
  }

  async deleteMaintenanceTask(id: string): Promise<void> {
    await this.request(`/maintenance/tasks/${id}/`, {
      method: 'DELETE',
    });
  }

  // AI Assistant API
  async sendChatMessage(message: string): Promise<any> {
    const response = await this.request('/ai/chat/', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    return response.data;
  }

  // Chat with Ollama
  async chatWithOllama(prompt: string, opts?: { 
    max_tokens?: number; 
    temperature?: number; 
    top_p?: number;
    top_k?: number;
    repeat_penalty?: number;
    num_ctx?: number;
  }): Promise<{ response: string; model: string }> {
    const response = await this.request<{ response: string; model: string }>('/ai/chat/ollama/', {
      method: 'POST',
      body: JSON.stringify({ prompt, ...opts }),
    });
    return response.data;
  }

  // Unified Chat History API
  async getUnifiedHistory(params?: { limit?: number; channel?: string; thread_id?: string }): Promise<Array<{ id: number; channel: string; thread_id: string; role: 'user'|'assistant'; content: string; metadata?: any; created_at: string }>> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.channel) query.append('channel', params.channel);
    if (params?.thread_id) query.append('thread_id', params.thread_id);
    const endpoint = `/ai/chat/history${query.toString() ? `?${query.toString()}` : ''}`;
    const response = await this.request<Array<{ id: number; channel: string; thread_id: string; role: 'user'|'assistant'; content: string; metadata?: any; created_at: string }>>(endpoint);
    return response.data as any;
  }

  async createChatMessage(payload: { channel: string; thread_id?: string; role: 'user'|'assistant'; content: string; metadata?: any }): Promise<{ id: number; channel: string; thread_id: string; role: 'user'|'assistant'; content: string; metadata?: any; created_at: string }>{
    const response = await this.request<{ id: number; channel: string; thread_id: string; role: 'user'|'assistant'; content: string; metadata?: any; created_at: string }>(
      '/ai/chat/message',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
    return response.data as any;
  }

  async getKnowledgeBase(): Promise<any> {
    const response = await this.request('/ai/knowledge/');
    return response.data;
  }

  // Vector search over pgvector
  async vectorSearch(query: string, topK: number = 5): Promise<{ query: string; top_k: number; results: Array<{ title: string; chunk_index: number; content: string; similarity: number }>}> {
    const response = await this.request<{ query: string; top_k: number; results: Array<{ title: string; chunk_index: number; content: string; similarity: number }>}>('/ai/rag/search/vector/', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    });
    return response.data;
  }

  async ragSearch(query: string, topK: number = 10, searchMode: string = 'advanced'): Promise<{ response: string; sources: Array<{ title: string; content: string; similarity: number }>; query: string; comprehensive_stats?: any }> {
    const response = await this.request<{ response: string; sources: Array<{ title: string; content: string; similarity: number }>; query: string; comprehensive_stats?: any }>('/ai/rag/search/', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK, search_mode: searchMode }),
    });
    return response.data;
  }

  // RAG chat (retrieval + prompt construction; server may return context and prompt)
  async ragChat(prompt: string): Promise<{ success: boolean; query: string; rag_prompt?: string; context_chunks?: Array<{ text: string; similarity: number }>; model_used?: string; error?: string }> {
    const response = await this.request<{ success: boolean; query: string; rag_prompt?: string; context_chunks?: Array<{ text: string; similarity: number }>; model_used?: string; error?: string }>('/ai/rag/chat/', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
    return response.data;
  }

  // Advanced RAG Search
  async advancedRagSearch(query: string, topK: number = 5, searchMode: string = 'hybrid'): Promise<{ 
    response: string; 
    sources: Array<{ title: string; content: string; similarity: number; page?: number }>; 
    query: string; 
    tokens_used?: number;
    search_method?: string;
    search_stats?: any;
  }> {
    const response = await this.request<{ 
      response: string; 
      sources: Array<{ title: string; content: string; similarity: number; page?: number }>; 
      query: string; 
      tokens_used?: number;
      search_method?: string;
      search_stats?: any;
    }>('/ai/rag/search/advanced/', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK, search_mode: searchMode }),
    });
    return response.data;
  }

  // Comprehensive RAG Search
  async comprehensiveRagSearch(query: string, topK: number = 10, includeStats: boolean = false): Promise<{ 
    response: string; 
    sources: Array<{ title: string; content: string; similarity: number; page?: number }>; 
    query: string; 
    tokens_used?: number;
    search_method?: string;
    search_stats?: any;
  }> {
    const response = await this.request<{ 
      response: string; 
      sources: Array<{ title: string; content: string; similarity: number; page?: number }>; 
      query: string; 
      tokens_used?: number;
      search_method?: string;
      search_stats?: any;
    }>('/ai/rag/search/comprehensive/', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK, include_stats: includeStats }),
    });
    return response.data;
  }

  // Get Graph Visualization Data
  async getGraphForQuery(query: string, maxNodes: number = 50, maxDepth: number = 2): Promise<{
    nodes: Array<{
      id: string;
      label: string;
      type: string;
      entityType?: string;
      group: string;
      size: number;
    }>;
    edges: Array<{
      from: string;
      to: string;
      type: string;
      label: string;
      weight?: number;
    }>;
    entities: Array<{
      id: string;
      name: string;
      type: string;
      normalized: string;
      confidence: number;
    }>;
    stats: {
      total_nodes: number;
      total_edges: number;
      query_entities: number;
    };
  }> {
    const response = await this.request<{
      nodes: Array<{
        id: string;
        label: string;
        type: string;
        entityType?: string;
        group: string;
        size: number;
      }>;
      edges: Array<{
        from: string;
        to: string;
        type: string;
        label: string;
        weight?: number;
      }>;
      entities: Array<{
        id: string;
        name: string;
        type: string;
        normalized: string;
        confidence: number;
      }>;
      stats: {
        total_nodes: number;
        total_edges: number;
        query_entities: number;
      };
    }>('/ai/rag/graph/query/', {
      method: 'POST',
      body: JSON.stringify({ query, max_nodes: maxNodes, max_depth: maxDepth }),
    });
    return response.data;
  }

  // Graph RAG Search
  async graphRagSearch(query: string, topK: number = 10): Promise<{ 
    response: string; 
    sources: Array<{ 
      title: string; 
      content: string; 
      similarity?: number; 
      page?: number;
      source?: 'vector+graph' | 'vector' | 'graph';
      graph_boost?: boolean;
      matched_entities?: Array<{ name: string; type: string }>;
    }>; 
    query: string; 
    search_method?: string;
    graph_stats?: {
      total_results: number;
      graph_enhanced: number;
      vector_only: number;
      query_entities: Array<{ name: string; type: string; normalized?: string }>;
    };
    entity_matches?: {
      exact_entities: Array<{ name: string; type: string }>;
      semantic_entities: Array<{ name: string; type: string; similarity: number }>;
      total_exact: number;
      total_semantic: number;
    };
  }> {
    const response = await this.request<{ 
      response: string; 
      sources: Array<{ 
        title: string; 
        content: string; 
        similarity?: number; 
        page?: number;
        source?: 'vector+graph' | 'vector' | 'graph';
        graph_boost?: boolean;
        matched_entities?: Array<{ name: string; type: string }>;
      }>; 
      query: string; 
      search_method?: string;
      graph_stats?: {
        total_results: number;
        graph_enhanced: number;
        vector_only: number;
        query_entities: Array<{ name: string; type: string; normalized?: string }>;
      };
      entity_matches?: {
        exact_entities: Array<{ name: string; type: string }>;
        semantic_entities: Array<{ name: string; type: string; similarity: number }>;
        total_exact: number;
        total_semantic: number;
      };
    }>('/ai/rag/search/graph/', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    });
    return response.data;
  }

  // Troubleshooting AI - Log Analysis
  async analyzeLogs(data: { query: string; log_content: string }): Promise<{
    analysis: string; 
    suggestions: string[];
    severity?: 'low' | 'medium' | 'high';
  }> {
    const response = await this.request<{ 
      analysis: string; 
      suggestions: string[];
      severity?: 'low' | 'medium' | 'high';
    }>('/ai/troubleshoot/analyze/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.data;
  }

  // License Management
  async getLicenseStatus(): Promise<any> {
    // TODO: Implement license status endpoint
    // Temporarily return mock data until endpoint is implemented
    return { status: 'active', expired_at: null };
  }

  async listLicenses(): Promise<any> {
    // TODO: Implement license list endpoint
    // Temporarily return empty list until endpoint is implemented
    return [];
  }

  async importLicense(file: File): Promise<any> {
    // TODO: Implement license import endpoint
    throw new Error('License import not yet implemented');
  }

  async activateLicense(key: string): Promise<any> {
    const response = await this.request('/admin/licenses/activate/', {
      method: 'POST',
      body: JSON.stringify({ license_key: key }),
    });
    return response.data;
  }

  // Upload a PDF for RAG processing (builds vectors in backend)
  async uploadRagPDF(file: File, title?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);

    const url = `${this.baseURL}/ai/rag/upload/`;
    const headers: HeadersInit = {};
    const token = localStorage.getItem(JWT_STORAGE_KEY);
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const resp = await fetch(url, { method: 'POST', headers, body: formData });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.error || `Upload failed: ${resp.status}`);
    }
    return resp.json();
  }

  // Weblinks API
  async getWeblinks(): Promise<{ links: Array<{ id: number; title: string; url: string; tags: string[]; created_at: string; updated_at: string; added_by?: number }>;
    count: number; }> {
    const response = await this.request<{ links: Array<{ id: number; title: string; url: string; tags: string[]; created_at: string; updated_at: string; added_by?: number }>; count: number }>('/ai/weblinks/');
    return response.data;
  }

  async createWeblink(params: { title: string; url: string; tags?: string[] }): Promise<any> {
    const response = await this.request<{ id: number; title: string; url: string; tags: string[]; created_at: string; updated_at: string; added_by?: number }>('/ai/weblinks/create/', {
      method: 'POST',
      body: JSON.stringify(params),
    });
    return response.data;
  }

  async deleteWeblink(id: number): Promise<void> {
    await this.request(`/ai/weblinks/${id}/delete/`, { method: 'DELETE' });
  }

  // Knowledge share API
  async getShareSettings(): Promise<{ id: number; enabled: boolean; share_token?: string | null }> {
    const response = await this.request<{ id: number; enabled: boolean; share_token?: string | null }>('/ai/share/');
    return response.data;
  }

  async setShareEnabled(enabled: boolean): Promise<{ id: number; enabled: boolean; share_token?: string | null }> {
    const response = await this.request<{ id: number; enabled: boolean; share_token?: string | null }>('/ai/share/', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    });
    return response.data;
  }

  // PDF Management API
  async uploadPDF(file: File, title: string, description?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) {
      formData.append('description', description);
    }

    // Use the post method which handles FormData and authentication properly
    // This ensures token refresh logic is applied and errors are handled consistently
    const response = await this.post('/ai/pdfs/upload/', formData);
    return response.data;
  }

  async getPDFs(): Promise<any> {
    const response = await this.request('/ai/pdfs/');
    return response.data;
  }

  async downloadPDF(pdfId: number): Promise<Blob> {
    const url = `${this.baseURL}/ai/pdfs/${pdfId}/download/`;
    const headers: HeadersInit = {};
    
    const token = this.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    
    return response.blob();
  }

  async deletePDF(pdfId: number): Promise<void> {
    await this.request(`/ai/pdfs/${pdfId}/delete/`, {
      method: 'DELETE',
    });
  }

  async searchPDFs(query: string, searchType: 'title' | 'content' | 'both' = 'both'): Promise<any> {
    const response = await this.request('/ai/pdfs/search/', {
      method: 'POST',
      body: JSON.stringify({ query, search_type: searchType }),
    });
    return response.data;
  }

  // Enhanced Document Management API
  async getDocuments(): Promise<any> {
    const response = await this.request('/ai/documents/');
    // Backend returns {message, timestamp, documents, total, page, page_size}
    // Frontend expects response.data which contains all these fields
    return response.data;
  }

  // File processing status (UploadedFile)
  async getFileProcessingStatus(fileId: number): Promise<{
    id: number;
    filename: string;
    file_size: number;
    processing_status: 'pending' | 'metadata_extracting' | 'chunking' | 'embedding' | 'ready' | 'failed';
    metadata_extracted: boolean;
    chunks_created: boolean;
    embeddings_created: boolean;
    chunk_count: number;
    embedding_count: number;
    is_ready: boolean;
    processing_error?: string | null;
    uploaded_at?: string | null;
    processing_started_at?: string | null;
    processing_completed_at?: string | null;
    progress_percentage?: number;
  }> {
    const response = await this.request<{
      id: number;
      filename: string;
      file_size: number;
      processing_status: 'pending' | 'metadata_extracting' | 'chunking' | 'embedding' | 'ready' | 'failed';
      metadata_extracted: boolean;
      chunks_created: boolean;
      embeddings_created: boolean;
      chunk_count: number;
      embedding_count: number;
      is_ready: boolean;
      processing_error?: string | null;
      uploaded_at?: string | null;
      processing_started_at?: string | null;
      processing_completed_at?: string | null;
      progress_percentage?: number;
    }>(`/ai/documents/files/${fileId}/status/`);
    return response.data;
  }

  async retryFileProcessing(fileId: number): Promise<{ uploaded_file_id: number; status: string }>{
    const response = await this.request<{ uploaded_file_id: number; status: string }>(`/ai/documents/files/${fileId}/retry/`, {
      method: 'POST',
    });
    return response.data;
  }

  async deleteUploadedFile(fileId: number): Promise<any> {
    const response = await this.request(`/ai/documents/files/${fileId}/delete/`, {
      method: 'DELETE',
    });
    return response.data;
  }

  async uploadDocument(
    file: File, 
    title: string, 
    description?: string, 
    documentType?: string,
    productCategory?: string,
    contentType?: string,
    version?: string
  ): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) {
      formData.append('description', description);
    }
    if (documentType) {
      formData.append('document_type', documentType);
    }
    if (productCategory) {
      formData.append('product_category', productCategory);
    }
    if (contentType) {
      formData.append('content_type', contentType);
    }
    if (version) {
      formData.append('version', version);
    }

    // Use the post method which handles FormData and authentication properly
    // This ensures token refresh logic is applied and errors are handled consistently
    const response = await this.post('/ai/documents/upload/', formData);
    return response.data;
  }

  // Webpage discovery and queuing
  async discoverWebpageFiles(config: {
    url: string;
    max_depth?: number;
    same_domain_only?: boolean;
    file_type_filters?: string[];
    max_file_size_mb?: number;
  }): Promise<any> {
    const response = await this.request('/ai/upload/discover-webpage/', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.data;
  }

  async queueWebpageFiles(files: any[], source: string): Promise<any> {
    const response = await this.request('/ai/upload/queue-webpage-files/', {
      method: 'POST',
      body: JSON.stringify({ files, source }),
    });
    return response.data;
  }

  // Queue statistics and processing health
  async getQueueStats(): Promise<any> {
    const response = await this.request('/ai/upload/queue/stats/', {
      method: 'GET',
    });
    return response.data;
  }

  async downloadDocument(docId: number): Promise<Blob> {
    const url = `${this.baseURL}/ai/documents/${docId}/download/`;
    const headers: HeadersInit = {};
    
    const token = this.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    
    return response.blob();
  }

  async deleteDocument(docId: number): Promise<void> {
    await this.request(`/ai/documents/${docId}/delete/`, {
      method: 'DELETE',
    });
  }

  async updateDocumentMetadata(docId: number, metadataUpdates: any): Promise<any> {
    const response = await this.request('/ai/content/metadata/' + docId + '/update/', {
      method: 'POST',
      body: JSON.stringify({ metadata_updates: metadataUpdates }),
    });
    return response.data;
  }

  async extractDocumentsMetadata(): Promise<any> {
    const response = await this.request('/ai/documents/extract-metadata/', {
      method: 'POST',
    });
    return response.data;
  }

  async getProductDocuments(productCategory: string, options?: { latestOnly?: boolean }): Promise<any> {
    let url = `/ai/products/${productCategory}/documents/`;
    if (options?.latestOnly) {
      url += '?latest_only=true';
    }
    const response = await this.request(url);
    return response.data;
  }

  async getAvailableProducts(): Promise<{ products: Array<{ product_category: string; document_count: number }> }> {
    const response = await this.request<{ products: Array<{ product_category: string; document_count: number }> }>(
      '/ai/products/available/'
    );
    return response.data as any;
  }

  async searchDocuments(query: string, searchType: 'title' | 'content' | 'both' = 'both', documentType: string = 'all'): Promise<any> {
    const response = await this.request('/ai/documents/search/', {
      method: 'POST',
      body: JSON.stringify({ query, search_type: searchType, document_type: documentType }),
    });
    return response.data;
  }

  // NEW: Bulk Import API Methods
  async listFolders(path: string = '/'): Promise<any> {
    const response = await this.request(`/ai/process/bulk/list-folders/?path=${encodeURIComponent(path)}`, {
      method: 'GET',
    });
    return response.data;
  }

  async scanFolder(folderPath: string): Promise<any> {
    const response = await this.request('/ai/process/bulk/scan-folder/', {
      method: 'POST',
      body: JSON.stringify({ folder_path: folderPath }),
    });
    return response.data;
  }

  async bulkImportFiles(files: Array<{ file_path: string; filename: string }>): Promise<any> {
    const response = await this.request('/ai/process/bulk/import-files/', {
      method: 'POST',
      body: JSON.stringify({ files }),
    });
    return response.data;
  }

  async getBulkImportStatus(status?: string): Promise<any> {
    let url = '/ai/process/bulk/status/';
    if (status) {
      url += `?status=${status}`;
    }
    const response = await this.request(url);
    return response.data;
  }

  // Performance monitoring
  async getPerformanceStats(): Promise<any> {
    const response = await this.request('/ai/performance/stats/');
    return response.data;
  }

  // Dashboard API
  async getDashboardStats(): Promise<any> {
    const response = await this.request('/ai/dashboard/stats/');
    return response.data;
  }

  // System Settings API
  async getSystemSettings(): Promise<any> {
    const response = await this.request('/ai/admin/settings/');
    return response.data;
  }

  async testConnection(type: string, config: any): Promise<any> {
    const response = await this.request('/ai/admin/settings/test-connection/', {
      method: 'POST',
      body: JSON.stringify({ type, config })
    });
    return response.data;
  }

  async switchAIMode(mode: 'performance' | 'lightweight'): Promise<any> {
    const response = await this.request('/ai/admin/settings/switch-ai-mode/', {
      method: 'POST',
      body: JSON.stringify({ mode })
    });
    return response.data;
  }

  async updateSystemSettings(settings: { rag?: { model?: string }; file_upload?: { enable_ocr_for_scanned_files?: boolean } }): Promise<any> {
    const response = await this.request('/ai/admin/settings/update/', {
      method: 'PUT',
      body: JSON.stringify(settings)
    });
    return response.data;
  }

  async getAvailableModels(): Promise<string[]> {
    const response = await this.request<{ success: boolean; models?: string[]; error?: string }>('/ai/admin/settings/available-models/');
    if (response.data.success) {
      return response.data.models || [];
    }
    return [];
  }

  // Website Management API Methods
  async getWebsites(params?: { status?: string; domain?: string; search?: string }): Promise<any> {
    let url = '/ai/websites/';
    if (params) {
      const queryParams = new URLSearchParams();
      if (params.status) queryParams.append('status', params.status);
      if (params.domain) queryParams.append('domain', params.domain);
      if (params.search) queryParams.append('search', params.search);
      if (queryParams.toString()) {
        url += `?${queryParams.toString()}`;
      }
    }
    const response = await this.request(url);
    return response.data;
  }

  async addWebsite(websiteData: {
    url: string;
    title?: string;
    description?: string;
    auto_refresh?: boolean;
    refresh_interval_days?: number;
  }): Promise<any> {
    const response = await this.request('/ai/websites/add/', {
      method: 'POST',
      body: JSON.stringify(websiteData),
    });
    return response.data;
  }

  async getWebsiteStatus(websiteId: number): Promise<any> {
    const response = await this.request(`/ai/websites/${websiteId}/status/`);
    return response.data;
  }

  async refreshWebsite(websiteId: number): Promise<any> {
    const response = await this.request(`/ai/websites/${websiteId}/refresh/`, {
      method: 'POST',
    });
    return response.data;
  }

  async deleteWebsite(websiteId: number): Promise<any> {
    const response = await this.request(`/ai/websites/${websiteId}/delete/`, {
      method: 'DELETE',
    });
    return response.data;
  }

  async retryWebsiteProcessing(websiteId: number): Promise<any> {
    const response = await this.request(`/ai/websites/${websiteId}/retry/`, {
      method: 'POST',
    });
    return response.data;
  }

  async updateWebsiteSettings(websiteId: number, settings: {
    title?: string;
    description?: string;
    auto_refresh?: boolean;
    refresh_interval_days?: number;
  }): Promise<any> {
    const response = await this.request(`/ai/websites/${websiteId}/settings/`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
    return response.data;
  }

  async getWebsiteStatistics(): Promise<any> {
    const response = await this.request('/ai/websites/statistics/');
    return response.data;
  }

  // Forum API methods
  async getForumCategories(): Promise<any> {
    const response = await this.request('/forum/categories/');
    return response.data;
  }

  async getForumTags(search?: string): Promise<any> {
    const params = search ? `?search=${encodeURIComponent(search)}` : '';
    const response = await this.request(`/forum/tags${params}`);
    return response.data;
  }

  async getForumPosts(params?: {
    page?: number;
    page_size?: number;
    category?: number;
    tag?: number;
    search?: string;
    status?: string;
    pinned?: boolean;
    featured?: boolean;
    author?: number;
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const queryString = queryParams.toString();
    const url = `/forum/posts/${queryString ? `?${queryString}` : ''}`;
    const response = await this.request(url);
    return response.data;
  }

  async getForumPost(postId: number): Promise<any> {
    const response = await this.request(`/forum/posts/${postId}/`);
    return response.data;
  }

  async createForumPost(data: {
    title: string;
    content: string;
    category?: number;
    tag_ids?: number[];
    is_public_visible?: boolean;
    allow_public_reply?: boolean;
    status?: string;
  }): Promise<any> {
    const response = await this.request('/forum/posts/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.data;
  }

  async updateForumPost(postId: number, data: {
    title?: string;
    content?: string;
    category?: number;
    tag_ids?: number[];
    is_public_visible?: boolean;
    allow_public_reply?: boolean;
    status?: string;
  }): Promise<any> {
    const response = await this.request(`/forum/posts/${postId}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    return response.data;
  }

  async deleteForumPost(postId: number): Promise<void> {
    await this.request(`/forum/posts/${postId}/`, {
      method: 'DELETE',
    });
  }

  async likeForumPost(postId: number): Promise<any> {
    const response = await this.request(`/forum/posts/${postId}/like/`, {
      method: 'POST',
    });
    return response.data;
  }

  async pinForumPost(postId: number): Promise<any> {
    const response = await this.request(`/forum/posts/${postId}/pin/`, {
      method: 'POST',
    });
    return response.data;
  }

  async featureForumPost(postId: number): Promise<any> {
    const response = await this.request(`/forum/posts/${postId}/feature/`, {
      method: 'POST',
    });
    return response.data;
  }

  async getForumPostReplies(postId: number, params?: {
    page?: number;
    page_size?: number;
    parent?: number;
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const queryString = queryParams.toString();
    const url = `/forum/replies/?post=${postId}${queryString ? `&${queryString}` : ''}`;
    const response = await this.request(url);
    return response.data;
  }

  async createForumReply(data: {
    content: string;
    post: number;
    parent_reply?: number;
    quoted_reply?: number;
    is_public_visible?: boolean;
  }): Promise<any> {
    const response = await this.request('/forum/replies/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.data;
  }

  async updateForumReply(replyId: number, data: {
    content?: string;
    is_public_visible?: boolean;
  }): Promise<any> {
    const response = await this.request(`/forum/replies/${replyId}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    return response.data;
  }

  async deleteForumReply(replyId: number): Promise<void> {
    await this.request(`/forum/replies/${replyId}/`, {
      method: 'DELETE',
    });
  }

  async likeForumReply(replyId: number): Promise<any> {
    const response = await this.request(`/forum/replies/${replyId}/like/`, {
      method: 'POST',
    });
    return response.data;
  }

  async uploadForumAttachment(file: File, postId?: number, replyId?: number): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (postId) {
      formData.append('post', postId.toString());
    }
    if (replyId) {
      formData.append('reply', replyId.toString());
    }

    const url = `${this.baseURL}/forum/attachments/`;
    const headers: HeadersInit = {};
    
    const token = this.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Upload failed: ${response.status}`);
    }

    return response.json();
  }

  async getForumNotifications(params?: {
    page?: number;
    page_size?: number;
    read?: boolean;
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const queryString = queryParams.toString();
    const url = `/forum/notifications/${queryString ? `?${queryString}` : ''}`;
    const response = await this.request(url);
    return response.data;
  }

  async markNotificationRead(notificationId: number): Promise<any> {
    const response = await this.request(`/forum/notifications/${notificationId}/read/`, {
      method: 'POST',
    });
    return response.data;
  }

  async markAllNotificationsRead(): Promise<any> {
    const response = await this.request('/forum/notifications/read-all/', {
      method: 'POST',
    });
    return response.data;
  }

  async getUnreadNotificationCount(): Promise<{ count: number }> {
    const response = await this.request<{ count: number }>('/forum/notifications/unread-count/');
    return response.data;
  }

  async getForumMentions(params?: {
    page?: number;
    page_size?: number;
    read?: boolean;
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const queryString = queryParams.toString();
    const url = `/forum/mentions/${queryString ? `?${queryString}` : ''}`;
    const response = await this.request(url);
    return response.data;
  }

  async markMentionRead(mentionId: number): Promise<any> {
    const response = await this.request(`/forum/mentions/${mentionId}/read/`, {
      method: 'POST',
    });
    return response.data;
  }
}

// Create and export API client instance
export const apiClient = new ApiClient(); 