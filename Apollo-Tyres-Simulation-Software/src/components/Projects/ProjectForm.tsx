import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { 
  ArrowLeft,
  Save,
  X,
  Check,
  AlertCircle
} from 'lucide-react';

interface FormData {
  project_name: string;
  region: string;
  department: string;
  tyre_size: string;
  protocol: string;
}

const ProjectForm: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<FormData>({
    project_name: '',
    region: '',
    department: '',
    tyre_size: '',
    protocol: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.project_name.trim()) {
      newErrors.project_name = 'Project name is required';
    } else if (formData.project_name.length < 3) {
      newErrors.project_name = 'Project name must be at least 3 characters';
    }

    if (!formData.region) {
      newErrors.region = 'Please select a region';
    }

    if (!formData.department) {
      newErrors.department = 'Please select a department';
    }

    if (!formData.tyre_size.trim()) {
      newErrors.tyre_size = 'Tyre size is required';
    }

    if (!formData.protocol) {
      newErrors.protocol = 'Please select a protocol';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError('');

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await api.post('/projects', {
        ...formData,
        status: 'Not Started',
      });

      if (response.data.success) {
        const protocolMap: Record<string, string> = {
          'MF62': '/mf',
          'MF52': '/mf52',
          'FTire': '/ftire',
          'CDTire': '/cdtire',
          'Custom': '/custom',
        };

        const protocolPath = protocolMap[formData.protocol] || '/select';
        navigate(`${protocolPath}?projectId=${response.data.id}`);
      } else {
        setSubmitError(response.data.message || 'Failed to create project');
      }
    } catch (error: any) {
      console.error('Error creating project:', error);
      setSubmitError(
        error.response?.data?.message || 
        error.message || 
        'An error occurred while creating the project'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name as keyof FormData]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const protocolOptions = [
    { value: 'MF62', label: 'MF 6.2' },
    { value: 'MF52', label: 'MF 5.2' },
    { value: 'FTire', label: 'FTire' },
    { value: 'CDTire', label: 'CDTire' },
    { value: 'Custom', label: 'Custom' },
  ];

  const regionOptions = [
    { value: 'APMEA', label: 'APMEA' },
    { value: 'EUROPE', label: 'Europe' },
    { value: 'USA', label: 'USA' },
  ];

  const departmentOptions = [
    { value: 'PCR', label: 'PCR' },
    { value: 'TBR', label: 'TBR' },
  ];

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/projects')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">New Project</h1>
            <p className="text-gray-500 mt-1">Create a new tyre simulation project</p>
          </div>
        </div>
        <button
          type="submit"
          form="project-form"
          disabled={isSubmitting}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Creating...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Create Project
            </>
          )}
        </button>
      </div>

      {/* Form */}
      <form id="project-form" onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="space-y-6">
          {/* Project Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="project_name"
              value={formData.project_name}
              onChange={handleChange}
              placeholder="Enter project name"
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 ${
                errors.project_name ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.project_name && (
              <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.project_name}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Region */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Region <span className="text-red-500">*</span>
              </label>
              <select
                name="region"
                value={formData.region}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 ${
                  errors.region ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Select Region</option>
                {regionOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {errors.region && (
                <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {errors.region}
                </p>
              )}
            </div>

            {/* Department */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Department <span className="text-red-500">*</span>
              </label>
              <select
                name="department"
                value={formData.department}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 ${
                  errors.department ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Select Department</option>
                {departmentOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {errors.department && (
                <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {errors.department}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Tyre Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tyre Size <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="tyre_size"
                value={formData.tyre_size}
                onChange={handleChange}
                placeholder="e.g., 235/45R17"
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 ${
                  errors.tyre_size ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.tyre_size && (
                <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {errors.tyre_size}
                </p>
              )}
            </div>

            {/* Protocol */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Protocol <span className="text-red-500">*</span>
              </label>
              <select
                name="protocol"
                value={formData.protocol}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 ${
                  errors.protocol ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Select Protocol</option>
                {protocolOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {errors.protocol && (
                <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {errors.protocol}
                </p>
              )}
            </div>
          </div>

          {/* Submit Error */}
          {submitError && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Error</p>
                <p className="text-sm">{submitError}</p>
              </div>
            </div>
          )}

          {/* Project Info */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Note:</span> After creating the project, you'll be redirected to the protocol-specific page to enter simulation parameters.
            </p>
          </div>
        </div>
      </form>
    </div>
  );
};

export default ProjectForm;