import React from 'react';

interface PlaceholderComponentProps {
  title: string;
  description?: string;
}

const PlaceholderComponent: React.FC<PlaceholderComponentProps> = ({ title, description }) => {
  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 mb-4">
            <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
          <p className="text-gray-500 mb-6">
            {description || `This ${title.toLowerCase()} monitoring page is under development.`}
          </p>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">
              This page will include comprehensive monitoring features, charts, and real-time data visualization.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlaceholderComponent;


