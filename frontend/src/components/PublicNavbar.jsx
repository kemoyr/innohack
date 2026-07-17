import { Link, NavLink } from 'react-router-dom';
import { LayoutDashboard, CalendarDays, Trophy, LogIn, UserPlus } from 'lucide-react';
import { getToken, getUser } from '../api';

const navItems = [
  { to: '/', label: 'Обзор', icon: LayoutDashboard },
  { to: '/calendar', label: 'Мероприятия', icon: CalendarDays },
  { to: '/ratings', label: 'Рейтинг', icon: Trophy },
];

export default function PublicNavbar() {
  const token = getToken();
  const user = getUser();

  return (
    <nav className="bg-white border-b border-neutral-200/60 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
              <span className="text-black font-extrabold text-sm">V+</span>
            </div>
            <span className="font-bold text-neutral-900 text-sm">
              Volunteer<span className="text-primary-500">+</span>
            </span>
          </Link>

          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-primary-100 text-primary-800'
                        : 'text-neutral-500 hover:text-neutral-700 hover:bg-neutral-50'
                    }`
                  }
                >
                  <Icon size={14} />
                  <span className="hidden sm:inline">{item.label}</span>
                </NavLink>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            {token && user ? (
              <Link
                to={user.role === 'coordinator' ? '/' : '/my-events'}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-primary-500 text-black rounded-lg text-xs font-bold hover:bg-primary-400 transition-all"
              >
                <span>{user.full_name || 'Кабинет'}</span>
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="flex items-center gap-1.5 px-3 py-1.5 text-neutral-600 hover:text-neutral-800 text-xs font-medium transition-colors"
                >
                  <LogIn size={14} />
                  <span className="hidden sm:inline">Войти</span>
                </Link>
                <Link
                  to="/register"
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-primary-500 text-black rounded-lg text-xs font-bold hover:bg-primary-400 transition-all"
                >
                  <UserPlus size={14} />
                  <span className="hidden sm:inline">Регистрация</span>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
