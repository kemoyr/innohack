import { Clock, CheckCircle2, XCircle, MapPin, CalendarDays, Users } from 'lucide-react';

const statusConfig = {
  planned: {
    icon: Clock,
    label: 'Ожидается',
    badgeClass: 'bg-blue-50 text-blue-700 border border-blue-200/50',
    iconClass: 'text-blue-500',
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

export default function EventCard({ event }) {
  const status = statusConfig[event.status] || statusConfig.planned;
  const StatusIcon = status.icon;

  return (
    <div className="bg-white rounded-xl border border-slate-200/60 p-4 transition-all duration-200 hover:shadow-md hover:border-slate-200">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5 mb-2.5">
            <StatusIcon size={16} className={status.iconClass} />
            <h3 className="font-semibold text-slate-800 truncate text-sm">
              {event.title}
            </h3>
          </div>

          <div className="space-y-1.5">
            {event.location_name && (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <MapPin size={14} className="text-slate-400 shrink-0" />
                <span className="truncate">{event.location_name}</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <CalendarDays size={14} className="text-slate-400 shrink-0" />
              <span>
                {formatDate(event.scheduled_date)}
                {formatTime(event.scheduled_date) &&
                  `, ${formatTime(event.scheduled_date)}`}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <span
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${status.badgeClass}`}
          >
            {status.label}
          </span>
          {event.status === 'completed' && event.attendance_count != null && (
            <div className="flex items-center gap-1.5 text-sm text-emerald-600 font-medium">
              <Users size={14} />
              <span>{event.attendance_count}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
