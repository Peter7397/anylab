import React, { useEffect, useMemo, useState } from 'react';
import { apiClient } from '../../services/api';

const License: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [list, setList] = useState<any>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const isAdmin = useMemo(() => {
    // Simple check: decode JWT payload to see if user is staff if present in claims in future
    // For now, rely on list endpoint (admin-only) response to imply admin
    return !!list; 
  }, [list]);

  const loadData = async () => {
    setError(null);
    try {
      const [st, l] = await Promise.allSettled([
        apiClient.getLicenseStatus(),
        apiClient.listLicenses(),
      ]);
      if (st.status === 'fulfilled') setStatus(st.value);
      if (l.status === 'fulfilled') setList(l.value);
    } catch (e: any) {
      setError(e?.message || 'Failed to load license data');
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true); setError(null); setMessage(null);
    try {
      await apiClient.importLicense(file);
      setMessage('License imported successfully');
      setFile(null);
      await loadData();
    } catch (e: any) {
      setError(e?.message || 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  const onActivate = async (key: string) => {
    setLoading(true); setError(null); setMessage(null);
    try {
      await apiClient.activateLicense(key);
      setMessage('License activated');
      await loadData();
    } catch (e: any) {
      setError(e?.message || 'Activation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">License Management</h1>
        <p className="text-gray-600">View current license status and manage licenses.</p>
      </div>

      {status && (
        <div className="bg-white rounded-lg border p-4">
          <h2 className="text-lg font-semibold">Current Status</h2>
          <div className="mt-2 text-sm text-gray-700">
            <div><span className="font-medium">Valid:</span> {String(status.valid)}</div>
            <div><span className="font-medium">Type:</span> {status.license_type || '-'}</div>
            <div><span className="font-medium">Expiry:</span> {status.expiry_date || '-'}</div>
            {status.license_info && (
              <div className="mt-2">
                <span className="font-medium">Modules:</span>
                <div className="mt-1 flex flex-wrap gap-2">
                  {status.license_info.module_permissions?.map((m: string) => (
                    <span key={m} className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-xs border border-indigo-200">{m}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {message && (
        <div className="rounded bg-green-50 text-green-800 border border-green-200 p-3 text-sm">{message}</div>
      )}
      {error && (
        <div className="rounded bg-red-50 text-red-800 border border-red-200 p-3 text-sm">{error}</div>
      )}

      <div className="bg-white rounded-lg border p-4">
        <h2 className="text-lg font-semibold">Import License</h2>
        <form onSubmit={onImport} className="mt-3 flex items-center gap-3">
          <input type="file" accept=".lic,.json,.txt" onChange={(e) => setFile(e.target.files?.[0] || null)} className="block w-full text-sm" />
          <button type="submit" disabled={loading || !file} className={`px-4 py-2 rounded bg-indigo-600 text-white text-sm ${(!file||loading)?'opacity-60 cursor-not-allowed':''}`}>Import</button>
        </form>
        <p className="text-xs text-gray-500 mt-2">Any authenticated user can import a license. Only admins can view the full list and perform admin actions.</p>
      </div>

      {isAdmin && (
        <div className="bg-white rounded-lg border p-4">
          <h2 className="text-lg font-semibold">All Licenses</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-gray-600">
                  <th className="py-2 pr-4">Key</th>
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Company</th>
                  <th className="py-2 pr-4">Valid</th>
                  <th className="py-2 pr-4">Activated</th>
                  <th className="py-2 pr-4">Expiry</th>
                  <th className="py-2 pr-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {list?.licenses?.map((lic: any) => (
                  <tr key={lic.id} className="border-t">
                    <td className="py-2 pr-4 font-mono text-xs">{lic.license_key}</td>
                    <td className="py-2 pr-4">{lic.license_type}</td>
                    <td className="py-2 pr-4">{lic.company_name}</td>
                    <td className="py-2 pr-4">{String(lic.is_valid)}</td>
                    <td className="py-2 pr-4">{lic.activated ? 'Yes' : 'No'}</td>
                    <td className="py-2 pr-4">{lic.expiry_date || '-'}</td>
                    <td className="py-2 pr-4">
                      {!lic.activated && (
                        <button onClick={() => onActivate(lic.license_key)} disabled={loading} className={`px-3 py-1 rounded bg-green-600 text-white text-xs ${loading?'opacity-60 cursor-not-allowed':''}`}>Activate</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default License;



