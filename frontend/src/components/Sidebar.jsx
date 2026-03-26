import { NavLink, useNavigate } from 'react-router-dom';
import { clearToken, getUser } from '../api';
import { LayoutDashboard, Users, CalendarDays, Trophy, Settings, LogOut, Shield, ShieldCheck, ClipboardList } from 'lucide-react';

const coordinatorNav = [
  { to: '/', label: 'Обзор', icon: LayoutDashboard },
  { to: '/team', label: 'Команда', icon: Users },
  { to: '/calendar', label: 'Календарь', icon: CalendarDays },
  { to: '/ratings', label: 'Рейтинг', icon: Trophy },
  { to: '/moderation', label: 'Модерация', icon: ShieldCheck },
  { to: '/settings', label: 'Настройки', icon: Settings },
];

const volunteerNav = [
  { to: '/', label: 'Обзор', icon: LayoutDashboard },
  { to: '/my-events', label: 'Мои мероприятия', icon: ClipboardList },
  { to: '/calendar', label: 'Календарь', icon: CalendarDays },
  { to: '/ratings', label: 'Рейтинг', icon: Trophy },
  { to: '/settings', label: 'Настройки', icon: Settings },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const user = getUser();
  const isCoordinator = user?.role === 'coordinator';
  const navItems = isCoordinator ? coordinatorNav : volunteerNav;

  function handleLogout() {
    clearToken();
    navigate('/login');
  }

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 bg-bee-black text-white flex flex-col z-50">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
            <span className="text-black font-extrabold text-lg tracking-tight">V+</span>
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white">
              Volunteer<span className="text-primary-400">+</span>
            </h1>
            <p className="text-xs text-neutral-500">
              {isCoordinator ? 'Панель координатора' : 'Панель волонтёра'}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary-500/15 text-primary-400'
                    : 'text-neutral-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Icon size={18} strokeWidth={2} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Beeline stripe accent */}
      <div className="mx-6 mb-4">
        <div className="h-1 rounded-full bg-gradient-to-r from-primary-500 via-primary-400 to-primary-500" />
      </div>

      {/* User info */}
      <div className="px-4 py-3 mx-3 mb-2 rounded-lg bg-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary-500/20 rounded-full flex items-center justify-center">
            <Shield size={14} className="text-primary-400" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-neutral-300 truncate">
              {user?.full_name || 'Пользователь'}
            </p>
            <p className="text-xs text-neutral-500">
              {isCoordinator ? 'Координатор' : 'Волонтёр'}
            </p>
          </div>
        </div>
      </div>

      {/* Logout */}
      <div className="px-3 py-3 border-t border-white/10">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-neutral-400 hover:bg-red-500/10 hover:text-red-400 transition-all duration-200 w-full"
        >
          <LogOut size={18} strokeWidth={2} />
          <span>Выйти</span>
        </button>
      </div>
    </aside>
  );
}
