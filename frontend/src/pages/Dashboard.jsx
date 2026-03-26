import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, CalendarDays, TrendingUp, CheckCircle2, ChevronRight, Loader2, Activity } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import api from '../api';
import StatsCard from '../components/StatsCard';
import EventCard from '../components/EventCard';
import Leaderboard from '../components/Leaderboard';
import ActivityFeed from '../components/ActivityFeed';

function formatCurrentDate() {
  return new Date().toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

const PIE_COLORS = ['#FFC800', '#10b981', '#ef4444'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, eventsData, leaderData] = await Promise.all([
          api.getStats(),
          api.getEvents(),
          api.getLeaderboard(),
        ]);
        setStats(statsData);
        setEvents(eventsData);
        setLeaderboard(leaderData);

        try {
          const charts = await api.getChartData();
          const daily = (charts.daily_events || []).map(d => ({
            date: new Date(d.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }),
            count: d.count,
          }));
          setChartData(daily);
        } catch {
          const days = [];
          for (let i = 13; i >= 0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            const dateStr = d.toISOString().split('T')[0];
            const dayLabel = d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
            const count = eventsData.filter((e) => {
              const eDate = new Date(e.scheduled_date).toISOString().split('T')[0];
              return eDate === dateStr;
            }).length;
            days.push({ date: dayLabel, count });
          }
          setChartData(days);
        }
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

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

  const completionRate =
    stats && stats.total_events > 0
      ? Math.round((stats.completed_events / stats.total_events) * 100)
      : 0;

  const recentEvents = [...events]
    .sort((a, b) => new Date(b.scheduled_date) - new Date(a.scheduled_date))
    .slice(0, 5);

  const topVolunteers = leaderboard.slice(0, 5);

  const planned = events.filter((e) => e.status === 'planned').length;
  const completed = events.filter((e) => e.status === 'completed').length;
  const cancelled = events.filter((e) => e.status === 'cancelled').length;
  const pieData = [
    { name: 'Ожидается', value: planned },
    { name: 'Завершено', value: completed },
    { name: 'Отменено', value: cancelled },
  ].filter((d) => d.value > 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Обзор</h1>
        <p className="text-sm text-neutral-500 mt-0.5 capitalize">
          {formatCurrentDate()}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Волонтёров"
          value={stats?.total_volunteers || 0}
          subtitle={`${stats?.active_volunteers || 0} активных`}
          icon={Users}
          color="primary"
        />
        <StatsCard
          title="Мероприятий"
          value={stats?.total_events || 0}
          subtitle={`${stats?.completed_events || 0} завершено`}
          icon={CalendarDays}
          color="dark"
        />
        <StatsCard
          title="За эту неделю"
          value={stats?.this_week_events || 0}
          subtitle={`${stats?.this_month_events || 0} за месяц`}
          icon={TrendingUp}
          color="accent"
        />
        <StatsCard
          title="Выполнено"
          value={`${completionRate}%`}
          subtitle="процент завершения"
          icon={CheckCircle2}
          color="green"
        />
      </div>

      {/* Activity Chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-neutral-900">Активность</h2>
              <p className="text-xs text-neutral-500 mt-0.5">Мероприятия за последние 14 дней</p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-neutral-400">
              <Activity size={14} />
              <span>Мероприятия / день</span>
            </div>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FFC800" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#FFC800" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: '#a3a3a3' }}
                  dy={8}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: '#a3a3a3' }}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    background: '#1A1A1A',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#f5f5f5',
                    padding: '8px 12px',
                  }}
                  itemStyle={{ color: '#FFC800' }}
                  labelStyle={{ color: '#a3a3a3', marginBottom: '4px' }}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#FFC800"
                  strokeWidth={2}
                  fill="url(#colorCount)"
                  name="Мероприятий"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - 2/3 */}
        <div className="lg:col-span-2 space-y-6">
          {/* Recent Events */}
          <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-neutral-900">
                Последние мероприятия
              </h2>
              <Link
                to="/calendar"
                className="flex items-center gap-1 text-xs text-primary-700 hover:text-primary-800 font-medium transition-colors"
              >
                <span>Все мероприятия</span>
                <ChevronRight size={14} />
              </Link>
            </div>
            {recentEvents.length > 0 ? (
              <div className="space-y-2.5">
                {recentEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>
            ) : (
              <div className="text-center text-neutral-400 py-8">
                <CalendarDays size={24} className="mx-auto mb-2 text-neutral-300" />
                <p className="text-sm">Мероприятий пока нет</p>
              </div>
            )}
          </div>

          {/* Activity Feed */}
          <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-neutral-900">
                Лента активности
              </h2>
              <div className="flex items-center gap-1.5 text-xs text-neutral-400">
                <Activity size={14} />
                <span>Недавнее</span>
              </div>
            </div>
            <ActivityFeed />
          </div>
        </div>

        {/* Right column - 1/3 */}
        <div className="lg:col-span-1 space-y-6">
          {/* Mini leaderboard */}
          <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-neutral-900">
                Топ волонтёров
              </h2>
              <Link
                to="/ratings"
                className="flex items-center gap-1 text-xs text-primary-700 hover:text-primary-800 font-medium transition-colors"
              >
                <span>Все</span>
                <ChevronRight size={14} />
              </Link>
            </div>
            <Leaderboard data={topVolunteers} compact />
          </div>

          {/* Event Distribution */}
          {pieData.length > 0 && (
            <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
              <h2 className="text-sm font-semibold text-neutral-900 mb-4">
                Распределение мероприятий
              </h2>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={72}
                      paddingAngle={3}
                      dataKey="value"
                      strokeWidth={0}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: '#1A1A1A',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '12px',
                        color: '#f5f5f5',
                        padding: '8px 12px',
                      }}
                      itemStyle={{ color: '#f5f5f5' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap justify-center gap-3 mt-2">
                {pieData.map((entry, idx) => (
                  <div key={entry.name} className="flex items-center gap-1.5">
                    <div
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: PIE_COLORS[idx % PIE_COLORS.length] }}
                    />
                    <span className="text-xs text-neutral-500">
                      {entry.name} ({entry.value})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
