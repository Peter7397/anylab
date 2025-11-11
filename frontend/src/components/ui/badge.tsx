import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'brand' | 'info' | 'warn' | 'danger' | 'neutral' | 'outline';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'brand', 
  className = '' 
}) => {
  const baseClasses = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium';
  
  const variantClasses = {
    brand: 'bg-primary-50 text-primary-800',
    info: 'bg-emerald-50 text-emerald-800',
    warn: 'bg-warning-50 text-warning-800',
    danger: 'bg-danger-50 text-danger-800',
    neutral: 'bg-gray-100 text-gray-800',
    outline: 'border border-gray-300 text-gray-700'
  } as const;

  return (
    <span className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
};
