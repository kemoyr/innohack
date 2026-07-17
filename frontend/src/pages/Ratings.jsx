import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Trophy, Award, Medal, Star, Loader2, Users, Flame, MapPin } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../api';

function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

const badgeGradients = {
  gold: 'from-primary-400 to-primary-600',
  silver: 'from-neutral-400 to-neutral-500',
  bronze: 'from-primary-600 to-primary-800',
  default: 'from-neutral-700 to-neutral-900',
};

const podiumConfig = [
  {
    place: 1,
    gradient: 'from-primary-400 to-primary-600',
    ring: 'ring-primary-300',
    bg: 'bg-primary-50',
    rankBg: 'bg-primary-500',
    rankText: 'text-black',
    size: 'w-20 h-20',
    textSize: 'text-2xl',
    order: 'order-2',
    mt: '',
  },
  {
    place: 2,
    gradient: 'from-neutral-300 to-neutral-400',
    ring: 'ring-neutral-300',
    bg: 'bg-neutral-50',
    rankBg: 'bg-neutral-400',
    rankText: 'text-white',
    size: 'w-16 h-16',
    textSize: 'text-xl',
    order: 'order-1',
    mt: 'mt-6',
  },
  {
    place: 3,
    gradient: 'from-primary-600 to-primary-800',
    ring: 'ring-primary-300/50',
    bg: 'bg-primary-50',
    rankBg: 'bg-primary-700',
    rankText: 'text-white',
    size: 'w-16 h-16',
    textSize: 'text-xl',
    order: 'order-3',
    mt: 'mt-6',
  },
];

