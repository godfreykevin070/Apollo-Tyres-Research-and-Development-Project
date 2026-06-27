import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/Common/ProtectedRoute';
import Layout from './components/Layout/Layout';
import Login from './components/Auth/Login';
import UserDashboard from './components/Dashboard/UserDashboard';
import ManagerDashboard from './components/Dashboard/ManagerDashboard';
import ProjectList from './components/Projects/ProjectList';
import ProjectForm from './components/Projects/ProjectForm';
import ActivityLog from './components/Activity/ActivityLog';
import UserManagement from './components/Users/UserManagement';

import MF62 from './protocols/MF62';
import MF52 from './protocols/MF52';
import FTire from './protocols/FTire';
import CDTire from './protocols/CDTire';
import Custom from './protocols/Custom';
import Select from './protocols/Select';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Protocol Pages - No Layout (full page) */}
          <Route path="/mf" element={<ProtectedRoute><MF62 /></ProtectedRoute>} />
          <Route path="/mf52" element={<ProtectedRoute><MF52 /></ProtectedRoute>} />
          <Route path="/ftire" element={<ProtectedRoute><FTire /></ProtectedRoute>} />
          <Route path="/cdtire" element={<ProtectedRoute><CDTire /></ProtectedRoute>} />
          <Route path="/custom" element={<ProtectedRoute><Custom /></ProtectedRoute>} />
          <Route path="/select" element={<ProtectedRoute><Select /></ProtectedRoute>} />
          
          <Route element={<Layout />}>
            {/* Dashboard - Accessible by all authenticated users */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <UserDashboard />
                </ProtectedRoute>
              }
            />

            {/* Manager/Admin Dashboard */}
            <Route
              path="/manager-dashboard"
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager']}>
                  <ManagerDashboard />
                </ProtectedRoute>
              }
            />

            {/* Projects */}
            <Route
              path="/projects"
              element={
                <ProtectedRoute>
                  <ProjectList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/new"
              element={
                <ProtectedRoute>
                  <ProjectForm />
                </ProtectedRoute>
              }
            />

            {/* Activity Log - All authenticated users */}
            <Route
              path="/activity-log"
              element={
                <ProtectedRoute>
                  <ActivityLog />
                </ProtectedRoute>
              }
            />

            {/* User Management - Admin and Manager only */}
            <Route
              path="/users"
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager']}>
                  <UserManagement />
                </ProtectedRoute>
              }
            />

            {/* Admin Panel - Admin only */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <div className="p-6">
                    <h1 className="text-2xl font-bold text-gray-800">Admin Panel</h1>
                    <p className="text-gray-500 mt-2">Admin-specific controls and settings</p>
                  </div>
                </ProtectedRoute>
              }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;