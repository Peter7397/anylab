import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helpText?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ label, helpText, error, className = '', ...props }) => {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <input
        className={`input ${error ? 'border-danger-300 focus:border-danger-500 focus:ring-danger-500' : ''} ${className}`}
        {...props}
      />
      {error ? (
        <p className="text-xs text-danger-600">{error}</p>
      ) : helpText ? (
        <p className="text-xs text-gray-500">{helpText}</p>
      ) : null}
    </div>
  );
};

export default Input;
