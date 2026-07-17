import { useState, useEffect } from 'react';
import { Clock, CheckCircle2, XCircle, MapPin, CalendarDays, Users, Star, UserPlus, Loader2 } from 'lucide-react';
import { getToken, getUser } from '../api';
import api from '../api';

const statusConfig = {
  pending: {
    icon: Clock,
    label: 'На проверке',
    badgeClass: 'bg-amber-100 text-amber-800 border border-amber-300/50',
    iconClass: 'text-amber-600',
  },
  planned: {
    icon: Clock,
    label: 'Ожидается',
    badgeClass: 'bg-primary-100 text-primary-800 border border-primary-300/50',
    iconClass: 'text-primary-600',
  },
  completed: {
    icon: CheckCircle2,
    label: 'Завершено',
    badgeClass: 'bg-emerald-50 text-emerald-700 border border-emerald-200/50',
    iconClass: 'text-emerald-500',
  },
  cancelled: {
    icon: XCircle,
    label: 'Отменено',
    badgeClass: 'bg-red-50 text-red-700 border border-red-200/50',
    iconClass: 'text-red-500',
  },
};

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function formatTime(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const hours = date.getHours();
  const minutes = date.getMinutes();
  if (hours === 0 && minutes === 0) return '';
  return date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function EventCard({ event, onApplied }) {
  const status = statusConfig[event.status] || statusConfig.planned;
  const StatusIcon = status.icon;
  const token = getToken();
  const user = getUser();
  const isLoggedIn = !!token;
  const isPlanned = event.status === 'planned';
  const isCompleted = event.status === 'completed';

  const [showApply, setShowApply] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [applying, setApplying] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [applied, setApplied] = useState(false);
  const [reviewed, setReviewed] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ full_name: user?.full_name || '', email: '', phone: '' });
  const [reviewForm, setReviewForm] = useState({ rating: 5, comment: '' });
  const [showComplete, setShowComplete] = useState(false);
  const [completeAttendance, setCompleteAttendance] = useState('');
  const [completing, setCompleting] = useState(false);
  const [completeMessage, setCompleteMessage] = useState('');

  const isCoordinator = user?.role === 'coordinator';
  const isEventOrganizer =
    user?.user_id != null &&
    event?.created_by != null &&
    Number(user.user_id) === Number(event.created_by);

  useEffect(() => {
    if (!token || !event?.id) return;
    let cancelled = false;
    (async () => {
      try {
        const [app, rev] = await Promise.all([
          api.getMyApplication(event.id).catch(() => null),
          api.getMyReview(event.id).catch(() => null),
        ]);
        if (cancelled) return;
        if (app && app.id) setApplied(true);
        if (rev && rev.id) setReviewed(true);
      } catch {
        /* ignore */
      }
    })();
    return () => { cancelled = true; };
  }, [token, event?.id]);

  async function handleApply(e) {
    e.preventDefault();
    setApplying(true);
    setError('');
    try {
      await api.applyToEvent(event.id, form);
      setApplied(true);
      setShowApply(false);
      if (onApplied) onApplied();
    } catch (err) {
      setError(err.message);
    } finally {
      setApplying(false);
    }
  }

  async function handleReview(e) {
    e.preventDefault();
    setReviewing(true);
    setError('');
    try {
      await api.reviewEvent(event.id, reviewForm);
      setReviewed(true);
      setShowReview(false);
      if (onApplied) onApplied();
    } catch (err) {
      setError(err.message);
    } finally {
      setReviewing(false);
    }
  }

  async function handleCompleteEvent(e) {
    e.preventDefault();
    setCompleting(true);
    setCompleteMessage('');
    setError('');
    try {
      const attendance = parseInt(String(completeAttendance), 10);
      const data = await api.updateEvent(event.id, {
        status: 'completed',
        attendance_count: Number.isFinite(attendance) ? attendance : 0,
      });
      setCompleteMessage(
        data.points_bonus != null
          ? `Мероприятие завершено. Организатору начислено +${data.points_bonus} баллов.`
          : 'Мероприятие завершено.',
      );
      if (onApplied) onApplied();
    } catch (err) {
      setError(err.message || 'Не удалось завершить');
    } finally {
      setCompleting(false);
    }
  }

  return (
    <div className="bg-white rounded-xl border border-neutral-200/60 p-4 transition-all duration-200 hover:shadow-md hover:border-primary-300/50">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5 mb-2.5">
            <StatusIcon size={16} className={status.iconClass} />
            <h3 className="font-semibold text-neutral-800 truncate text-sm">
              {event.title}
            </h3>
          </div>

          <div className="space-y-1.5">
            {event.location_name && (
              <div className="flex items-center gap-2 text-sm text-neutral-500">
                <MapPin size={14} className="text-neutral-400 shrink-0" />
                <span className="truncate">{event.location_name}</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-sm text-neutral-500">
              <CalendarDays size={14} className="text-neutral-400 shrink-0" />
              <span>
                {formatDate(event.scheduled_date)}
                {formatTime(event.scheduled_date) &&
                  `, ${formatTime(event.scheduled_date)}`}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 mt-2.5">
            {event.application_count > 0 && (
              <div className="flex items-center gap-1 text-xs text-neutral-500">
                <Users size={12} />
                <span>{event.application_count} заявок</span>
              </div>
            )}
            {event.avg_rating > 0 && (
              <div className="flex items-center gap-1 text-xs text-primary-700">
                <Star size={12} className="fill-primary-500 text-primary-500" />
                <span>{event.avg_rating}</span>
                <span className="text-neutral-400">({event.review_count})</span>
              </div>
            )}
            {isCompleted && event.attendance_count > 0 && (
              <div className="flex items-center gap-1 text-xs text-emerald-600">
                <Users size={12} />
                <span>{event.attendance_count} участников</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <span
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${status.badgeClass}`}
          >
            {status.label}
          </span>
        </div>
      </div>

      {/* Coordinator: complete planned event */}
      {isLoggedIn && isCoordinator && isPlanned && (
        <div className="mt-3 pt-3 border-t border-neutral-100">
          {!showComplete ? (
            <button
              type="button"
              onClick={() => {
                setShowComplete(true);
                setCompleteAttendance(String(event.attendance_count || ''));
                setCompleteMessage('');
                setError('');
              }}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-100 text-emerald-900 rounded-lg text-xs font-semibold hover:bg-emerald-200 transition-all"
            >
              <CheckCircle2 size={14} />
              Завершить мероприятие
            </button>
          ) : (
            <form onSubmit={handleCompleteEvent} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-neutral-600 mb-1">
                  Число участников (необязательно)
                </label>
                <input
                  type="number"
                  min={0}
                  value={completeAttendance}
                  onChange={(e) => setCompleteAttendance(e.target.value)}
                  placeholder="0"
                  className="w-full max-w-[140px] px-3 py-2 border border-neutral-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500"
                />
              </div>
              {error && <p className="text-xs text-red-600">{error}</p>}
              {completeMessage && (
                <p className="text-xs text-emerald-700 font-medium">{completeMessage}</p>
              )}
              <div className="flex gap-2 flex-wrap">
                <button
                  type="submit"
                  disabled={completing || !!completeMessage}
                  className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-black rounded-lg text-xs font-bold hover:bg-primary-400 transition-all disabled:opacity-50"
                >
                  {completing ? <Loader2 size={12} className="animate-spin" /> : <CheckCircle2 size={12} />}
                  Подтвердить завершение
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowComplete(false);
                    setCompleteMessage('');
                    setError('');
                  }}
                  className="px-4 py-2 text-neutral-500 text-xs font-medium hover:text-neutral-700"
                >
                  Отмена
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* Action buttons */}
      {isLoggedIn && !isCoordinator && !applied && isPlanned && (
        <div className="mt-3 pt-3 border-t border-neutral-100">
          {!showApply ? (
            <button
              onClick={() => setShowApply(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-800 rounded-lg text-xs font-semibold hover:bg-primary-200 transition-all"
            >
              <UserPlus size={14} />
              Подать заявку
            </button>
          ) : (
            <form onSubmit={handleApply} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                  type="text"
                  required
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  placeholder="ФИО *"
                  className="px-3 py-2 border border-neutral-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500"
                />
                <input
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="Email *"
                  className="px-3 py-2 border border-neutral-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500"
                />
                <input
                  type="tel"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  placeholder="Телефон"
                  className="px-3 py-2 border border-neutral-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500"
                />
              </div>
              {error && <p className="text-xs text-red-600">{error}</p>}
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={applying}
                  className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-black rounded-lg text-xs font-bold hover:bg-primary-400 transition-all disabled:opacity-50"
                >
                  {applying ? <Loader2 size={12} className="animate-spin" /> : <UserPlus size={12} />}
                  Отправить
                </button>
                <button
                  type="button"
                  onClick={() => { setShowApply(false); setError(''); }}
                  className="px-4 py-2 text-neutral-500 text-xs font-medium hover:text-neutral-700"
                >
                  Отмена
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {applied && (
        <div className="mt-3 pt-3 border-t border-neutral-100">
          <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
            <CheckCircle2 size={14} />
            Заявка отправлена!
          </div>
        </div>
      )}

      {/* Review: участники с заявкой или организатор (создатель) мероприятия */}
      {isLoggedIn &&
        !isCoordinator &&
        isCompleted &&
        (applied || isEventOrganizer) &&
        !reviewed && (
        <div className="mt-3 pt-3 border-t border-neutral-100">
          {!showReview ? (
            <button
              onClick={() => setShowReview(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-800 rounded-lg text-xs font-semibold hover:bg-primary-200 transition-all"
            >
              <Star size={14} />
              Оставить отзыв
            </button>
          ) : (
            <form onSubmit={handleReview} className="space-y-3">
              <div>
                <p className="text-xs font-medium text-neutral-600 mb-1.5">Оценка</p>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setReviewForm({ ...reviewForm, rating: s })}
                      className="p-1 transition-transform hover:scale-110"
                    >
                      <Star
                        size={20}
                        className={s <= reviewForm.rating ? 'fill-primary-500 text-primary-500' : 'text-neutral-300'}
                      />
                    </button>
                  ))}
                </div>
              </div>
              <textarea
                value={reviewForm.comment}
                onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
                placeholder="Ваш отзыв..."
                rows={2}
                className="w-full px-3 py-2 border border-neutral-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 resize-none"
              />
              {error && <p className="text-xs text-red-600">{error}</p>}
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={reviewing}
                  className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-black rounded-lg text-xs font-bold hover:bg-primary-400 transition-all disabled:opacity-50"
                >
                  {reviewing ? <Loader2 size={12} className="animate-spin" /> : <Star size={12} />}
                  Отправить
                </button>
                <button
                  type="button"
                  onClick={() => { setShowReview(false); setError(''); }}
                  className="px-4 py-2 text-neutral-500 text-xs font-medium hover:text-neutral-700"
                >
                  Отмена
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {reviewed && (
        <div className="mt-3 pt-3 border-t border-neutral-100">
          <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
            <CheckCircle2 size={14} />
            Отзыв отправлен!
          </div>
        </div>
      )}
    </div>
  );
}
