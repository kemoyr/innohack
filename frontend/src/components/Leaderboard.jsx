import { useNavigate } from 'react-router-dom';
import { Star } from 'lucide-react';

const podiumStyles = [
  {
    bg: 'bg-gradient-to-r from-primary-50 to-primary-100',
    border: 'border-primary-300',
    text: 'text-neutral-900',
    badge: 'bg-primary-100 text-primary-800',
    rankBg: 'bg-primary-500 text-black',
  },
  {
    bg: 'bg-gradient-to-r from-neutral-50 to-neutral-100',
    border: 'border-neutral-200',
    text: 'text-neutral-700',
    badge: 'bg-neutral-100 text-neutral-600',
    rankBg: 'bg-neutral-400 text-white',
  },
  {
    bg: 'bg-gradient-to-r from-primary-50 to-primary-100',
    border: 'border-primary-400/30',
    text: 'text-primary-900',
    badge: 'bg-primary-200 text-primary-900',
    rankBg: 'bg-primary-700 text-white',
  },
];

export default function Leaderboard({ data, compact = false }) {
  const navigate = useNavigate();

  if (!data || data.length === 0) {
    return (
      <div className="text-center text-neutral-400 py-8">
        Нет данных для отображения
      </div>
    );
  }

  const top3 = data.slice(0, 3);
  const rest = compact ? [] : data.slice(3);
  const maxPoints = data[0]?.points || 1;

  return (
    <div className="space-y-2">
      {top3.map((person, idx) => {
        const style = podiumStyles[idx];
        return (
          <div
            key={person.id}
            onClick={() => navigate(`/volunteer/${person.id}`)}
            className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-200 hover:shadow-md ${style.bg} ${style.border}`}
          >
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${style.rankBg}`}>
              {idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <p className={`font-semibold ${style.text} text-sm truncate`}>
                {person.full_name}
              </p>
              {!compact && (
                <p className="text-xs text-neutral-500">{person.city}</p>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <Star size={13} className="text-primary-500" />
              <span className={`text-sm font-bold ${style.badge} px-2 py-0.5 rounded-lg`}>
                {person.points}
              </span>
            </div>
          </div>
        );
      })}

      {rest.map((person, idx) => {
        const rank = idx + 4;
        const barWidth = Math.max((person.points / maxPoints) * 100, 8);
        return (
          <div
            key={person.id}
            onClick={() => navigate(`/volunteer/${person.id}`)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200 hover:bg-neutral-50"
          >
            <span className="w-7 text-center text-sm font-semibold text-neutral-400">
              {rank}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-neutral-700 text-sm truncate">
                {person.full_name}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 h-1.5 bg-neutral-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-400/40 rounded-full transition-all duration-500"
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
                <span className="text-xs text-neutral-400 whitespace-nowrap">
                  {person.city}
                </span>
              </div>
            </div>
            <span className="font-semibold text-sm text-neutral-600">
              {person.points}
            </span>
          </div>
        );
      })}
    </div>
  );
}
