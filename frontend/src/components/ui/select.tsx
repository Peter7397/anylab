import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

interface SelectProps {
  children: React.ReactNode;
  value?: string;
  onValueChange?: (value: string) => void;
  placeholder?: string;
  className?: string;
}

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

interface SelectContentProps {
  children: React.ReactNode;
}

interface SelectItemProps {
  children: React.ReactNode;
  value: string;
}

export const Select: React.FC<SelectProps> = ({ 
  children, 
  value, 
  onValueChange, 
  placeholder,
  className = '' 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedValue, setSelectedValue] = useState(value || '');
  const [selectedLabel, setSelectedLabel] = useState(placeholder || '');
  const selectRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleSelectItem = (event: CustomEvent) => {
      const { value: itemValue, label } = event.detail;
      setSelectedValue(itemValue);
      setSelectedLabel(label);
      setIsOpen(false);
      onValueChange?.(itemValue);
    };

    document.addEventListener('mousedown', handleClickOutside);
    window.addEventListener('select-item', handleSelectItem as EventListener);
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('select-item', handleSelectItem as EventListener);
    };
  }, [onValueChange]);

  return (
    <div ref={selectRef} className={`relative ${className}`}>
      <SelectTrigger onClick={() => setIsOpen(!isOpen)}>
        <span className={selectedValue ? 'text-gray-900' : 'text-gray-500'}>
          {selectedLabel}
        </span>
        <ChevronDown className="h-4 w-4" />
      </SelectTrigger>
      
      {isOpen && (
        <SelectContent>
          {children}
        </SelectContent>
      )}
    </div>
  );
};

export const SelectTrigger: React.FC<SelectTriggerProps> = ({ children, className = '', onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
    >
      {children}
    </button>
  );
};

export const SelectContent: React.FC<SelectContentProps> = ({ children }) => {
  return (
    <div className="absolute top-full z-50 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg">
      <div className="py-1">
        {children}
      </div>
    </div>
  );
};

export const SelectItem: React.FC<SelectItemProps> = ({ children, value }) => {
  const handleClick = () => {
    const event = new CustomEvent('select-item', { detail: { value, label: children } });
    window.dispatchEvent(event);
  };

  return (
    <button
      className="relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-gray-100 focus:bg-gray-100"
      onClick={handleClick}
    >
      {children}
    </button>
  );
};

export const SelectValue: React.FC<{ placeholder?: string }> = ({ placeholder }) => {
  return <span className="text-gray-500">{placeholder}</span>;
};
