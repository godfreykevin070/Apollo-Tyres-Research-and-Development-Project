import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { 
  ArrowLeft, 
  Play, 
  FileText, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  RefreshCw,
  Eye
} from 'lucide-react';

interface RunData {
  number_of_runs: number;
  tests: string;
  p: string;
  l: string;
  job: string;
  old_job: string;
  template_tydex: string;
  tydex_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  run_start_time?: string;
  run_end_time?: string;
  run_duration_seconds?: number;
}

const Select: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const projectId = searchParams.get('projectId');
  
  const [runs, setRuns] = useState<RunData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [runningJobs, setRunningJobs] = useState<Set<number>>(new Set());
  const [error, setError] = useState('');

  useEffect(() => {
    if (projectId) {
      loadRuns();
      loadRunStatuses();
    } else {
      setError('Project ID is required');
      setIsLoading(false);
    }
  }, [projectId]);

  const loadRuns = async () => {
    setIsLoading(true);
    try {
      const response = await api.get(`/projects/${projectId}/matrix`);

      if (response.data.success) {
        setRuns(response.data.rows || []);
      } else {
        setError('Failed to load run data');
      }
    } catch (error: any) {
      console.error('Error loading runs:', error);
      setError(error.response?.data?.message || 'Failed to load run data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadRunStatuses = async () => {
    try {
      const response = await api.get(`/projects/${projectId}/run-status`);

      if (response.data.success) {
        const runStatuses = response.data.runs; 

        setRuns(prev =>
          prev.map(run => {
            const latest = runStatuses.find(
              (r: any) => r.number_of_runs === run.number_of_runs
            );

            return latest
              ? {
                  ...run,
                  status:
                    latest.run_status === "not_started"
                      ? "pending"
                      : latest.run_status,
                  run_start_time: latest.run_start_time,
                  run_end_time: latest.run_end_time,
                  run_duration_seconds: latest.run_duration_seconds,
                }
              : run;
          })
        );
      }
    } catch (error) {
      console.error("Error loading run statuses:", error);
    }
  };

  const handleRunSimulation = async (runNumber: number) => {
    setRunningJobs(prev => new Set(prev).add(runNumber));
    setError('');

    try {
      const response = await api.post('/resolve-job-dependencies', {
        projectId,
        runNumber
      });

      if (response.data.success) {
        // Update status to running
        setRuns(prev => prev.map(run => 
          run.number_of_runs === runNumber 
            ? { ...run, status: 'running' } 
            : run
        ));
        
        // Poll for status updates
        pollRunStatus();
      } else {
        setError(response.data.message || 'Failed to start simulation');
        setRuns(prev => prev.map(run => 
          run.number_of_runs === runNumber 
            ? { ...run, status: 'failed' } 
            : run
        ));
      }
    } catch (error: any) {
      console.log(error.response?.status);
      console.log(error.response?.data);
      console.log(error.response?.headers);
      console.error('Error running simulation:', error);
      setError(error.response?.data?.message || 'Failed to start simulation');
      setRuns(prev => prev.map(run => 
        run.number_of_runs === runNumber 
          ? { ...run, status: 'failed' } 
          : run
      ));
    } finally {
      setRunningJobs(prev => {
        const newSet = new Set(prev);
        newSet.delete(runNumber);
        return newSet;
      });
    }
  };

  const pollRunStatus = async () => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await api.get(
          `/projects/${projectId}/run-status`
        );

        if (response.data.success) {
          const updatedRuns = response.data.runs;

          setRuns(prev =>
            prev.map(run => {
              const latest = updatedRuns.find(
                (r: any) => r.number_of_runs === run.number_of_runs
              );

              return latest
                ? {
                    ...run,
                    status:
                      latest.run_status === "not_started"
                        ? "pending"
                        : latest.run_status,
                    run_start_time: latest.run_start_time,
                    run_end_time: latest.run_end_time,
                    run_duration_seconds: latest.run_duration_seconds,
                  }
                : run;
            })
          );

          const allFinished = updatedRuns.every(
            (r: any) =>
              r.run_status === "completed" ||
              r.run_status === "failed" ||
              r.run_status === "not_started"
          );

          if (!allFinished && attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 5000);
          }
        }
      } catch (err) {
        console.error("Polling failed:", err);

        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 5000);
        }
      }
    };

    poll();
  };

  const handleGenerateTydex = async (runNumber: number) => {
    try {
      const run = runs.find(r => r.number_of_runs === runNumber);
      if (!run) return;

      const response = await api.post('/generate-tydex', {
        projectId,
        runNumber,
        rowData: run
      });

      if (response.data.success) {
        alert('Tydex file generated successfully');
        await loadRunStatuses();
      } else {
        setError(response.data.message || 'Failed to generate Tydex');
      }
    } catch (error: any) {
      console.error("Status:", error.response?.status);
      console.error("Data:", error.response?.data);
      console.error("Headers:", error.response?.headers);

      setError(
        error.response?.data?.detail ||
        error.response?.data?.message ||
        "Failed to generate Tydex"
      );
    }
  };

  const getStatusBadge = (status: string) => {
    const classes = {
      pending: 'bg-gray-100 text-gray-700',
      running: 'bg-yellow-100 text-yellow-700 animate-pulse',
      completed: 'bg-green-100 text-green-700',
      failed: 'bg-red-100 text-red-700',
    };
    return classes[status as keyof typeof classes] || classes.pending;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'running': return <Clock className="w-4 h-4 animate-spin" />;
      case 'failed': return <AlertCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

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
              <h1 className="text-2xl font-bold text-gray-800">Run Simulations</h1>
              <p className="text-sm text-gray-500">Project ID: {projectId}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadRunStatuses}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button
              onClick={() => navigate(`/projects/${projectId}`)}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <Eye className="w-4 h-4" />
              View Project
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

        {/* Run Status Summary */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
            <p className="text-2xl font-bold text-gray-800">{runs.length}</p>
            <p className="text-sm text-gray-500">Total Tests</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
            <p className="text-2xl font-bold text-green-600">
              {runs.filter(r => r.status === 'completed').length}
            </p>
            <p className="text-sm text-gray-500">Completed</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
            <p className="text-2xl font-bold text-yellow-600">
              {runs.filter(r => r.status === 'running').length}
            </p>
            <p className="text-sm text-gray-500">Running</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
            <p className="text-2xl font-bold text-red-600">
              {runs.filter(r => r.status === 'failed').length}
            </p>
            <p className="text-sm text-gray-500">Failed</p>
          </div>
        </div>

        {/* Runs Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Test</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">L</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {runs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      No test runs found
                    </td>
                  </tr>
                ) : (
                  runs.map((run) => (
                    <tr key={run.number_of_runs} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-500">{run.number_of_runs}</td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-800">{run.tests}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{run.p}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{run.l}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{run.job}</td>
                      <td className="px-6 py-4">
                        <span className={`text-xs px-2 py-1 rounded-full flex items-center gap-1 ${getStatusBadge(run.status)}`}>
                          {getStatusIcon(run.status)}
                          {run.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {run.status === 'pending' && (
                            <button
                              onClick={() => handleRunSimulation(run.number_of_runs)}
                              disabled={runningJobs.has(run.number_of_runs)}
                              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors flex items-center gap-1 disabled:opacity-50"
                            >
                              <Play className="w-3 h-3" />
                              Run
                            </button>
                          )}
                          {run.status === 'completed' && (
                            <button
                              onClick={() => handleGenerateTydex(run.number_of_runs)}
                              className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm transition-colors flex items-center gap-1"
                            >
                              <FileText className="w-3 h-3" />
                              Tydex
                            </button>
                          )}
                          {run.status === 'failed' && (
                            <button
                              onClick={() => handleRunSimulation(run.number_of_runs)}
                              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm transition-colors flex items-center gap-1"
                            >
                              <RefreshCw className="w-3 h-3" />
                              Retry
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Select;