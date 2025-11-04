import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { apiClient, MergedPermissions, User } from '../services/api';

interface AuthContextValue {
  permissions: MergedPermissions | null;
  loading: boolean;
  refreshPermissions: () => Promise<void>;
  user: User | null;
  error: string | null;
  clearAuth: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  permissions: null,
  loading: true,
  refreshPermissions: async () => {},
  user: null,
  error: null,
  clearAuth: () => {},
});

// Export function to notify AuthContext of token refresh
let authContextRefreshCallback: (() => Promise<void>) | null = null;

export const notifyAuthTokenRefreshed = () => {
  if (authContextRefreshCallback) {
    authContextRefreshCallback();
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [permissions, setPermissions] = useState<MergedPermissions | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  const clearAuth = useCallback(() => {
    setPermissions(null);
    setUser(null);
    setError(null);
    localStorage.removeItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'anylab_token');
    localStorage.removeItem(process.env.REACT_APP_REFRESH_TOKEN_KEY || 'anylab_refresh_token');
  }, []);

  const load = useCallback(async () => {
    try {
      setError(null);
      const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'anylab_token');
      if (!token) {
        setPermissions(null);
        setUser(null);
        setLoading(false);
        return;
      }

      // Try to load permissions and user profile
      const perms = await apiClient.getMyPermissions();
      setPermissions(perms);
      const profile = await apiClient.getCurrentUser();
      setUser(profile);
    } catch (e: any) {
      // If authentication fails, clear tokens and auth state
      console.error('Failed to load auth data:', e);
      
      // Check if it's an authentication error (401)
      if (e?.message?.includes('Authentication') || e?.message?.includes('401')) {
        clearAuth();
        setError('Session expired. Please log in again.');
      } else {
        setError('Failed to load user permissions. Please try refreshing the page.');
        // Don't clear auth on other errors - might be network issue
      }
    } finally {
      setLoading(false);
    }
  }, [clearAuth]);

  // Register refresh callback for API client
  useEffect(() => {
    authContextRefreshCallback = load;
    return () => {
      authContextRefreshCallback = null;
    };
  }, [load]);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    permissions,
    loading,
    refreshPermissions: load,
    user,
    error,
    clearAuth,
  }), [permissions, loading, user, error, load, clearAuth]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);


