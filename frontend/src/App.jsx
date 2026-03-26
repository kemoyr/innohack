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

function SidebarLayout({ children }) {
  return (
    <div className="dashboard-layout">
      <Sidebar />
      <div className="main-content">
        <div className="p-6 lg:p-8">{children}</div>
      </div>
    </div>
  );
}

function AuthRoute({ children }) {
  const token = getToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <SidebarLayout>{children}</SidebarLayout>;
}

function CoordinatorRoute({ children }) {
  const token = getToken();
  const user = getUser();
  if (!token || !user || user.role !== 'coordinator') {
    return <Navigate to="/login" replace />;
  }
  return <SidebarLayout>{children}</SidebarLayout>;
}

function SmartRoute({ children }) {
  const token = getToken();
  if (token) {
    return <SidebarLayout>{children}</SidebarLayout>;
  }
  return <PublicLayout>{children}</PublicLayout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Public or sidebar depending on auth */}
      <Route path="/" element={<SmartRoute><Dashboard /></SmartRoute>} />
      <Route path="/calendar" element={<SmartRoute><Calendar /></SmartRoute>} />
      <Route path="/ratings" element={<SmartRoute><Ratings /></SmartRoute>} />
      <Route path="/volunteer/:id" element={<SmartRoute><VolunteerDetail /></SmartRoute>} />

      {/* Coordinator-only */}
      <Route path="/team" element={<CoordinatorRoute><Team /></CoordinatorRoute>} />
      <Route path="/team/:id" element={<CoordinatorRoute><VolunteerDetail /></CoordinatorRoute>} />
      <Route path="/moderation" element={<CoordinatorRoute><ModerationPage /></CoordinatorRoute>} />

      {/* Any authenticated user */}
      <Route path="/my-events" element={<AuthRoute><MyEvents /></AuthRoute>} />
      <Route path="/settings" element={<AuthRoute><SettingsPage /></AuthRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
