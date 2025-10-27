// API Service Layer for AnyLab Frontend
// This file handles all API communication with the Django backend

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';
const JWT_STORAGE_KEY = process.env.REACT_APP_JWT_STORAGE_KEY || 'anylab_token';
const REFRESH_TOKEN_KEY = process.env.REACT_APP_REFRESH_TOKEN_KEY || 'anylab_refresh_token';

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
  is_active: boolean;
}

export interface System {
  id: string;
  name: string;
  ip: string;
  os: string;
  lastLogin: string;
  status: 'online' | 'warning' | 'offline';
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
    localStorage.setItem(JWT_STORAGE_KEY, token);
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

    return headers;
  }

  // Make API request
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
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
          // Token expired, try to refresh
          const refreshed = await this.refreshToken();
          if (refreshed) {
            // Retry the original request
            return this.request(endpoint, options);
          } else {
            // Refresh failed, redirect to login
            this.logout();
            throw new Error('Authentication failed');
          }
        }
        throw new Error(data.message || data.error || `HTTP ${response.status}`);
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

  // Refresh authentication token
  private async refreshToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseURL}/token/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        this.setAuthToken(data.access);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    return false;
  }

  // Authentication Methods
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await this.request<AuthTokens>('/token/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    this.setAuthToken(response.data.access);
    this.setRefreshToken(response.data.refresh);

    return response.data;
  }

  logout(): void {
    this.removeAuthToken();
    this.removeRefreshToken();
    // Redirect to login page
    window.location.href = '/login';
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.request<User>('/users/me/');
    return response.data;
  }

  // Health Check
  async healthCheck(): Promise<any> {
    const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/health/`);
    return response.json();
  }

  // Users API
  async getUsers(): Promise<User[]> {
    const response = await this.request<User[]>('/users/');
    return response.data;
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

  async deleteUser(id: number): Promise<void> {
    await this.request(`/users/${id}/`, {
      method: 'DELETE',
    });
  }

  // Roles API
  async getRoles(): Promise<any[]> {
    const response = await this.request('/users/roles/');
    return response.data as any[];
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
    const response = await this.request(`/users/${userId}/roles/`);
    return response.data as any[];
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

  // Chat with Ollama (Qwen)
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
    const response = await this.request('/admin/licenses/status/');
    return response.data;
  }

  async listLicenses(): Promise<any> {
    const response = await this.request('/admin/licenses/');
    return response.data;
  }

  async importLicense(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('license_file', file);
    
    const url = `${this.baseURL}/admin/licenses/import/`;
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
      throw new Error(errorData.error || `Import failed: ${response.status}`);
    }

    return response.json();
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

    const url = `${this.baseURL}/ai/pdfs/upload/`;
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

    const url = `${this.baseURL}/ai/documents/upload/`;
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
      body: JSON.stringify({ document_id: docId, metadata_updates: metadataUpdates }),
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

  async searchDocuments(query: string, searchType: 'title' | 'content' | 'both' = 'both', documentType: string = 'all'): Promise<any> {
    const response = await this.request('/ai/documents/search/', {
      method: 'POST',
      body: JSON.stringify({ query, search_type: searchType, document_type: documentType }),
    });
    return response.data;
  }

  // Performance monitoring
  async getPerformanceStats(): Promise<any> {
    const response = await this.request('/ai/performance/stats/');
    return response.data;
  }
}

// Create and export API client instance
export const apiClient = new ApiClient(); 