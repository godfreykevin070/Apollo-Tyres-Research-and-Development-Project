import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import type { Project } from '../../types';
import { 
  FolderOpen, 
  Plus, 
  Search, 
  ChevronLeft, 
  ChevronRight,
  Eye,
  Edit,
  Trash2,
  CheckCircle,
  Clock,
  AlertCircle,
  Archive,
  Filter,
  Grid,
  List,
  RefreshCw
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

const ProjectList: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [filteredProjects, setFilteredProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [protocolFilter, setProtocolFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [itemsPerPage] = useState(12);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [projects, searchTerm, statusFilter, protocolFilter]);

  const loadProjects = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/projects');
      setProjects(response.data || []);
    } catch (error) {
      console.error('Error loading projects:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...projects];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(p =>
        p.project_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.id.toString().includes(searchTerm) ||
        p.protocol.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(p => p.status === statusFilter);
    }

    // Protocol filter
    if (protocolFilter !== 'all') {
      filtered = filtered.filter(p => p.protocol === protocolFilter);
    }

    // Sort by created date (newest first)
    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    setFilteredProjects(filtered);
  };

  const handleDeleteProject = async (projectId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this project?')) return;

    try {
      await api.delete(`/projects/${projectId}`);
      await loadProjects();
    } catch (error) {
      console.error('Error deleting project:', error);
      alert('Failed to delete project');
    }
  };

  const handleViewProject = (projectId: number) => {
    navigate(`/projects/${projectId}`);
  };

  const handleEditProject = (projectId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    // Get the project to determine its protocol
    const project = projects.find(p => p.id === projectId);
    if (!project) {
      alert('Project not found');
      return;
    }

    // Navigate to the appropriate protocol input page based on status and protocol
    const status = project.status?.toLowerCase() || '';
    const protocol = project.protocol || '';

    // If project is Completed, go to select page (view only)
    if (status === 'completed') {
      navigate(`/select?projectId=${projectId}`);
      return;
    }

    // Otherwise, go to the protocol input page
    const protocolMap: Record<string, string> = {
      'MF62': '/mf',
      'MF52': '/mf52',
      'FTire': '/ftire',
      'CDTire': '/cdtire',
      'Custom': '/custom',
    };

    const protocolPath = protocolMap[protocol];
    if (protocolPath) {
      navigate(`${protocolPath}?projectId=${projectId}`);
    } else {
      // Fallback to select page if protocol not recognized
      navigate(`/select?projectId=${projectId}`);
    }
  };

  const handleContinueProject = (projectId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    const project = projects.find(p => p.id === projectId);
    if (!project) {
      alert('Project not found');
      return;
    }

    const status = project.status?.toLowerCase() || '';
    const protocol = project.protocol || '';

    // If project is Completed or In Progress, go to select page
    if (status === 'completed' || status === 'in progress') {
      navigate(`/select?projectId=${projectId}`);
      return;
    }

    // If Not Started, go to protocol input page
    const protocolMap: Record<string, string> = {
      'MF62': '/mf',
      'MF52': '/mf52',
      'FTire': '/ftire',
      'CDTire': '/cdtire',
      'Custom': '/custom',
    };

    const protocolPath = protocolMap[protocol];
    if (protocolPath) {
      navigate(`${protocolPath}?projectId=${projectId}`);
    } else {
      navigate(`/select?projectId=${projectId}`);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Completed':
        return CheckCircle;
      case 'In Progress':
        return Clock;
      case 'Archived':
        return Archive;
      default:
        return AlertCircle;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'In Progress':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'Archived':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      default:
        return 'bg-blue-100 text-blue-700 border-blue-200';
    }
  };

  const getProtocolColor = (protocol: string) => {
    const colors: Record<string, string> = {
      'MF62': 'bg-purple-100 text-purple-700',
      'MF52': 'bg-indigo-100 text-indigo-700',
      'FTire': 'bg-orange-100 text-orange-700',
      'CDTire': 'bg-red-100 text-red-700',
      'Custom': 'bg-teal-100 text-teal-700',
    };
    return colors[protocol] || 'bg-gray-100 text-gray-700';
  };

  const totalPages = Math.ceil(filteredProjects.length / itemsPerPage);
  const paginatedProjects = filteredProjects.slice(
    (page - 1) * itemsPerPage,
    page * itemsPerPage
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">My Projects</h1>
          <p className="text-gray-500 mt-1">Manage and track all your projects</p>
        </div>
        <button
          onClick={() => navigate('/projects/new')}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Project
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
          <p className="text-2xl font-bold text-gray-800">{projects.length}</p>
          <p className="text-sm text-gray-500">Total Projects</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
          <p className="text-2xl font-bold text-green-600">
            {projects.filter(p => p.status === 'Completed').length}
          </p>
          <p className="text-sm text-gray-500">Completed</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
          <p className="text-2xl font-bold text-yellow-600">
            {projects.filter(p => p.status === 'In Progress').length}
          </p>
          <p className="text-sm text-gray-500">In Progress</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
          <p className="text-2xl font-bold text-blue-600">
            {projects.filter(p => p.status === 'Not Started').length}
          </p>
          <p className="text-sm text-gray-500">Not Started</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="all">All Status</option>
            <option value="Not Started">Not Started</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
            <option value="Archived">Archived</option>
          </select>

          <select
            value={protocolFilter}
            onChange={(e) => setProtocolFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="all">All Protocols</option>
            <option value="MF62">MF 6.2</option>
            <option value="MF52">MF 5.2</option>
            <option value="FTire">FTire</option>
            <option value="CDTire">CDTire</option>
            <option value="Custom">Custom</option>
          </select>

          <button
            onClick={loadProjects}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>

          <div className="flex gap-1 ml-auto">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'grid' ? 'bg-red-100 text-red-600' : 'hover:bg-gray-100'
              }`}
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'list' ? 'bg-red-100 text-red-600' : 'hover:bg-gray-100'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Projects */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center border border-gray-200">
          <FolderOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No projects found</p>
          <button
            onClick={() => navigate('/projects/new')}
            className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Create your first project
          </button>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {paginatedProjects.map((project) => {
            const StatusIcon = getStatusIcon(project.status);
            const isCompleted = project.status === 'Completed';
            const isArchived = project.status === 'Archived';
            const isInProgress = project.status === 'In Progress';
            
            return (
              <div
                key={project.id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => handleViewProject(project.id)}
              >
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-gray-800 truncate">
                        {project.project_name}
                      </h3>
                      <p className="text-xs text-gray-500">ID: #{project.id}</p>
                    </div>
                    <div className="flex gap-1 ml-2">
                      {!isCompleted && !isArchived && (
                        <button
                          onClick={(e) => handleEditProject(project.id, e)}
                          className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
                          title="Edit Project"
                        >
                          <Edit className="w-3.5 h-3.5 text-gray-500" />
                        </button>
                      )}
                      <button
                        onClick={(e) => handleDeleteProject(project.id, e)}
                        className="p-1 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete Project"
                      >
                        <Trash2 className="w-3.5 h-3.5 text-red-500" />
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(project.status)}`}>
                      <StatusIcon className="w-3 h-3 inline mr-1" />
                      {project.status}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getProtocolColor(project.protocol)}`}>
                      {project.protocol}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-1 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <span className="text-gray-400">Region:</span>
                      <span className="text-gray-700">{project.region}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-gray-400">Department:</span>
                      <span className="text-gray-700">{project.department}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-gray-400">Tyre Size:</span>
                      <span className="text-gray-700">{project.tyre_size}"</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-gray-400">Created:</span>
                      <span className="text-gray-700">
                        {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
                      </span>
                    </div>
                  </div>

                  {/* Action Button */}
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleContinueProject(project.id, e);
                      }}
                      className={`w-full px-3 py-1.5 text-sm rounded-lg transition-colors ${
                        isCompleted || isInProgress
                          ? 'bg-blue-600 hover:bg-blue-700 text-white'
                          : 'bg-green-600 hover:bg-green-700 text-white'
                      }`}
                    >
                      {isCompleted ? 'View Results' : isInProgress ? 'Continue' : 'Start Project'}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Protocol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Region</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedProjects.map((project) => {
                  const StatusIcon = getStatusIcon(project.status);
                  const isCompleted = project.status === 'Completed';
                  const isArchived = project.status === 'Archived';
                  const isInProgress = project.status === 'In Progress';
                  
                  return (
                    <tr
                      key={project.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleViewProject(project.id)}
                    >
                      <td className="px-6 py-4 text-sm text-gray-500">#{project.id}</td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-800">
                        {project.project_name}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getProtocolColor(project.protocol)}`}>
                          {project.protocol}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(project.status)}`}>
                          <StatusIcon className="w-3 h-3 inline mr-1" />
                          {project.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">{project.region}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {format(new Date(project.created_at), 'MMM d, yyyy')}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-2">
                          {!isCompleted && !isArchived && (
                            <button
                              onClick={(e) => handleEditProject(project.id, e)}
                              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
                              title="Edit Project"
                            >
                              <Edit className="w-4 h-4 text-gray-500" />
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleContinueProject(project.id, e);
                            }}
                            className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                              isCompleted || isInProgress
                                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                                : 'bg-green-600 hover:bg-green-700 text-white'
                            }`}
                          >
                            {isCompleted ? 'View' : isInProgress ? 'Continue' : 'Start'}
                          </button>
                          <button
                            onClick={(e) => handleDeleteProject(project.id, e)}
                            className="p-1 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete Project"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {((page - 1) * itemsPerPage) + 1} to {Math.min(page * itemsPerPage, filteredProjects.length)} of {filteredProjects.length}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-4 py-2 text-sm text-gray-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectList;