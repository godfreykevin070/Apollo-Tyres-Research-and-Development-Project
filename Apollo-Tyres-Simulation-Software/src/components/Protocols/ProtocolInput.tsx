import React from 'react';

interface Field {
  key: string;
  label: string;
  placeholder: string;
  required?: boolean;
}

interface ProtocolInputProps {
  title: string;
  fields: Field[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  errors?: Record<string, string>;
}

const ProtocolInput: React.FC<ProtocolInputProps> = ({
  title,
  fields,
  values,
  onChange,
  errors = {}
}) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {fields.map((field) => (
          <div key={field.key}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <input
              type="text"
              value={values[field.key] || ''}
              onChange={(e) => onChange(field.key, e.target.value)}
              placeholder={field.placeholder}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 ${
                errors[field.key] ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors[field.key] && (
              <p className="mt-1 text-xs text-red-500">{errors[field.key]}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProtocolInput;