import { useState, useEffect } from 'react';
import { CalendarDays, Clock, CheckCircle2, Plus, Loader2, XCircle, X } from 'lucide-react';
import api from '../api';
import EventCard from '../components/EventCard';

function groupByMonth(events) {
  const groups = {};
  events.forEach((event) => {
    const date = new Date(event.scheduled_date);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const label = date.toLocaleDateString('ru-RU', {
      month: 'long',
      year: 'numeric',
    });
    if (!groups[key]) {
      groups[key] = { label, events: [] };
    }
    groups[key].events.push(event);
  });
  return Object.entries(groups)
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([, group]) => group);
}

export default function Calendar() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    location_name: '',
    scheduled_date: '',
  });

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.getEvents();
        setEvents(data);
      } catch (err) {
        console.error('Failed to fetch events:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  async function handleCreateEvent(e) {
    e.preventDefault();
    setCreating(true);
    try {
      const newEvent = await api.createEvent(formData);
      setEvents((prev) => [newEvent, ...prev]);
      setShowCreate(false);
      setFormData({ title: '', location_name: '', scheduled_date: '' });
    } catch (err) {
      console.error('Failed to create event:', err);
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-slate-400">
          <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
          <span className="text-sm font-medium">Загрузка...</span>
        </div>
      </div>
    );
  }

  const planned = events.filter((e) => e.status === 'planned');
  const completed = events.filter((e) => e.status === 'completed');
  const cancelled = events.filter((e) => e.status === 'cancelled');

  const displayed =
    tab === 'planned' ? planned : tab === 'completed' ? completed : events;

  const sorted = [...displayed].sort(
    (a, b) => new Date(b.scheduled_date) - new Date(a.scheduled_date)
  );

  const grouped = groupByMonth(sorted);

  const tabs = [
    { key: 'all', label: 'Все', count: events.length, icon: CalendarDays },
    { key: 'planned', label: 'Предстоящие', count: planned.length, icon: Clock },
    { key: 'completed', label: 'Завершённые', count: completed.length, icon: CheckCircle2 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Календарь</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Все мероприятия ({events.length})
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700 shadow-sm shadow-primary-600/25 transition-all duration-200"
        >
          <Plus size={16} />
          <span>Создать мероприятие</span>
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200/60 p-4 flex items-center gap-4">
          <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
            <CalendarDays size={18} className="text-blue-600" />
          </div>
          <div>
            <p className="text-xl font-bold text-slate-900">{events.length}</p>
            <p className="text-xs text-slate-500">Всего мероприятий</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200/60 p-4 flex items-center gap-4">
          <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
            <Clock size={18} className="text-amber-600" />
          </div>
          <div>
            <p className="text-xl font-bold text-slate-900">{planned.length}</p>
            <p className="text-xs text-slate-500">Запланировано</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200/60 p-4 flex items-center gap-4">
          <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
            <CheckCircle2 size={18} className="text-emerald-600" />
          </div>
          <div>
            <p className="text-xl font-bold text-slate-900">{completed.length}</p>
            <p className="text-xs text-slate-500">Завершено</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {tabs.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                tab === t.key
                  ? 'bg-primary-600 text-white shadow-md shadow-primary-600/25'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Icon size={15} />
              <span>{t.label}</span>
              <span
                className={`px-1.5 py-0.5 rounded-md text-xs font-semibold ${
                  tab === t.key
                    ? 'bg-white/20'
                    : 'bg-slate-100 text-slate-500'
                }`}
              >
                {t.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Events grouped by month */}
      {grouped.length > 0 ? (
        <div className="space-y-6">
          {grouped.map((group) => (
            <div key={group.label}>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-1">
                {group.label}
              </h3>
              <div className="space-y-2.5">
                {group.events.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <CalendarDays size={32} className="mx-auto mb-3 text-slate-300" />
          <p className="text-slate-500 text-sm font-medium">Мероприятий не найдено</p>
          <p className="text-xs text-slate-400 mt-1">Попробуйте выбрать другой фильтр</p>
        </div>
      )}

      {/* Create Event Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 relative">
            <button
              onClick={() => setShowCreate(false)}
              className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 text-slate-400 transition-colors"
            >
              <X size={18} />
            </button>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center">
                <Plus size={18} className="text-primary-600" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-slate-900">Новое мероприятие</h2>
                <p className="text-xs text-slate-500">Заполните информацию</p>
              </div>
            </div>
            <form onSubmit={handleCreateEvent} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Название
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Название мероприятия..."
                  className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Место проведения
                </label>
                <input
                  type="text"
                  value={formData.location_name}
                  onChange={(e) => setFormData({ ...formData, location_name: e.target.value })}
                  placeholder="Адрес или место..."
                  className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Дата и время
                </label>
                <input
                  type="datetime-local"
                  required
                  value={formData.scheduled_date}
                  onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 transition-all"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="flex-1 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700 shadow-sm shadow-primary-600/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {creating ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      Создание...
                    </>
                  ) : (
                    'Создать'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
