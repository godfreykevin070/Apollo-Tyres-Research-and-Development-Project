import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  PlusCircle,
  Activity,
  Users,
  History,
  HelpCircle,
  LogOut,
  UserCog,
} from 'lucide-react';
import type { User } from '../../types';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  user: User | null;
}

const Sidebar: React.FC<SidebarProps> = ({ user }) => {
  const { logout } = useAuth();

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/projects', icon: FolderOpen, label: 'My Projects' },
    { path: '/projects/new', icon: PlusCircle, label: 'New Project' },
    { path: '/activity-log', icon: Activity, label: 'Activity Log' },
    { path: '/history', icon: History, label: 'Project History' },
  ];

  // Admin and Manager can see user management
  if (user?.role === 'admin' || user?.role === 'manager') {
    navItems.splice(4, 0, { path: '/users', icon: Users, label: 'User Management' });
  }

  // Admin can see admin panel
  if (user?.role === 'admin') {
    navItems.splice(5, 0, { path: '/admin', icon: UserCog, label: 'Admin Panel' });
  }

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">AT</span>
          </div>
          <span className="text-lg font-bold text-gray-800">Apollo Tyres</span>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-red-50 text-red-600'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="text-sm font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-gray-600">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">
              {user?.name || 'User'}
            </p>
            <p className="text-xs text-gray-500 capitalize">{user?.role || 'User'}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;