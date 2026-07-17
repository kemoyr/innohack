import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
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
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen bg-neutral-50">
      <Sidebar mobileOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      {mobileNavOpen ? (
        <button
          type="button"
          aria-label="Закрыть меню"
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileNavOpen(false)}
        />
      ) : null}
      <div className="flex min-h-screen min-w-0 flex-1 flex-col lg:ml-64">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-neutral-200/80 bg-white px-3 py-2.5 shadow-sm lg:hidden">
          <button
            type="button"
            onClick={() => setMobileNavOpen(true)}
            className="flex rounded-xl p-2.5 text-neutral-800 hover:bg-neutral-100 active:bg-neutral-200"
            aria-label="Открыть меню"
          >
            <Menu size={22} strokeWidth={2} />
          </button>
          <span className="text-sm font-bold text-neutral-900">
            Volunteer<span className="text-primary-600">+</span>
          </span>
        </header>
        <div className="flex-1 p-4 sm:p-5 lg:p-8">{children}</div>
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

      <Route path="/" element={<SmartRoute><Dashboard /></SmartRoute>} />
      <Route path="/calendar" element={<SmartRoute><Calendar /></SmartRoute>} />
      <Route path="/ratings" element={<SmartRoute><Ratings /></SmartRoute>} />
      <Route path="/volunteer/:id" element={<SmartRoute><VolunteerDetail /></SmartRoute>} />

      <Route path="/team" element={<CoordinatorRoute><Team /></CoordinatorRoute>} />
      <Route path="/team/:id" element={<CoordinatorRoute><VolunteerDetail /></CoordinatorRoute>} />
      <Route path="/moderation" element={<CoordinatorRoute><ModerationPage /></CoordinatorRoute>} />

      <Route path="/my-events" element={<AuthRoute><MyEvents /></AuthRoute>} />
      <Route path="/settings" element={<AuthRoute><SettingsPage /></AuthRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
