import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../services/api';

export type ChatChannel = 'chat' | 'rag_basic' | 'rag' | 'rag_comprehensive' | 'rag_graph' | 'troubleshooting';

export interface UnifiedMessage {
  id: number;
  channel: ChatChannel;
  thread_id: string;
  role: 'user' | 'assistant';
  content: string;
  metadata?: any;
  created_at: string;
}

export function useUnifiedChatHistory(initialLimit: number = 200) {
  const [history, setHistory] = useState<UnifiedMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (params?: { limit?: number; channel?: ChatChannel; thread_id?: string }) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.getUnifiedHistory({ limit: params?.limit ?? initialLimit, channel: params?.channel, thread_id: params?.thread_id });
      setHistory(Array.isArray(data) ? data.map(d => ({ ...d, channel: d.channel as ChatChannel })) : []);
    } catch (e: any) {
      setError(e?.message || 'Failed to load history');
    } finally {
      setIsLoading(false);
    }
  }, [initialLimit]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const recordUserPrompt = useCallback(async (channel: ChatChannel, content: string, threadId?: string, metadata?: any) => {
    const res = await apiClient.createChatMessage({ channel, role: 'user', content, thread_id: threadId, metadata });
    // Optimistically update history
    setHistory(prev => [{ ...res, channel: res.channel as ChatChannel }, ...prev].slice(0, initialLimit));
    return res.thread_id as string;
  }, [initialLimit]);

  const crossPostToChannel = useCallback((channel: ChatChannel, content: string) => {
    const payload = { channel, content, ts: Date.now() };
    localStorage.setItem('anylab_cross_post', JSON.stringify(payload));
  }, []);

  return {
    history,
    isLoading,
    error,
    refresh,
    recordUserPrompt,
    crossPostToChannel,
  } as const;
}


