// API Service Layer for OnLab Frontend
// This file handles all API communication with the Django backend

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';
const JWT_STORAGE_KEY = process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token';
const REFRESH_TOKEN_KEY = process.env.REACT_APP_REFRESH_TOKEN_KEY || 'onlab_refresh_token';

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
      const data = await response.json();

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
        throw new Error(data.message || `HTTP ${response.status}`);
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
    const response = await this.request<{ query: string; top_k: number; results: Array<{ title: string; chunk_index: number; content: string; similarity: number }>}>('/ai/vector/search/', {
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
    }>('/ai/rag/advanced/', {
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
    }>('/ai/rag/comprehensive/', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK, include_stats: includeStats }),
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
    return response.data;
  }

  async uploadDocument(file: File, title: string, description?: string, documentType?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) {
      formData.append('description', description);
    }
    if (documentType) {
      formData.append('document_type', documentType);
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