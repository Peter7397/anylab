import React from 'react';

interface PanelProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
  children?: React.ReactNode;
}

export const Panel: React.FC<PanelProps> = ({ title, subtitle, actions, className = '', children }) => {
  return (
    <div className={`panel ${className}`}>
      {(title || actions) && (
        <div className="panel-header">
          <div>
            {title && <h3 className="text-sm font-semibold text-gray-900">{title}</h3>}
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="panel-body">
        {children}
      </div>
    </div>
  );
};

export default Panel;
