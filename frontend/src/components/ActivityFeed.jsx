import { useState, useEffect } from 'react';
import { UserPlus, FileCheck, Award, CalendarPlus, Activity, Loader2 } from 'lucide-react';
import api from '../api';

const typeConfig = {
  volunteer: {
    icon: UserPlus,
    bg: 'bg-blue-100',
    text: 'text-blue-600',
  },
  submission: {
    icon: FileCheck,
    bg: 'bg-emerald-100',
    text: 'text-emerald-600',
  },
  achievement: {
    icon: Award,
    bg: 'bg-amber-100',
    text: 'text-amber-600',
  },
  event: {
    icon: CalendarPlus,
    bg: 'bg-purple-100',
    text: 'text-purple-600',
  },
};

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'только что';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    if (minutes === 1) return '1 минуту назад';
    if (minutes < 5) return `${minutes} минуты назад`;
    return `${minutes} минут назад`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    if (hours === 1) return '1 час назад';
    if (hours < 5) return `${hours} часа назад`;
    return `${hours} часов назад`;
  }
  const days = Math.floor(hours / 24);
  if (days === 1) return 'вчера';
  if (days < 7) {
    if (days < 5) return `${days} дня назад`;
    return `${days} дней назад`;
  }
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

export default function ActivityFeed() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchActivity() {
      try {
        const data = await api.getActivity();
        setActivities(data);
      } catch {
        // Activity feed is optional, fail silently
        setActivities([]);
      } finally {
        setLoading(false);
      }
    }
    fetchActivity();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-primary-500" />
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-slate-400">
        <Activity size={24} className="mb-2" />
        <p className="text-sm">Нет недавних действий</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {activities.slice(0, 10).map((item, idx) => {
        const config = typeConfig[item.type] || typeConfig.event;
        const Icon = config.icon;
        return (
          <div
            key={idx}
            className="flex items-start gap-3 py-2.5 px-1 rounded-lg transition-colors hover:bg-slate-50"
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${config.bg}`}>
              <Icon size={14} className={config.text} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-700 leading-snug">
                {item.description}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                {timeAgo(item.created_at)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
