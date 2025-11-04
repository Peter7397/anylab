import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../services/api';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If already logged in, redirect to dashboard
    const token = localStorage.getItem('anylab_token');
    if (token) {
      // Use replace to avoid adding to history, and prevent redirect loops
      navigate('/dashboard', { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      console.log('Login - Attempting to login...');
      const tokens = await apiClient.login({ username, password });
      console.log('Login - Login successful, tokens received:', !!tokens);
      
      // Verify token was stored
      const token = localStorage.getItem('anylab_token');
      console.log('Login - Token in localStorage:', !!token, token ? token.substring(0, 50) + '...' : 'none');
      
      if (!token) {
        throw new Error('Token was not stored in localStorage');
      }
      
      // Small delay to ensure localStorage is persisted
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Verify again after delay
      const tokenAfterDelay = localStorage.getItem('anylab_token');
      console.log('Login - Token after delay:', !!tokenAfterDelay);
      
      if (!tokenAfterDelay) {
        throw new Error('Token was lost after storage');
      }
      
      // Force page reload to trigger AuthContext reload
      console.log('Login - Redirecting to dashboard...');
      window.location.href = '/dashboard';
    } catch (err: any) {
      console.error('Login - Login failed:', err);
      const message = err?.message || 'Login failed. Please check your credentials and try again.';
      setError(message);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-gray-900">AnyLab</h1>
          <p className="text-sm text-gray-500">AI Next to Your Lab</p>
          <h2 className="text-xl font-semibold text-gray-900 mt-4">Sign in</h2>
          <p className="text-sm text-gray-500 mt-1">Enter your credentials to continue</p>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700 border border-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              placeholder="your.username"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full inline-flex justify-center items-center rounded-md bg-indigo-600 px-4 py-2 text-white font-medium shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            type="button"
            className="text-sm text-indigo-600 hover:text-indigo-700"
            onClick={() => alert('Please contact your administrator to reset your password.')}
          >
            Forgot your password?
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;


