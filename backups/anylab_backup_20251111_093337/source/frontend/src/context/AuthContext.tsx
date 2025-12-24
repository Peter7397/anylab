import React, { createContext, useContext, useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { apiClient, MergedPermissions, User } from '../services/api';
import { backendHealth } from '../services/backendHealth';

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
    localStorage.removeItem('anylab_token');
    localStorage.removeItem('anylab_refresh_token');
  }, []);

  const load = useCallback(async () => {
    try {
      setError(null);
      const token = localStorage.getItem('anylab_token');
      console.log('AuthContext - Token found:', !!token);
      if (!token) {
        console.log('AuthContext - No token, clearing auth state');
        setPermissions(null);
        setUser(null);
        setLoading(false);
        return;
      }

      // Check backend health before attempting API calls
      const isHealthy = await backendHealth.checkHealth();
      if (!isHealthy) {
        console.log('AuthContext - Backend is unhealthy, skipping API call');
        connectionErrorRef.current = true;
        setError('Backend server is not responding. Please check if the backend is running.');
        setLoading(false);
        return;
      }

      // Try to load permissions and user profile
      console.log('AuthContext - Loading permissions...');
      const perms = await apiClient.getMyPermissions();
      console.log('AuthContext - Permissions loaded:', perms);
      setPermissions(perms);
      
      console.log('AuthContext - Loading user profile...');
      const profile = await apiClient.getCurrentUser();
      console.log('AuthContext - User profile loaded:', profile);
      setUser(profile);
      
      // Mark backend as healthy after successful connection
      backendHealth.markHealthy();
      connectionErrorRef.current = false;
    } catch (e: any) {
      // If authentication fails, clear tokens and auth state
      console.error('AuthContext - Failed to load auth data:', e);
      
      // Check if it's an authentication error (401)
      if (e?.message?.includes('Authentication') || e?.message?.includes('401')) {
        console.log('AuthContext - Authentication error, clearing auth');
        clearAuth();
        setError('Session expired. Please log in again.');
        connectionErrorRef.current = false;
        backendHealth.markHealthy(); // Backend is up, just auth issue
      } else if (e?.message?.includes('Failed to fetch') || e?.message?.includes('CONNECTION_REFUSED') || e?.message?.includes('NetworkError')) {
        // Connection error - backend is down
        console.log('AuthContext - Connection error, marking backend as unhealthy');
        backendHealth.markUnhealthy();
        connectionErrorRef.current = true;
        setError('Cannot connect to server. The backend may be down or not running.');
        // Don't clear auth on connection errors - backend might come back
      } else {
        console.log('AuthContext - Non-auth error, keeping token but showing error');
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

  // Track connection errors to prevent infinite polling
  const connectionErrorRef = useRef<boolean>(false);
  const lastAttemptRef = useRef<number>(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const backoffDelayRef = useRef<number>(1000); // Start with 1 second

  // Reload when token changes (e.g., after login)
  useEffect(() => {
    const checkToken = async () => {
      const token = localStorage.getItem('anylab_token');
      
      // If backend is unhealthy, don't poll at all
      if (!backendHealth.getHealthStatus()) {
        console.log('AuthContext - Backend is unhealthy, skipping token check');
        // Still check occasionally (every 30 seconds) to see if backend comes back
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = setInterval(checkToken, 30000);
        }
        return;
      }
      
      // If we have connection errors, use exponential backoff
      const now = Date.now();
      if (connectionErrorRef.current && (now - lastAttemptRef.current < backoffDelayRef.current)) {
        return; // Skip if we're in backoff period
      }
      
      if (token && !user && !loading) {
        console.log('AuthContext - Token detected but no user, reloading...');
        lastAttemptRef.current = now;
        
        try {
          await load();
          // Success - reset backoff
          backoffDelayRef.current = 1000;
          connectionErrorRef.current = false;
          // Restore normal polling interval
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = setInterval(checkToken, 1000);
          }
        } catch (error) {
          // Failure - increase backoff (exponential, max 30 seconds)
          backoffDelayRef.current = Math.min(backoffDelayRef.current * 2, 30000);
          connectionErrorRef.current = true;
          // Slow down polling
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = setInterval(checkToken, backoffDelayRef.current);
          }
        }
      }
    };
    
    // Check immediately
    checkToken();
    
    // Also listen for storage events (in case token is set in another tab/window)
    window.addEventListener('storage', checkToken);
    
    // Poll for token changes (for same-tab login) - start with normal frequency
    intervalRef.current = setInterval(checkToken, 1000);
    
    return () => {
      window.removeEventListener('storage', checkToken);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [user, loading, load]);

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


