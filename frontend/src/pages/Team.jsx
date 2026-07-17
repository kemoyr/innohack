import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, Star, ChevronRight, UserCheck, UserX, Users, Loader2, Power } from 'lucide-react';
import api from '../api';

export default function Team() {
  const [volunteers, setVolunteers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [togglingId, setTogglingId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.getVolunteers();
        setVolunteers(data);
      } catch (err) {
        console.error('Failed to fetch volunteers:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  async function handleToggleStatus(e, volunteerId) {
    e.stopPropagation();
    setTogglingId(volunteerId);
    try {
      const updated = await api.toggleVolunteerStatus(volunteerId);
      setVolunteers((prev) =>
        prev.map((v) => (v.id === volunteerId ? { ...v, status: updated.status || (v.status === 'active' ? 'inactive' : 'active') } : v))
      );
    } catch {
      // Avoid UI noise; list will re-sync on next fetch/navigation.
    } finally {
      setTogglingId(null);
    }
  }

  const filtered = volunteers.filter((v) => {
    const matchSearch =
      !search ||
      v.full_name.toLowerCase().includes(search.toLowerCase()) ||
      (v.city && v.city.toLowerCase().includes(search.toLowerCase()));

    const matchFilter =
      filter === 'all' ||
      (filter === 'active' && v.status === 'active') ||
      (filter === 'inactive' && v.status !== 'active');

    return matchSearch && matchFilter;
  });

  const filterButtons = [
    { key: 'all', label: 'Все', icon: Users },
    { key: 'active', label: 'Активные', icon: UserCheck },
    { key: 'inactive', label: 'Неактивные', icon: UserX },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-neutral-400">
          <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
          <span className="text-sm font-medium">Загрузка...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Команда</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          Реестр волонтёров ({volunteers.length} всего)
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2">
            <Search size={16} className="text-neutral-400" />
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск по имени или городу..."
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-neutral-200 rounded-xl text-sm text-neutral-700 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 transition-all duration-200"
          />
        </div>

        <div className="flex gap-2">
          {filterButtons.map((btn) => {
            const Icon = btn.icon;
            return (
              <button
                key={btn.key}
                onClick={() => setFilter(btn.key)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  filter === btn.key
                    ? 'bg-primary-500 text-black shadow-md shadow-primary-500/25'
                    : 'bg-white text-neutral-600 border border-neutral-200 hover:bg-neutral-50'
                }`}
              >
                <Icon size={15} />
                <span>{btn.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <p className="text-xs text-neutral-400 font-medium">
        Показано: {filtered.length} из {volunteers.length}
      </p>

      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((v) => (
            <div
              key={v.id}
              onClick={() => navigate(`/team/${v.id}`)}
              className="bg-white rounded-xl border border-neutral-200/60 p-5 cursor-pointer transition-all duration-200 hover:shadow-md hover:border-primary-300/50 group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-800 font-bold text-sm">
                    {v.full_name.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-semibold text-neutral-800 truncate text-sm">
                      {v.full_name}
                    </h3>
                    <div className="flex items-center gap-1 text-xs text-neutral-400 mt-0.5">
                      <MapPin size={11} />
                      <span>{v.city || 'Город не указан'}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleToggleStatus(e, v.id)}
                    disabled={togglingId === v.id}
                    className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-200 ${
                      v.status === 'active'
                        ? 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'
                        : 'bg-neutral-50 text-neutral-400 hover:bg-neutral-100'
                    }`}
                    title={v.status === 'active' ? 'Деактивировать' : 'Активировать'}
                  >
                    {togglingId === v.id ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <Power size={13} />
                    )}
                  </button>
                  <span
                    className={`px-2 py-0.5 rounded-md text-xs font-semibold ${
                      v.status === 'active'
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-neutral-100 text-neutral-500'
                    }`}
                  >
                    {v.status === 'active' ? 'Активен' : 'Неактивен'}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-neutral-100">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1.5 text-sm">
                    <Star size={13} className="text-primary-500" />
                    <span className="font-semibold text-neutral-700">
                      {v.points || 0}
                    </span>
                    <span className="text-xs text-neutral-400">баллов</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-xs text-primary-700 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>Подробнее</span>
                  <ChevronRight size={14} />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <UserX size={32} className="mx-auto mb-3 text-neutral-300" />
          <p className="text-neutral-500 text-sm font-medium">Волонтёры не найдены</p>
          <p className="text-xs text-neutral-400 mt-1">
            Попробуйте изменить параметры поиска
          </p>
        </div>
      )}
    </div>
  );
}
