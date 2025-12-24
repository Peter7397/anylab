import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation('admin');
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
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [showRoleMenu, setShowRoleMenu] = useState<number | null>(null);
  
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

  // New role form state
  const [newRole, setNewRole] = useState({
    name: '',
    description: '',
    permissions: {
      features: {
        'ai.rag': false,
        'knowledge.view': false,
        'admin': false,
        'documents.upload': false,
        'documents.bulk_import': false,
        'help_portal.edit': false,
        'forum.view': false,
        'forum.post': false,
        'forum.reply': false,
        'forum.edit': false,
        'forum.moderate': false,
        'forum.manage': false,
      }
    }
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
      setError(err?.message || t('failedToLoadUsersAndRoles'));
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUser.username || !newUser.password) {
      setError(t('pleaseFillInUsernameAndPassword'));
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
      setError(err?.message || t('failedToCreateUser'));
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (window.confirm(t('confirmDeleteUser'))) {
      try {
        await apiClient.deleteUser(parseInt(userId));
        await loadData();
      } catch (err: any) {
        setError(err?.message || t('failedToDeleteUser'));
      }
    }
  };

  const handleAssignRole = async (userId: string, roleId: number) => {
    try {
      await apiClient.assignRole(parseInt(userId), roleId);
      await loadData();
    } catch (err: any) {
      setError(err?.message || t('failedToAssignRole'));
    }
  };

  const handleRemoveRole = async (userId: string, roleId: number) => {
    try {
      await apiClient.removeRole(parseInt(userId), roleId);
      await loadData();
    } catch (err: any) {
      setError(err?.message || t('failedToRemoveRole'));
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
      setError(err?.message || t('failedToSaveRoles'));
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
      setError(t('passwordMustBeAtLeast4Characters'));
      return;
    }
    if (newPassword !== confirmPassword) {
      setError(t('passwordsDoNotMatch'));
      return;
    }
    try {
      setError(null);
      await apiClient.resetUserPassword(parseInt(editingUser.id), newPassword);
      setShowResetModal(false);
      setEditingUser(null);
    } catch (err: any) {
      setError(err?.message || t('failedToResetPassword'));
    }
  };

  // Role management functions
  const openCreateRole = () => {
    setEditingRole(null);
    setNewRole({
      name: '',
      description: '',
      permissions: {
        features: {
          'ai.rag': false,
          'knowledge.view': false,
          'admin': false,
          'documents.upload': false,
          'documents.bulk_import': false,
          'help_portal.edit': false,
          'forum.view': false,
          'forum.post': false,
          'forum.reply': false,
          'forum.edit': false,
          'forum.moderate': false,
          'forum.manage': false,
        }
      }
    });
    setShowRoleModal(true);
  };

  const openEditRole = (role: Role) => {
    setEditingRole(role);
    setNewRole({
      name: role.name,
      description: role.description || '',
      permissions: role.permissions || {
        features: {}
      }
    });
    setShowRoleModal(true);
    setShowRoleMenu(null);
  };

  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRole.name.trim()) {
      setError(t('pleaseFillInRoleName'));
      return;
    }
    try {
      setError(null);
      await apiClient.createRole(newRole);
      setShowRoleModal(false);
      setNewRole({
        name: '',
        description: '',
        permissions: {
          features: {
            'ai.rag': false,
            'knowledge.view': false,
            'admin': false,
            'documents.upload': false,
            'documents.bulk_import': false,
            'help_portal.edit': false,
            'forum.view': false,
            'forum.post': false,
            'forum.reply': false,
            'forum.edit': false,
            'forum.moderate': false,
            'forum.manage': false,
          }
        }
      });
      await loadData();
    } catch (err: any) {
      setError(err?.message || t('failedToCreateRole'));
    }
  };

  const handleUpdateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRole || !newRole.name.trim()) {
      setError(t('pleaseFillInRoleName'));
      return;
    }
    try {
      setError(null);
      await apiClient.updateRole(editingRole.id, newRole);
      setShowRoleModal(false);
      setEditingRole(null);
      await loadData();
    } catch (err: any) {
      setError(err?.message || t('failedToUpdateRole'));
    }
  };

  const handleDeleteRole = async (roleId: number) => {
    if (!window.confirm(t('confirmDeleteRole'))) {
      return;
    }
    try {
      setError(null);
      await apiClient.deleteRole(roleId);
      setShowRoleMenu(null);
      await loadData();
    } catch (err: any) {
      setError(err?.message || t('failedToDeleteRole'));
    }
  };

  const togglePermission = (feature: string) => {
    setNewRole(prev => ({
      ...prev,
      permissions: {
        ...prev.permissions,
        features: {
          ...prev.permissions.features,
          [feature]: !prev.permissions.features[feature as keyof typeof prev.permissions.features]
        }
      }
    }));
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
          <h1 className="text-2xl font-bold text-gray-900">{t('usersRoles')}</h1>
          <p className="text-gray-600">{t('manageUserAccountsAndRolePermissions')}</p>
        </div>
        <div className="flex space-x-3">
          <button 
            className="btn-primary"
            onClick={() => { setNewUser({ username: '', email: '', password: '', first_name: '', last_name: '', department: '', position: '' }); setShowAddModal(true); }}
          >
            <UserPlus size={16} className="mr-2" />
            {t('addUser')}
          </button>
          <button 
            className="btn-secondary"
            onClick={openCreateRole}
          >
            <Shield size={16} className="mr-2" />
            {t('manageRoles')}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <AlertCircle className="text-red-600 mt-0.5 mr-3" size={20} />
          <div>
            <p className="text-sm font-medium text-red-800">{t('error')}</p>
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
              <p className="text-sm font-medium text-gray-600">{t('totalUsers')}</p>
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
              <p className="text-sm font-medium text-gray-600">{t('activeUsers')}</p>
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
              <p className="text-sm font-medium text-gray-600">{t('roles')}</p>
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
              <p className="text-sm font-medium text-gray-600">{t('inactive')}</p>
              <p className="text-2xl font-bold text-gray-900">{stats.inactive}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">{t('users')}</h2>
          <div className="flex space-x-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="text"
                placeholder={t('searchUsers')}
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
              <option value="all">{t('allRoles')}</option>
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
                  {t('user')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('role')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('status')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('department')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('actions')}
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
                      <span className="text-xs text-gray-400">{t('noRolesAssigned')}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(user.is_active)}`}>
                      {user.is_active ? t('active') : t('inactive')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.department || t('notAvailable')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-3" onClick={() => openEditUser(user)}>
                      <Edit size={16} />
                    </button>
                    <button 
                      className="text-amber-600 hover:text-amber-800 mr-3"
                      onClick={() => openResetPassword(user)}
                    >
                      {t('resetPassword')}
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
          <h2 className="text-lg font-semibold text-gray-900">{t('rolesAndPermissions')}</h2>
          <button 
            className="btn-secondary"
            onClick={openCreateRole}
          >
            <Shield size={16} className="mr-2" />
            {t('createRole')}
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
                    ({t('usersCount', { count: users.filter(u => u.roles?.some(r => r.id === role.id)).length })})
                  </span>
                </div>
                <div className="relative">
                  <button 
                    className="text-gray-400 hover:text-gray-600"
                    onClick={() => setShowRoleMenu(showRoleMenu === role.id ? null : role.id)}
                  >
                    <MoreVertical size={16} />
                  </button>
                  {showRoleMenu === role.id && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                      <div className="py-1">
                        <button
                          onClick={() => openEditRole(role)}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                        >
                          <Edit size={16} className="mr-3" />
                          {t('editRole')}
                        </button>
                        <button
                          onClick={() => handleDeleteRole(role.id)}
                          className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                        >
                          <Trash2 size={16} className="mr-3" />
                          {t('deleteRole')}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mb-3">{role.description || t('noDescription')}</p>
              
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">{t('permissions')}:</h4>
                <div className="flex flex-wrap gap-1">
                  {role.permissions && role.permissions.features ? (
                    Object.keys(role.permissions.features).length > 0 ? (
                      Object.entries(role.permissions.features)
                        .filter(([_, enabled]) => enabled)
                        .map(([feature, _]) => (
                          <span
                            key={feature}
                            className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {feature}
                          </span>
                        ))
                    ) : (
                      <span className="text-xs text-gray-400">{t('noSpecificPermissions')}</span>
                    )
                  ) : (
                    <span className="text-xs text-gray-400">{t('noPermissionsDefined')}</span>
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
              <h3 className="text-lg font-medium text-gray-900 mb-4">{t('addNewUser')}</h3>
              <form className="space-y-4" onSubmit={handleAddUser}>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('username')} *</label>
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
                  <label className="block text-sm font-medium text-gray-700">{t('email')}</label>
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
                  <label className="block text-sm font-medium text-gray-700">{t('password')} *</label>
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
                  <label className="block text-sm font-medium text-gray-700">{t('firstName')}</label>
                  <input 
                    type="text" 
                    className="input-field"
                    value={newUser.first_name}
                    onChange={(e) => setNewUser({...newUser, first_name: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('lastName')}</label>
                  <input 
                    type="text" 
                    className="input-field"
                    value={newUser.last_name}
                    onChange={(e) => setNewUser({...newUser, last_name: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('department')}</label>
                  <input 
                    type="text" 
                    className="input-field"
                    value={newUser.department}
                    onChange={(e) => setNewUser({...newUser, department: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('position')}</label>
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
                    {t('cancel')}
                  </button>
                  <button type="submit" className="btn-primary">
                    {t('addUser')}
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
              <h3 className="text-lg font-medium text-gray-900 mb-2">{t('editRoles')}</h3>
              <p className="text-sm text-gray-600 mb-4">{editingUser.first_name} {editingUser.last_name} ({editingUser.username})</p>
              <div className="max-h-80 overflow-y-auto border rounded-md p-3">
                {roles.length === 0 && (
                  <div className="text-sm text-gray-500">{t('noRolesAvailable')}</div>
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
                  {t('cancel')}
                </button>
                <button
                  type="button"
                  onClick={saveUserRoles}
                  className="btn-primary"
                >
                  {t('save')}
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
              <h3 className="text-lg font-medium text-gray-900 mb-2">{t('resetPassword')}</h3>
              <p className="text-sm text-gray-600 mb-4">{editingUser.first_name} {editingUser.last_name} ({editingUser.username})</p>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('newPassword')}</label>
                  <input
                    type="password"
                    className="input-field"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('confirmPassword')}</label>
                  <input
                    type="password"
                    className="input-field"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-4">
                <button className="btn-secondary" onClick={() => { setShowResetModal(false); setEditingUser(null); }}>{t('cancel')}</button>
                <button className="btn-primary" onClick={submitResetPassword}>{t('save')}</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Role Management Modal */}
      {showRoleModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingRole ? t('editRole') : t('createRole')}
              </h3>
              <form className="space-y-4" onSubmit={editingRole ? handleUpdateRole : handleCreateRole}>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('role')} {t('name')} *</label>
                  <input 
                    type="text" 
                    className="input-field"
                    value={newRole.name}
                    onChange={(e) => setNewRole({...newRole, name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('description')}</label>
                  <textarea 
                    className="input-field"
                    rows={3}
                    value={newRole.description}
                    onChange={(e) => setNewRole({...newRole, description: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('permissions')}</label>
                  <div className="border border-gray-200 rounded-lg p-4 space-y-2 max-h-64 overflow-y-auto">
                    {Object.keys(newRole.permissions.features).map((feature) => (
                      <label key={feature} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={newRole.permissions.features[feature as keyof typeof newRole.permissions.features] || false}
                          onChange={() => togglePermission(feature)}
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-4">
                  <button
                    type="button"
                    onClick={() => { setShowRoleModal(false); setEditingRole(null); }}
                    className="btn-secondary"
                  >
                    {t('cancel')}
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                  >
                    {editingRole ? t('update') : t('create')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Click outside to close role menu */}
      {showRoleMenu !== null && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowRoleMenu(null)}
        />
      )}
    </div>
  );
};

export default UsersRoles;