export default function Ratings() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [nominations, setNominations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('leaderboard');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [leaderData, achData, nomData] = await Promise.all([
          api.getLeaderboard(),
          api.getAchievements(),
          api.getNominations(),
        ]);
        setLeaderboard(leaderData);
        setAchievements(achData);
        setNominations(nomData);
      } catch (err) {
        console.error('Failed to fetch ratings data:', err);
      } finally {
        setLoading(false);
      }
    };
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

  const top3 = leaderboard.slice(0, 3);
  const maxPoints = leaderboard[0]?.points || 1;

  const chartBarData = leaderboard.slice(0, 10).map((p) => ({
    name: p.full_name?.split(' ')[0] || '?',
    points: p.points,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Рейтинг</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          Лидерборд и достижения волонтёров
        </p>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => setTab('leaderboard')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
            tab === 'leaderboard'
              ? 'bg-primary-500 text-black shadow-md shadow-primary-500/25'
              : 'bg-white text-neutral-600 border border-neutral-200 hover:bg-neutral-50'
          }`}
        >
          <Trophy size={15} />
          Лидерборд
        </button>
        <button
          onClick={() => setTab('achievements')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
            tab === 'achievements'
              ? 'bg-primary-500 text-black shadow-md shadow-primary-500/25'
              : 'bg-white text-neutral-600 border border-neutral-200 hover:bg-neutral-50'
          }`}
        >
          <Award size={15} />
          Достижения
          <span
            className={`px-1.5 py-0.5 rounded-md text-xs font-semibold ${
              tab === 'achievements'
                ? 'bg-black/10'
                : 'bg-neutral-100 text-neutral-500'
            }`}
          >
            {achievements.length}
          </span>
        </button>
      </div>

      {nominations && (nominations.biggest_audience || nominations.most_active || nominations.multi_city) && (
        <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
          <h2 className="text-sm font-semibold text-neutral-900 mb-4">Номинации</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {nominations.biggest_audience && (
              <div
                onClick={() => navigate(`/volunteer/${nominations.biggest_audience.volunteer_id}`)}
                className="cursor-pointer p-4 rounded-xl border border-neutral-200/60 hover:border-primary-300/50 transition-all"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
                    <Users size={16} className="text-primary-700" />
                  </div>
                  <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">
                    Самая большая аудитория
                  </span>
                </div>
                <p className="text-sm font-semibold text-neutral-900">
                  {nominations.biggest_audience.attendance_count} человек
                </p>
                <p className="text-xs text-neutral-500 mt-0.5 truncate">
                  {nominations.biggest_audience.event_title}
                </p>
                {nominations.biggest_audience.volunteer_name && (
                  <p className="text-xs text-primary-700 mt-1 font-medium">
                    {nominations.biggest_audience.volunteer_name}
                  </p>
                )}
              </div>
            )}
            {nominations.most_active && (
              <div
                onClick={() => navigate(`/volunteer/${nominations.most_active.id}`)}
                className="cursor-pointer p-4 rounded-xl border border-neutral-200/60 hover:border-primary-300/50 transition-all"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
                    <Flame size={16} className="text-primary-700" />
                  </div>
                  <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">
                    Самый активный волонтёр
                  </span>
                </div>
                <p className="text-sm font-semibold text-neutral-900">
                  {nominations.most_active.event_count} мероприятий
                </p>
                <p className="text-xs text-primary-700 mt-1 font-medium">
                  {nominations.most_active.full_name}
                </p>
              </div>
            )}
            {nominations.multi_city && (
              <div
                onClick={() => navigate(`/volunteer/${nominations.multi_city.id}`)}
                className="cursor-pointer p-4 rounded-xl border border-neutral-200/60 hover:border-primary-300/50 transition-all"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
                    <MapPin size={16} className="text-primary-700" />
                  </div>
                  <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">
                    Мультигород
                  </span>
                </div>
                <p className="text-sm font-semibold text-neutral-900">
                  {nominations.multi_city.city_count} города
                </p>
                <p className="text-xs text-primary-700 mt-1 font-medium">
                  {nominations.multi_city.full_name}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'leaderboard' ? (
        <div className="space-y-6">
          {top3.length >= 3 && (
            <div className="bg-white rounded-xl border border-neutral-200/60 p-8">
              <div className="flex items-end justify-center gap-6 md:gap-10">
                {podiumConfig.map((config) => {
                  const person = top3[config.place - 1];
                  if (!person) return null;
                  return (
                    <div
                      key={person.id}
                      className={`flex flex-col items-center cursor-pointer transition-all duration-200 hover:-translate-y-1 ${config.order} ${config.mt}`}
                      onClick={() => navigate(`/volunteer/${person.id}`)}
                    >
                      <div className={`w-8 h-8 ${config.rankBg} rounded-full flex items-center justify-center ${config.rankText} text-sm font-bold mb-3 shadow-sm`}>
                        {config.place}
                      </div>
                      <div
                        className={`${config.size} bg-gradient-to-br ${config.gradient} rounded-full flex items-center justify-center text-white font-bold ${config.textSize} shadow-lg ring-4 ${config.ring} mb-3`}
                      >
                        {person.full_name?.charAt(0)?.toUpperCase() || '?'}
                      </div>
                      <p className="font-semibold text-neutral-800 text-sm text-center">
                        {person.full_name}
                      </p>
                      <p className="text-xs text-neutral-500">{person.city}</p>
                      <div className="mt-2 flex items-center gap-1 px-2.5 py-1 bg-primary-50 rounded-lg">
                        <Star size={12} className="text-primary-500" />
                        <span className="font-bold text-xs text-primary-800">
                          {person.points}
                        </span>
                      </div>
                      {person.submission_count != null && (
                        <p className="text-xs text-neutral-400 mt-1">
                          {person.submission_count} отчётов
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {top3.length > 0 && top3.length < 3 && (
            <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
              <div className="flex justify-center gap-8">
                {top3.map((person, idx) => {
                  const config = podiumConfig[idx];
                  return (
                    <div
                      key={person.id}
                      className="flex flex-col items-center cursor-pointer transition-all duration-200 hover:-translate-y-1"
                      onClick={() => navigate(`/volunteer/${person.id}`)}
                    >
                      <div className={`w-8 h-8 ${config.rankBg} rounded-full flex items-center justify-center ${config.rankText} text-sm font-bold mb-3`}>
                        {config.place}
                      </div>
                      <div
                        className={`w-16 h-16 bg-gradient-to-br ${config.gradient} rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg ring-4 ${config.ring} mb-3`}
                      >
                        {person.full_name?.charAt(0)?.toUpperCase() || '?'}
                      </div>
                      <p className="font-semibold text-neutral-800 text-sm">{person.full_name}</p>
                      <p className="text-xs text-neutral-500">{person.city}</p>
                      <div className="mt-2 flex items-center gap-1 px-2.5 py-1 bg-primary-50 rounded-lg">
                        <Star size={12} className="text-primary-500" />
                        <span className="font-bold text-xs text-primary-800">{person.points}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {chartBarData.length > 0 && (
            <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
              <h2 className="text-sm font-semibold text-neutral-900 mb-4">
                Распределение баллов
              </h2>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartBarData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                    <XAxis
                      dataKey="name"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 11, fill: '#a3a3a3' }}
                      dy={8}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 11, fill: '#a3a3a3' }}
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
                      itemStyle={{ color: '#FFCC00' }}
                      labelStyle={{ color: '#a3a3a3', marginBottom: '4px' }}
                    />
                    <Bar
                      dataKey="points"
                      fill="#FFCC00"
                      radius={[6, 6, 0, 0]}
                      name="Баллы"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {leaderboard.length > 0 && (
            <div className="bg-white rounded-xl border border-neutral-200/60 overflow-hidden">
              <div className="px-6 py-4 border-b border-neutral-100">
                <h2 className="text-sm font-semibold text-neutral-900">
                  Полный рейтинг ({leaderboard.length} участников)
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-neutral-50/80">
                      <th className="text-left px-6 py-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider w-16">
                        #
                      </th>
                      <th className="text-left px-6 py-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                        Имя
                      </th>
                      <th className="text-left px-6 py-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                        Город
                      </th>
                      <th className="text-left px-6 py-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                        Прогресс
                      </th>
                      <th className="text-right px-6 py-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider w-24">
                        Баллы
                      </th>
                      <th className="text-right px-6 py-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider w-24">
                        Отчёты
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-50">
                    {leaderboard.map((person, idx) => {
                      const rank = idx + 1;
                      const barWidth = Math.max(
                        (person.points / maxPoints) * 100,
                        5
                      );
                      const isTop3 = rank <= 3;
                      const rankColors = [
                        'bg-primary-500 text-black',
                        'bg-neutral-400 text-white',
                        'bg-primary-700 text-white',
                      ];
                      return (
                        <tr
                          key={person.id}
                          onClick={() => navigate(`/volunteer/${person.id}`)}
                          className="cursor-pointer transition-colors duration-150 hover:bg-primary-50/50"
                        >
                          <td className="px-6 py-3.5">
                            {isTop3 ? (
                              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${rankColors[rank - 1]}`}>
                                {rank}
                              </div>
                            ) : (
                              <span className="font-semibold text-sm text-neutral-400 pl-1.5">
                                {rank}
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-3.5">
                            <div className="flex items-center gap-3">
                              <div
                                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                                  isTop3
                                    ? 'bg-primary-100 text-primary-800'
                                    : 'bg-neutral-100 text-neutral-500'
                                }`}
                              >
                                {person.full_name?.charAt(0)?.toUpperCase() || '?'}
                              </div>
                              <span
                                className={`text-sm font-medium ${
                                  isTop3 ? 'text-neutral-800' : 'text-neutral-600'
                                }`}
                              >
                                {person.full_name}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-3.5 text-sm text-neutral-500">
                            {person.city || '---'}
                          </td>
                          <td className="px-6 py-3.5">
                            <div className="w-full h-1.5 bg-neutral-100 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${
                                  isTop3
                                    ? 'bg-gradient-to-r from-primary-500 to-primary-400'
                                    : 'bg-primary-300/40'
                                }`}
                                style={{ width: `${barWidth}%` }}
                              />
                            </div>
                          </td>
                          <td className="px-6 py-3.5 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Star size={12} className="text-primary-500" />
                              <span
                                className={`font-bold text-sm ${
                                  isTop3 ? 'text-primary-800' : 'text-neutral-600'
                                }`}
                              >
                                {person.points}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-3.5 text-right text-sm text-neutral-500">
                            {person.submission_count ?? '---'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {leaderboard.length === 0 && (
            <div className="text-center py-16">
              <Trophy size={32} className="mx-auto mb-3 text-neutral-300" />
              <p className="text-neutral-500 text-sm font-medium">Пока нет данных для рейтинга</p>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {achievements.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {achievements.map((ach) => {
                const gradient = badgeGradients[ach.badge_type] || badgeGradients.default;
                return (
                  <div
                    key={ach.id}
                    className="bg-white rounded-xl border border-neutral-200/60 overflow-hidden transition-all duration-200 hover:shadow-md hover:-translate-y-0.5"
                  >
                    <div className={`bg-gradient-to-r ${gradient} px-5 py-4 text-white`}>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                          {ach.badge_type === 'gold' ? (
                            <Medal size={20} className="text-white" />
                          ) : ach.badge_type === 'silver' ? (
                            <Medal size={20} className="text-white" />
                          ) : ach.badge_type === 'bronze' ? (
                            <Medal size={20} className="text-white" />
                          ) : (
                            <Award size={20} className="text-white" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <h3 className="font-bold text-sm truncate">{ach.title}</h3>
                          {ach.description && (
                            <p className="text-xs text-white/80 truncate mt-0.5">
                              {ach.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="px-5 py-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center text-xs text-primary-800 font-bold">
                          {ach.volunteer_name?.charAt(0)?.toUpperCase() || '?'}
                        </div>
                        <span className="text-xs font-medium text-neutral-700 truncate">
                          {ach.volunteer_name}
                        </span>
                      </div>
                      <span className="text-xs text-neutral-400">
                        {formatDate(ach.created_at)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-16">
              <Award size={32} className="mx-auto mb-3 text-neutral-300" />
              <p className="text-neutral-500 text-sm font-medium">Достижений пока нет</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
