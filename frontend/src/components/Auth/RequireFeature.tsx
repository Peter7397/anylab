import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface RequireFeatureProps {
  feature: string;
  fallbackPath?: string;
  children: React.ReactNode;
}

const RequireFeature: React.FC<RequireFeatureProps> = ({ feature, fallbackPath = '/', children }) => {
  const { permissions, loading, user } = useAuth();

  // Show loading spinner while checking permissions
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          <p className="text-sm text-gray-500">Loading permissions...</p>
        </div>
      </div>
    );
  }

  const isStaff = !!user?.is_staff;
  const isSuperuser = (user as any)?.is_superuser ? true : false;
  const allowed = isSuperuser || isStaff || !!permissions?.features?.[feature];
  
  if (!allowed) {
    return <Navigate to={fallbackPath} replace />;
  }

  return <>{children}</>;
};

export default RequireFeature;


