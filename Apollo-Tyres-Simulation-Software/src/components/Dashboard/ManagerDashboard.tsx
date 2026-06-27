import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import type { Project, User, ActivityLog } from '../../types';
import {
  Users,
  FolderOpen,
  CheckCircle,
  Clock,
  TrendingUp,
  Activity,
  UserPlus,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import UserForm from '../../components/Users/UserForm';

const ManagerDashboard: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [showUserForm, setShowUserForm] = useState(false);
  const [stats, setStats] = useState({
    totalProjects: 0,
    totalUsers: 0,
    completedProjects: 0,
    activeUsers: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [projectsRes, usersRes, activitiesRes] = await Promise.all([
        api.get('/projects'),
        api.get('/manager/users'),
        api.get('/activity-log?limit=5'),
      ]);

      const projectData = projectsRes.data;
      const userData = usersRes.data.users || [];
      const activityData = activitiesRes.data.logs || [];

      setProjects(projectData);
      setUsers(userData);
      setActivities(activityData);

      const completed = projectData.filter((p: Project) => p.status === 'Completed').length;
      const activeUsers = userData.filter((u: User) => {
        if (!u.last_login) return false;
        const daysSinceLogin = (Date.now() - new Date(u.last_login).getTime()) / (1000 * 60 * 60 * 24);
        return daysSinceLogin <= 7;
      }).length;

      setStats({
        totalProjects: projectData.length,
        totalUsers: userData.length,
        completedProjects: completed,
        activeUsers: activeUsers,
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const statCards = [
    {
      label: 'Total Projects',
      value: stats.totalProjects,
      icon: FolderOpen,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'Total Engineers',
      value: stats.totalUsers,
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      label: 'Completed Projects',
      value: stats.completedProjects,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      label: 'Active Users (7d)',
      value: stats.activeUsers,
      icon: Clock,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
  ];

  const getStatusBadge = (status: string) => {
    const classes = {
      'Completed': 'bg-green-100 text-green-700',
      'In Progress': 'bg-yellow-100 text-yellow-700',
      'Not Started': 'bg-gray-100 text-gray-700',
      'Archived': 'bg-red-100 text-red-700',
    };
    return classes[status as keyof typeof classes] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              Welcome, {user?.name}! 👋
            </h1>
            <p className="text-gray-500 mt-1">Monitor system performance and manage your team.</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowUserForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              <UserPlus className="w-4 h-4" />
              Add Engineer
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
              <TrendingUp className="w-4 h-4 text-gray-400" />
            </div>
            <p className="text-2xl font-bold text-gray-800 mt-3">{stat.value}</p>
            <p className="text-sm text-gray-500">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">Recent Activity</h2>
        </div>
        <div className="p-6">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="w-8 h-8 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : activities.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No recent activity</p>
          ) : (
            <div className="space-y-4">
              {activities.map((activity) => (
                <div key={activity.id} className="flex items-start gap-4">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <Activity className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800">{activity.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">
                        {activity.user_name || activity.user_email}
                      </span>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-500">
                        {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    activity.status === 'success' 
                      ? 'bg-green-100 text-green-700'
                      : activity.status === 'failed'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {activity.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* User Form Modal */}
      {showUserForm && (
        <UserForm
          onClose={() => setShowUserForm(false)}
          onSuccess={() => {
            setShowUserForm(false);
            loadDashboardData();
          }}
        />
      )}
    </div>
  );
};

export default ManagerDashboard;