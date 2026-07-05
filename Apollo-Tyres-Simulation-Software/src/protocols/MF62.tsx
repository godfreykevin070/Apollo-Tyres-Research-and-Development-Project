import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { ArrowLeft, Save, Upload } from 'lucide-react';

interface ParameterData {
  p1: string;
  p2: string;
  p3: string;
  l1: string;
  l2: string;
  l3: string;
  vel: string;
  ia: string;
  sa: string;
  sr: string;
  rimWidth: string;
  rimDiameter: string;
  nominalWidth: string;
  outerDiameter: string;
  aspectRatio: string;
}

const MF62: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const projectId = searchParams.get('projectId');
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [meshFile, setMeshFile] = useState<File | null>(null);
  const [protocolProjects, setProtocolProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [parameters, setParameters] = useState<ParameterData>({
    p1: '', p2: '', p3: '',
    l1: '', l2: '', l3: '',
    vel: '', ia: '', sa: '', sr: '',
    rimWidth: '', rimDiameter: '', nominalWidth: '', outerDiameter: '',
    aspectRatio: ''
  });
  const protocol = "MF62";

  useEffect(() => {
    if (projectId) {
      loadInputs();
    }
  }, [projectId]);

  const loadInputs = async () => {
    try {
      const projectsResponse = await api.get(`/projects/protocol/${protocol}`);
      setProtocolProjects(projectsResponse.data.projects);

    } catch (err) {
      console.error(err);
    }
  };

  const handleParameterChange = (key: string, value: string) => {
    setParameters(prev => ({ ...prev, [key]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setMeshFile(e.target.files[0]);
    }
  };

  const applySavedInputs = () => {
    const selected = protocolProjects.find(
        p => p.id === selectedProjectId
    );

    if (!selected) return;

    let inputs = selected.inputs;

    // Parse JSON if stored as string
    if (typeof inputs === "string") {
        inputs = JSON.parse(inputs);
    }

    setParameters(inputs);
  };

  const validateParameters = (): boolean => {
    const required = ['p1', 'p2', 'p3', 'l1', 'l2', 'l3', 'vel', 'ia', 'sa', 'sr', 
                      'rimWidth', 'rimDiameter', 'nominalWidth', 'outerDiameter', 'aspectRatio'];
    const missing = required.filter(key => !parameters[key as keyof ParameterData]);
    
    if (missing.length > 0) {
      setError(`Please fill in all required fields: ${missing.join(', ')}`);
      return false;
    }
    setError('');
    return true;
  };

  const handleSubmit = async () => {
    if (!validateParameters()) return;

    if (!projectId) {
      setError("Project ID is missing");
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      // 1. Save project inputs
      await api.put(`/projects/${projectId}/inputs`, {
        inputs: parameters,
      });

      // 2. Generate parameter files
      await api.post("/generate-parameters", {
          ...parameters,
          protocol,
          projectId: projectId,
      });

      // 3. Upload mesh file if selected
      if (meshFile) {
        const formData = new FormData();

        formData.append("meshFile", meshFile);
        formData.append("projectId", projectId!);

        await api.post("/upload-mesh-file", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
      }

      // 4. Read MF5pt2.xlsx from protocol directory and store into mf52_data
      const storeResponse = await api.post("/store-mf62-data");

      if (!storeResponse.data.success) {
        throw new Error("Failed to import Excel data.");
      }

      // 5. Copy scratch table -> project table
      const matrixResponse = await api.post("/store-project-matrix", {
        projectId: Number(projectId),
        protocol: protocol,
      });

      if (!matrixResponse.data.success) {
        throw new Error("Failed to save matrix data.");
      }

      // 6. Process project
      const processResponse = await api.post("/process-mf62", {
        projectId: Number(projectId),
        parameters,
      });

      if (processResponse.data.success) {
        navigate(`/select?projectId=${projectId}`);
      } else {
        setError(processResponse.data.message || "Failed to process MF62.");
      }
    } catch (error: any) {
      console.error(error);

      setError(
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        "An unexpected error occurred."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const parameterGroups = [
    {
      title: 'Pressure',
      fields: [
        { key: 'p1', label: 'P1', placeholder: 'Enter P1 value in psi' },
        { key: 'p2', label: 'P2', placeholder: 'Enter P2 value in psi' },
        { key: 'p3', label: 'P3', placeholder: 'Enter P3 value in psi' },
      ]
    },
    {
      title: 'Load',
      fields: [
        { key: 'l1', label: 'L1', placeholder: 'Enter L1 value in Kg' },
        { key: 'l2', label: 'L2', placeholder: 'Enter L2 value in Kg' },
        { key: 'l3', label: 'L3', placeholder: 'Enter L3 value in Kg' },
      ]
    },
    {
      title: 'Speed & Angles',
      fields: [
        { key: 'vel', label: 'VEL', placeholder: 'Enter velocity in kmph' },
        { key: 'ia', label: 'IA', placeholder: 'Enter IA value in degree' },
        { key: 'sa', label: 'SA', placeholder: 'Enter SA value in degree' },
        { key: 'sr', label: 'SR', placeholder: 'Enter SR value in %' },
      ]
    },
    {
      title: 'Tyre Dimensions',
      fields: [
        { key: 'rimWidth', label: 'RW', placeholder: 'Enter RW value in mm' },
        { key: 'rimDiameter', label: 'RD', placeholder: 'Enter RD value in mm' },
        { key: 'nominalWidth', label: 'NW', placeholder: 'Enter NW value in mm' },
        { key: 'outerDiameter', label: 'OD', placeholder: 'Enter OD value in mm' },
        { key: 'aspectRatio', label: 'AR', placeholder: 'Enter AR value in %' },
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/projects')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">MF 6.2 Protocol</h1>
              <p className="text-sm text-gray-500">Project ID: {projectId || 'New Project'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Submit
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Parameters */}
          <div className="lg:col-span-2 space-y-6">
            {parameterGroups.map((group) => (
              <div key={group.title} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">{group.title}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {group.fields.map((field) => (
                    <div key={field.key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {field.label}
                      </label>
                      <input
                        type="text"
                        value={parameters[field.key as keyof ParameterData] || ''}
                        onChange={(e) => handleParameterChange(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Mesh File Upload */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Mesh File</h3>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  type="file"
                  id="meshFile"
                  accept=".inp"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="meshFile"
                  className="cursor-pointer flex flex-col items-center gap-2"
                >
                  <Upload className="w-8 h-8 text-gray-400" />
                  <span className="text-sm text-gray-600">
                    {meshFile ? meshFile.name : 'Click to upload mesh file (.inp)'}
                  </span>
                  <span className="text-xs text-gray-400">Drag and drop or click to browse</span>
                </label>
              </div>
            </div>
          </div>

          {/* Apply Inputs */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 top-6">
              <h2 className="text-xl font-semibold mb-6">
                Project Details
              </h2>
              <div className="mt-6">
                <label className="block text-sm font-medium mb-2">
                    Previous MF62 Projects
                </label>
                <select
                    value={selectedProjectId ?? ""}
                    onChange={(e)=>
                        setSelectedProjectId(Number(e.target.value))
                    }
                    className="w-full border rounded-lg p-2"
                >
                    <option value="">
                        Select Project
                    </option>
                    {protocolProjects.map(project => (
                        <option
                            key={project.id}
                            value={project.id}
                        >
                            {project.project_name}
                        </option>
                    ))}
                </select>
            </div>
              <div className="mt-8">
                <button
                  onClick={applySavedInputs}
                  disabled={!selectedProjectId}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-lg py-3"
                >
                  Apply Saved Inputs
                </button>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
};

export default MF62;