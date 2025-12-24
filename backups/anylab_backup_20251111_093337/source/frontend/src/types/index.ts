export interface System {
  id: string;
  name: string;
  ip: string;
  os: string;
  lastLogin: string;
  status: 'online' | 'offline' | 'warning';
}

export interface Log {
  id: string;
  timestamp: string;
  source: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  aiTag?: 'critical' | 'warning' | 'info';
}

export interface KnowledgeDocument {
  id: string;
  name: string;
  type: 'pdf' | 'url';
  dateAdded: string;
  status: 'indexed' | 'failed' | 'processing';
  url?: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: string;
  sources?: string[] | Array<{
    id?: any;
    title?: string;
    filename?: string;
    page_number?: number;
    chunk_index?: number;
    file_size?: number;
    uploaded_file_id?: number;
    content?: string;
    similarity?: number;
    download_url?: string;
  }>;
  searchStats?: {
    total_results?: number;
    response_length?: number;
    query_type?: string;
    avg_relevance_score?: number;
    unique_sources?: number;
    context_characters?: number;
    search_method?: string;
  };
}

export interface MaintenanceTask {
  id: string;
  title: string;
  description: string;
  scheduledDate: string;
  type: 'sql' | 'service' | 'reboot';
  status: 'pending' | 'completed' | 'failed';
}

export interface ResourceMetrics {
  cpu: number;
  ram: number;
  disk: number;
  timestamp: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'viewer';
}

export type AIMode = 'performance' | 'lightweight';

export interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: string;
} 