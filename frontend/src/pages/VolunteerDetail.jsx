import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  MapPin,
  MessageCircle,
  Calendar,
  CalendarDays,
  Star,
  FileText,
  Award,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
} from 'lucide-react';
import api from '../api';

function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

const badgeColors = {
  gold: 'from-primary-400 to-primary-600',
  silver: 'from-neutral-400 to-neutral-500',
  bronze: 'from-accent-400 to-accent-600',
  default: 'from-neutral-700 to-neutral-900',
};

const submissionStatusConfig = {
  verified: { label: 'Принят', icon: CheckCircle2, className: 'bg-emerald-50 text-emerald-700' },
  rejected: { label: 'Отклонён', icon: XCircle, className: 'bg-red-50 text-red-700' },
  pending: { label: 'На проверке', icon: Clock, className: 'bg-primary-100 text-primary-800' },
  bonus: { label: 'Начисление', icon: Star, className: 'bg-amber-50 text-amber-900' },
};

const createdEventStatusConfig = {
  pending: { label: 'На модерации', cls: 'bg-amber-50 text-amber-800' },
  planned: { label: 'В календаре', cls: 'bg-primary-50 text-primary-800' },
  completed: { label: 'Завершено', cls: 'bg-emerald-50 text-emerald-700' },
  cancelled: { label: 'Отменено', cls: 'bg-neutral-100 text-neutral-500' },
  rejected: { label: 'Отклонено', cls: 'bg-red-50 text-red-700' },
};

