import { Routes, Route, Navigate } from 'react-router-dom';
import { getToken } from './api';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Team from './pages/Team';
import VolunteerDetail from './pages/VolunteerDetail';
import Calendar from './pages/Calendar';
import Ratings from './pages/Ratings';
import SettingsPage from './pages/SettingsPage';
import './App.css';

function ProtectedRoute({ children }) {
  const token = getToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function AuthenticatedLayout({ children }) {
  return (
    <div className="dashboard-layout">
      <Sidebar />
      <div className="main-content">
        <div className="p-6 lg:p-8">{children}</div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AuthenticatedLayout>
              <Dashboard />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/team"
        element={
          <ProtectedRoute>
            <AuthenticatedLayout>
              <Team />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/team/:id"
        element={
          <ProtectedRoute>
            <AuthenticatedLayout>
              <VolunteerDetail />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/calendar"
        element={
          <ProtectedRoute>
            <AuthenticatedLayout>
              <Calendar />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ratings"
        element={
          <ProtectedRoute>
            <AuthenticatedLayout>
              <Ratings />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <AuthenticatedLayout>
              <SettingsPage />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
