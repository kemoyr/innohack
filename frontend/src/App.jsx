import { Routes, Route, Navigate } from 'react-router-dom';
import { getToken, getUser } from './api';
import Sidebar from './components/Sidebar';
import PublicNavbar from './components/PublicNavbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Team from './pages/Team';
import VolunteerDetail from './pages/VolunteerDetail';
import Calendar from './pages/Calendar';
import Ratings from './pages/Ratings';
import SettingsPage from './pages/SettingsPage';
import ModerationPage from './pages/ModerationPage';
import MyEvents from './pages/MyEvents';
import './App.css';

function PublicLayout({ children }) {
  return (
    <div className="min-h-screen">
      <PublicNavbar />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">{children}</div>
    </div>
  );
}

function CoordinatorLayout({ children }) {
  return (
    <div className="dashboard-layout">
      <Sidebar />
      <div className="main-content">
        <div className="p-6 lg:p-8">{children}</div>
      </div>
    </div>
  );
}

function CoordinatorRoute({ children }) {
  const token = getToken();
  const user = getUser();
  if (!token || !user || user.role !== 'coordinator') {
    return <Navigate to="/login" replace />;
  }
  return <CoordinatorLayout>{children}</CoordinatorLayout>;
}

function AuthRoute({ children }) {
  const token = getToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  const user = getUser();
  if (user?.role === 'coordinator') {
    return <CoordinatorLayout>{children}</CoordinatorLayout>;
  }
  return <PublicLayout>{children}</PublicLayout>;
}

function SmartRedirect() {
  const token = getToken();
  const user = getUser();
  if (token && user?.role === 'coordinator') {
    return <CoordinatorLayout><Dashboard /></CoordinatorLayout>;
  }
  return <PublicLayout><Dashboard /></PublicLayout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Public/Smart routes */}
      <Route path="/" element={<SmartRedirect />} />
      <Route
        path="/calendar"
        element={
          getToken() && getUser()?.role === 'coordinator'
            ? <CoordinatorRoute><Calendar /></CoordinatorRoute>
            : <PublicLayout><Calendar /></PublicLayout>
        }
      />
      <Route
        path="/ratings"
        element={
          getToken() && getUser()?.role === 'coordinator'
            ? <CoordinatorRoute><Ratings /></CoordinatorRoute>
            : <PublicLayout><Ratings /></PublicLayout>
        }
      />

      {/* Coordinator-only */}
      <Route path="/admin" element={<CoordinatorRoute><Dashboard /></CoordinatorRoute>} />
      <Route path="/team" element={<CoordinatorRoute><Team /></CoordinatorRoute>} />
      <Route path="/team/:id" element={<CoordinatorRoute><VolunteerDetail /></CoordinatorRoute>} />
      <Route path="/settings" element={<CoordinatorRoute><SettingsPage /></CoordinatorRoute>} />
      <Route path="/moderation" element={<CoordinatorRoute><ModerationPage /></CoordinatorRoute>} />

      {/* Volunteer auth-required */}
      <Route path="/my-events" element={<AuthRoute><MyEvents /></AuthRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