export default function VolunteerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [volunteer, setVolunteer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.getVolunteer(id);
        setVolunteer(data);
      } catch {
        setError('Не удалось загрузить данные волонтёра');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [id]);

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

  if (error || !volunteer) {
    return (
      <div className="text-center py-16">
        <AlertCircle size={32} className="mx-auto mb-3 text-neutral-300" />
        <p className="text-neutral-500 text-sm">{error || 'Волонтёр не найден'}</p>
        <button
          onClick={() => navigate('/team')}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-black rounded-xl hover:bg-primary-400 transition-colors text-sm font-bold"
        >
          <ArrowLeft size={16} />
          Назад
        </button>
      </div>
    );
  }

  const activityReports = volunteer.activity_reports || [];
  const reportsCount = activityReports.filter((r) => r.kind === 'submission').length;
  const createdEvents = volunteer.created_events || [];
  const achievements = volunteer.achievements || [];
  const reviews = volunteer.reviews || [];
  const isPublicProfile = volunteer.profile_scope === 'public';

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-neutral-500 hover:text-primary-700 transition-colors font-medium"
      >
        <ArrowLeft size={16} />
        <span>Назад</span>
      </button>

      {/* Profile Header */}
      <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
        {isPublicProfile && (
          <div className="mb-4 rounded-xl border border-neutral-200/80 bg-neutral-50 px-4 py-3 text-xs text-neutral-600 leading-relaxed">
            Открытый профиль: контакты, детальные отчёты и мероприятия на модерации не показываются. Полные данные видны владельцу после входа и координатору.
          </div>
        )}
        <div className="flex items-start gap-5">
          <div className="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center text-primary-800 text-xl font-bold shrink-0">
            {volunteer.full_name?.charAt(0)?.toUpperCase() || '?'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl font-bold text-neutral-900">
                {volunteer.full_name}
              </h1>
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold ${
                  volunteer.status === 'active'
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-neutral-100 text-neutral-500'
                }`}
              >
                {volunteer.status === 'active' ? (
                  <CheckCircle2 size={12} />
                ) : (
                  <XCircle size={12} />
                )}
                {volunteer.status === 'active' ? 'Активен' : 'Неактивен'}
              </span>
            </div>
            <div className="flex flex-wrap gap-4 mt-3 text-sm text-neutral-500">
              {volunteer.city && (
                <div className="flex items-center gap-1.5">
                  <MapPin size={14} className="text-neutral-400" />
                  <span>{volunteer.city}</span>
                </div>
              )}
              {volunteer.telegram_id && (
                <div className="flex items-center gap-1.5">
                  <MessageCircle size={14} className="text-neutral-400" />
                  <span>Telegram: {volunteer.telegram_id}</span>
                </div>
              )}
              {volunteer.created_at && (
                <div className="flex items-center gap-1.5">
                  <Calendar size={14} className="text-neutral-400" />
                  <span>С {formatDate(volunteer.created_at)}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 pt-6 border-t border-neutral-100">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Star size={16} className="text-primary-500" />
            </div>
            <p className="text-2xl font-bold text-neutral-900">{volunteer.points || 0}</p>
            <p className="text-xs text-neutral-500 mt-0.5">Баллов</p>
            <p className="text-[10px] text-neutral-400 mt-1 px-1 leading-snug max-w-[200px] mx-auto">
              {isPublicProfile
                ? 'Детальная разбивка — только для владельца'
                : 'Разбивка — в блоке «Отчёты» ниже'}
            </p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <FileText size={16} className="text-neutral-500" />
            </div>
            <p className="text-2xl font-bold text-neutral-900">{reportsCount}</p>
            <p className="text-xs text-neutral-500 mt-0.5">Отчётов</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Award size={16} className="text-accent-500" />
            </div>
            <p className="text-2xl font-bold text-neutral-900">{achievements.length}</p>
            <p className="text-xs text-neutral-500 mt-0.5">Достижений</p>
          </div>
        </div>
      </div>

      {/* Events created by this volunteer (не путать с отчётами) */}
      {createdEvents.length > 0 && (
        <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
          <div className="flex items-center gap-2 mb-4">
            <CalendarDays size={16} className="text-accent-600" />
            <h2 className="text-sm font-semibold text-neutral-900">Созданные мероприятия</h2>
            <span className="text-xs text-neutral-400 ml-auto">{createdEvents.length}</span>
          </div>
          <p className="text-xs text-neutral-500 mb-3">
            Здесь идеи и события, которые волонтёр подал через сайт. Отчёты о проведённых мероприятиях — в блоке «Отчёты».
          </p>
          <div className="space-y-2">
            {createdEvents.map((ev) => {
              const st = createdEventStatusConfig[ev.status] || createdEventStatusConfig.pending;
              return (
                <div
                  key={ev.id}
                  className="flex items-start justify-between gap-3 p-3 rounded-lg bg-neutral-50/50 border border-neutral-100"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-neutral-800 truncate">{ev.title}</p>
                    <p className="text-xs text-neutral-400 mt-0.5">
                      {ev.scheduled_date ? formatDate(ev.scheduled_date) : 'Дата уточняется'}
                      {ev.location_name ? ` · ${ev.location_name}` : ''}
                    </p>
                  </div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-md shrink-0 ${st.cls}`}>
                    {st.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Submissions */}
        <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
          <div className="flex items-center gap-2 mb-1">
            <FileText size={16} className="text-neutral-400" />
            <h2 className="text-sm font-semibold text-neutral-900">Отчёты</h2>
            <span className="text-xs text-neutral-400 ml-auto">{activityReports.length}</span>
          </div>
          <p className="text-xs text-neutral-500 mb-4">
            Для каждой строки указано, за что начислены баллы (как раньше в «Истории начислений»), плюс отдельные бонусы без отчёта.
          </p>
          {activityReports.length > 0 ? (
            <div className="space-y-2 max-h-[28rem] overflow-y-auto pr-1">
              {activityReports.map((row) => {
                const isBonus = row.kind === 'bonus';
                const statusConf =
                  submissionStatusConfig[row.status] || submissionStatusConfig.pending;
                const StatusIcon = statusConf.icon;
                const pts = row.points_awarded ?? 0;
                return (
                  <div
                    key={row.id}
                    className="flex items-start justify-between gap-3 p-3 rounded-lg bg-neutral-50/50 border border-neutral-100"
                  >
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      {isBonus ? (
                        <Star size={14} className="text-amber-500 shrink-0 mt-0.5" />
                      ) : (
                        <FileText size={14} className="text-neutral-400 shrink-0 mt-0.5" />
                      )}
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-neutral-800 leading-snug">
                          {row.accrual_reason || 'Начисление'}
                        </p>
                        {row.event_title && (
                          <p className="text-xs text-neutral-500 truncate mt-1">{row.event_title}</p>
                        )}
                        <p className="text-xs text-neutral-400 mt-1">
                          {formatDate(row.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1.5 shrink-0">
                      {(pts !== 0 || isBonus) && (
                        <span
                          className={`inline-flex items-center gap-0.5 text-sm font-bold tabular-nums ${pts >= 0 ? 'text-emerald-700' : 'text-red-600'}`}
                        >
                          <Star size={12} className="text-primary-500" />
                          {pts >= 0 ? '+' : ''}
                          {pts}
                        </span>
                      )}
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold ${statusConf.className}`}
                      >
                        <StatusIcon size={11} />
                        {statusConf.label}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-10 text-neutral-400">
              <FileText size={24} className="mx-auto mb-2 text-neutral-300" />
              <p className="text-sm">Отчётов и начислений пока нет</p>
            </div>
          )}
        </div>

        {/* Achievements */}
        <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Award size={16} className="text-neutral-400" />
            <h2 className="text-sm font-semibold text-neutral-900">Достижения</h2>
            <span className="text-xs text-neutral-400 ml-auto">{achievements.length}</span>
          </div>
          {achievements.length > 0 ? (
            <div className="grid grid-cols-2 gap-3">
              {achievements.map((ach, idx) => {
                const gradient = badgeColors[ach.badge_type] || badgeColors.default;
                return (
                  <div
                    key={ach.id || idx}
                    className={`bg-gradient-to-br ${gradient} rounded-xl p-4 text-center shadow-sm`}
                  >
                    <div className="w-10 h-10 mx-auto mb-2 bg-white/20 rounded-xl flex items-center justify-center">
                      <Award size={20} className="text-white" />
                    </div>
                    <p className="font-bold text-sm text-white">{ach.title}</p>
                    {ach.description && (
                      <p className="text-xs mt-1 text-white/80">{ach.description}</p>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-10 text-neutral-400">
              <Award size={24} className="mx-auto mb-2 text-neutral-300" />
              <p className="text-sm">Достижений пока нет</p>
            </div>
          )}
        </div>
      </div>

      {/* Reviews written by this volunteer */}
      {reviews.length > 0 && (
        <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Star size={16} className="text-primary-500" />
            <h2 className="text-sm font-semibold text-neutral-900">Отзывы</h2>
            <span className="text-xs text-neutral-400 ml-auto">{reviews.length}</span>
          </div>
          <div className="space-y-3">
            {reviews.map((rev) => (
              <div key={rev.id} className="p-4 rounded-lg bg-neutral-50/50 border border-neutral-100">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-neutral-700">{rev.event_title}</p>
                  <div className="flex items-center gap-0.5">
                    {[1, 2, 3, 4, 5].map((s) => (
                      <Star
                        key={s}
                        size={12}
                        className={s <= rev.rating ? 'fill-primary-500 text-primary-500' : 'text-neutral-300'}
                      />
                    ))}
                  </div>
                </div>
                {rev.comment && (
                  <p className="text-xs text-neutral-500">{rev.comment}</p>
                )}
                <p className="text-xs text-neutral-400 mt-1.5">{formatDate(rev.created_at)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
