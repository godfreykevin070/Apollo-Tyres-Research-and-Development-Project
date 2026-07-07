import React from 'react';

interface Field {
  key: string;
  label: string;
  placeholder: string;
  required?: boolean;
  type?: 'text' | 'number';
  pattern?: string;
}

interface ParameterInputProps {
  title: string;
  description?: string;
  fields: Field[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  errors?: Record<string, string>;
  columns?: 1 | 2 | 3;
  className?: string;
}

const ParameterInput: React.FC<ParameterInputProps> = ({
  title,
  description,
  fields,
  values,
  onChange,
  errors = {},
  columns = 2,
  className = '',
}) => {
  const getGridCols = () => {
    switch (columns) {
      case 1: return 'grid-cols-1';
      case 3: return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3';
      default: return 'grid-cols-1 sm:grid-cols-2';
    }
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
        {description && (
          <p className="text-sm text-gray-500 mt-1">{description}</p>
        )}
      </div>

      <div className={`grid ${getGridCols()} gap-4`}>
        {fields.map((field) => {
          const value = values[field.key] || '';
          const error = errors[field.key];
          const isRequired = field.required !== false;

          return (
            <div key={field.key} className="space-y-1">
              <label 
                htmlFor={`param-${field.key}`}
                className="block text-sm font-medium text-gray-700"
              >
                {field.label}
                {isRequired && <span className="text-red-500 ml-1">*</span>}
              </label>
              <input
                id={`param-${field.key}`}
                type={field.type || 'text'}
                value={value}
                onChange={(e) => onChange(field.key, e.target.value)}
                placeholder={field.placeholder}
                pattern={field.pattern}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors ${
                  error ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {error && (
                <p className="text-xs text-red-500 mt-1">{error}</p>
              )}
              {!error && field.pattern && (
                <p className="text-xs text-gray-400 mt-1">
                  Format: {field.pattern}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ParameterInput;