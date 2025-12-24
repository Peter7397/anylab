import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Shield, Edit, Trash2, Search, Filter, MoreVertical, AlertCircle } from 'lucide-react';
import { apiClient } from '../../services/api';

interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  employee_id?: string;
  department?: string;
  position?: string;
  phone?: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  roles?: Role[];
}

interface Role {
  id: number;
  name: string;
  description: string;
  permissions: any;
  is_active: boolean;
  userCount?: number;
}

const UsersRoles: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedRoleIds, setSelectedRoleIds] = useState<Set<number>>(new Set());
  const [showResetModal, setShowResetModal] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // New user form state
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    department: '',
    position: '',
  });

  // Load data from API
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [usersData, rolesData] = await Promise.allSettled([
        apiClient.getUsers(),
        apiClient.getRoles(),
      ]);

      if (usersData.status === 'fulfilled') {
        const usersWithRoles = await Promise.all(
          usersData.value.map(async (user: any) => {
            try {
              const userRoles = await apiClient.getUserRoles(parseInt(user.id));
              return { ...user, roles: userRoles.map((ur: any) => ur.role) };
            } catch {
              return { ...user, roles: [] };
            }
          })
        );
        setUsers(usersWithRoles);
      }

      if (rolesData.status === 'fulfilled') {
        const rolesWithCounts = rolesData.value.map((role: any) => ({
          ...role,
          userCount: users.filter(u => u.roles?.some(r => r.id === role.id)).length
        }));
        setRoles(rolesWithCounts);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load users and roles');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUser.username || !newUser.password) {
      setError('Please fill in username and password');
      return;
    }

    try {
      setError(null);
      await apiClient.createUser(newUser);
      setShowAddModal(false);
      setNewUser({
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        department: '',
        position: '',
      });
      await loadData();
    } catch (err: any) {
      setError(err?.message || 'Failed to create user');
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await apiClient.deleteUser(parseInt(userId));
        await loadData();
      } catch (err: any) {
        setError(err?.message || 'Failed to delete user');
      }
    }
  };

  const handleAssignRole = async (userId: string, roleId: number) => {
    try {
      await apiClient.assignRole(parseInt(userId), roleId);
      await loadData();
    } catch (err: any) {
      setError(err?.message || 'Failed to assign role');
    }
  };

  const handleRemoveRole = async (userId: string, roleId: number) => {
    try {
      await apiClient.removeRole(parseInt(userId), roleId);
      await loadData();
    } catch (err: any) {
      setError(err?.message || 'Failed to remove role');
    }
  };

  const openEditUser = (user: User) => {
    setEditingUser(user);
    const currentRoleIds = new Set<number>((user.roles || []).map(r => r.id));
    setSelectedRoleIds(currentRoleIds);
    setShowEditModal(true);
  };

  const toggleSelectedRole = (roleId: number) => {
    setSelectedRoleIds(prev => {
      const next = new Set(prev);
      if (next.has(roleId)) next.delete(roleId); else next.add(roleId);
      return next;
    });
  };

  const saveUserRoles = async () => {
    if (!editingUser) return;
    try {
      setError(null);
      // Determine diffs
      const current = new Set<number>((editingUser.roles || []).map(r => r.id));
      const desired = selectedRoleIds;
      const toAdd: number[] = [];
      const toRemove: number[] = [];
      roles.forEach(role => {
        const hasNow = current.has(role.id);
        const wants = desired.has(role.id);
        if (!hasNow && wants) toAdd.push(role.id);
        if (hasNow && !wants) toRemove.push(role.id);
      });

      // Apply changes
      await Promise.all([
        ...toAdd.map(id => apiClient.assignRole(parseInt(editingUser.id), id)),
        ...toRemove.map(id => apiClient.removeRole(parseInt(editingUser.id), id))
      ]);

      setShowEditModal(false);
      setEditingUser(null);
      await loadData();
    } catch (err: any) {
      setError(err?.message || 'Failed to save roles');
    }
  };

  const openResetPassword = (user: User) => {
    setEditingUser(user);
    setNewPassword('');
    setConfirmPassword('');
    setShowResetModal(true);
  };

  const submitResetPassword = async () => {
    if (!editingUser) return;
    if (!newPassword || newPassword.length < 4) {
      setError('Password must be at least 4 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    try {
      setError(null);
      await apiClient.resetUserPassword(parseInt(editingUser.id), newPassword);
      setShowResetModal(false);
      setEditingUser(null);
    } catch (err: any) {
      setError(err?.message || 'Failed to reset password');
    }
  };

  // Filter users based on search and role
  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      `${user.first_name} ${user.last_name}`.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesRole = selectedRole === 'all' || 
      user.roles?.some(role => role.name.toLowerCase() === selectedRole.toLowerCase());

    return matchesSearch && matchesRole;
  });

  // Calculate stats
  const stats = {
    total: users.length,
    active: users.filter(u => u.is_active).length,
    inactive: users.filter(u => !u.is_active).length,
    rolesCount: roles.length,
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
      case 'Admin': return 'text-red-600 bg-red-100';
      case 'manager':
      case 'Manager': return 'text-blue-600 bg-blue-100';
      case 'technician':
      case 'Technician': return 'text-green-600 bg-green-100';
      case 'viewer':
      case 'Viewer': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive
      ? 'text-green-600 bg-green-100'
      : 'text-red-600 bg-red-100';
  };

  const getRoleIcon = () => <Shield size={16} />;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Users & Roles</h1>
          <p className="text-gray-600">Manage user accounts and role permissions</p>
        </div>
        <div className="flex space-x-3">
          <button 
            className="btn-primary"
            onClick={() => { setNewUser({ username: '', email: '', password: '', first_name: '', last_name: '', department: '', position: '' }); setShowAddModal(true); }}
          >
            <UserPlus size={16} className="mr-2" />
            Add User
          </button>
          <button className="btn-secondary">
            <Shield size={16} className="mr-2" />
            Manage Roles
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <AlertCircle className="text-red-600 mt-0.5 mr-3" size={20} />
          <div>
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="text-blue-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Users</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Users className="text-green-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Users</p>
              <p className="text-2xl font-bold text-gray-900">{stats.active}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-amber-100 rounded-lg">
              <Shield className="text-amber-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Roles</p>
              <p className="text-2xl font-bold text-gray-900">{stats.rolesCount}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <Users className="text-red-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Inactive</p>
              <p className="text-2xl font-bold text-gray-900">{stats.inactive}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Users</h2>
          <div className="flex space-x-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="text"
                placeholder="Search users..."
                className="input-field pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <select 
              className="input-field"
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
            >
              <option value="all">All Roles</option>
              {roles.map((role) => (
                <option key={role.id} value={role.name}>
                  {role.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {user.first_name} {user.last_name} ({user.username})
                      </div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.roles && user.roles.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {user.roles.map((role) => (
                          <span
                            key={role.id}
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(role.name)}`}
                          >
                            {role.name}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">No roles assigned</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(user.is_active)}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.department || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-3" onClick={() => openEditUser(user)}>
                      <Edit size={16} />
                    </button>
                    <button 
                      className="text-amber-600 hover:text-amber-800 mr-3"
                      onClick={() => openResetPassword(user)}
                    >
                      Reset PW
                    </button>
                    <button 
                      className="text-red-600 hover:text-red-900"
                      onClick={() => handleDeleteUser(user.id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Roles Section */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Roles & Permissions</h2>
          <button className="btn-secondary">
            <Shield size={16} className="mr-2" />
            Create Role
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {roles.map((role) => (
            <div key={role.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(role.name)}`}>
                    {getRoleIcon()}
                    <span className="ml-1">{role.name}</span>
                  </span>
                  <span className="ml-2 text-sm text-gray-500">
                    ({users.filter(u => u.roles?.some(r => r.id === role.id)).length} users)
                  </span>
                </div>
                <button className="text-gray-400 hover:text-gray-600">
                  <MoreVertical size={16} />
                </button>
              </div>
              
              <p className="text-sm text-gray-600 mb-3">{role.description || 'No description'}</p>
              
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Permissions:</h4>
                <div className="flex flex-wrap gap-1">
                  {role.permissions && typeof role.permissions === 'object' ? (
                    Object.keys(role.permissions).length > 0 ? (
                      Object.keys(role.permissions).map((key) => (
                        <span
                          key={key}
                          className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800"
                        >
                          {key}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-400">No specific permissions</span>
                    )
                  ) : (
                    <span className="text-xs text-gray-400">No permissions defined</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Add New User</h3>
              <form className="space-y-4" onSubmit={handleAddUser}>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Username *</label>
                  <input 
                    type="text" 
                    className="input-field"
                    name="new_username"
                    autoComplete="off"
                    value={newUser.username}
                    onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <input 
                    type="email" 
                    className="input-field"
                    name="new_email"
                    autoComplete="off"
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Password *</label>
                  <input 
                    type="password" 
                    className="input-field"
                    name="new_password"
                    autoComplete="new-password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">First Name</label>
                  <input 
                    type="text" 
                    className="input-field"
                    value={newUser.first_name}
                    onChange={(e) => setNewUser({...newUser, first_name: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Name</label>
                  <input 
                    type="text" 
                    className="input-field"
                    value={newUser.last_name}
                    onChange={(e) => setNewUser({...newUser, last_name: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Department</label>
                  <input 
                    type="text" 
                    className="input-field"
                    value={newUser.department}
                    onChange={(e) => setNewUser({...newUser, department: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Position</label>
                  <input 
                    type="text" 
                    className="input-field"
                    value={newUser.position}
                    onChange={(e) => setNewUser({...newUser, position: e.target.value})}
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary">
                    Add User
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Roles Modal */}
      {showEditModal && editingUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-[28rem] shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Edit Roles</h3>
              <p className="text-sm text-gray-600 mb-4">{editingUser.first_name} {editingUser.last_name} ({editingUser.username})</p>
              <div className="max-h-80 overflow-y-auto border rounded-md p-3">
                {roles.length === 0 && (
                  <div className="text-sm text-gray-500">No roles available</div>
                )}
                <ul className="space-y-2">
                  {roles.map(role => (
                    <li key={role.id} className="flex items-center justify-between">
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          className="h-4 w-4"
                          checked={selectedRoleIds.has(role.id)}
                          onChange={() => toggleSelectedRole(role.id)}
                        />
                        <span className="text-sm text-gray-800">{role.name}</span>
                      </label>
                      <span className="text-xs text-gray-500">{role.description || ''}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="flex justify-end space-x-3 mt-4">
                <button
                  type="button"
                  onClick={() => { setShowEditModal(false); setEditingUser(null); }}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={saveUserRoles}
                  className="btn-primary"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {showResetModal && editingUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Reset Password</h3>
              <p className="text-sm text-gray-600 mb-4">{editingUser.first_name} {editingUser.last_name} ({editingUser.username})</p>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">New Password</label>
                  <input
                    type="password"
                    className="input-field"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Confirm Password</label>
                  <input
                    type="password"
                    className="input-field"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-4">
                <button className="btn-secondary" onClick={() => { setShowResetModal(false); setEditingUser(null); }}>Cancel</button>
                <button className="btn-primary" onClick={submitResetPassword}>Save</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UsersRoles;
