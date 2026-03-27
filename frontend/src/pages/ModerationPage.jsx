import { useState, useEffect } from 'react';
import { ShieldCheck, ShieldX, Clock, CheckCircle2, XCircle, Loader2, History, AlertTriangle, MapPin, CalendarDays, User, Brain, MessageSquare } from 'lucide-react';
import api from '../api';

export default function ModerationPage() {
  const [queue, setQueue] = useState([]);
  const [history, setHistory] = useState([]);
  const [tab, setTab] = useState('queue');
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [q, h] = await Promise.all([
        api.getModerationQueue(),
        api.getModerationHistory(),
      ]);
      setQueue(q);
      setHistory(h);
    } catch (err) {
      console.error('Moderation fetch error:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDecision(eventId, action, comment = '') {
    setActing(eventId);
    try {
      await api.moderateEvent(eventId, { action, comment });
      await fetchData();
    } catch (err) {
      console.error('Moderation error:', err);
    } finally {
      setActing(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Модерация</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          Проверка мероприятий от волонтёров
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setTab('queue')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            tab === 'queue'
              ? 'bg-primary-500 text-black shadow-md'
              : 'bg-white text-neutral-600 border border-neutral-200 hover:bg-neutral-50'
          }`}
        >
          <AlertTriangle size={15} />
          На проверке
          {queue.length > 0 && (
            <span className={`px-1.5 py-0.5 rounded-md text-xs font-bold ${
              tab === 'queue' ? 'bg-black/10' : 'bg-red-100 text-red-600'
            }`}>
              {queue.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setTab('history')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            tab === 'history'
              ? 'bg-primary-500 text-black shadow-md'
              : 'bg-white text-neutral-600 border border-neutral-200 hover:bg-neutral-50'
          }`}
        >
          <History size={15} />
          История
          <span className={`px-1.5 py-0.5 rounded-md text-xs font-semibold ${
            tab === 'history' ? 'bg-black/10' : 'bg-neutral-100 text-neutral-500'
          }`}>
            {history.length}
          </span>
        </button>
      </div>

      {tab === 'queue' ? (
        queue.length > 0 ? (
          <div className="space-y-4">
            {queue.map((item) => (
              <div key={item.id} className="bg-white rounded-xl border border-neutral-200/60 p-6">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-neutral-900">{item.event_title}</h3>
                    <div className="flex flex-wrap gap-3 mt-2 text-xs text-neutral-500">
                      <span className="flex items-center gap-1">
                        <User size={12} /> {item.volunteer_name}
                      </span>
                      {item.location_name && (
                        <span className="flex items-center gap-1">
                          <MapPin size={12} /> {item.location_name}
                        </span>
                      )}
                      {item.scheduled_date && (
                        <span className="flex items-center gap-1">
                          <CalendarDays size={12} /> {new Date(item.scheduled_date).toLocaleDateString('ru-RU')}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="px-2.5 py-1 bg-amber-100 text-amber-800 rounded-lg text-xs font-semibold flex items-center gap-1">
                    <Clock size={12} /> Ожидает
                  </span>
                </div>

                {item.volunteer_comment?.trim() ? (
                  <div className="bg-primary-50/60 border border-primary-100 rounded-lg p-4 mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <MessageSquare size={14} className="text-primary-700" />
                      <span className="text-xs font-semibold text-neutral-700">Текст от волонтёра</span>
                    </div>
                    <p className="text-sm text-neutral-800 whitespace-pre-wrap">{item.volunteer_comment.trim()}</p>
                  </div>
                ) : null}

                {/* AI reference confidence */}
                <div className="bg-neutral-50 rounded-lg p-4 mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain size={14} className="text-neutral-500" />
                    <span className="text-xs font-semibold text-neutral-600">Справка ИИ</span>
                    <span className="text-xs font-bold text-primary-800 ml-auto">
                      Уверенность модели:{' '}
                      {item.ai_confidence_percent ?? Math.round((item.ai_score || 0) * 100)}%
                    </span>
                  </div>
                  {item.ai_reasons && item.ai_reasons.length > 0 ? (
                    <ul className="space-y-1">
                      {item.ai_reasons.map((reason, i) => (
                        <li key={i} className="text-xs text-neutral-600 flex items-start gap-1.5">
                          <span className="text-neutral-400 shrink-0 mt-0.5">•</span>
                          {reason}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-neutral-400">Нет пояснений</p>
                  )}
                </div>

                {/* Geo info */}
                {(item.location_lat || item.location_lon) && (
                  <p className="text-xs text-neutral-400 mb-4">
                    Координаты: {item.location_lat?.toFixed(4)}, {item.location_lon?.toFixed(4)}
                  </p>
                )}

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    onClick={() => handleDecision(item.event_id, 'approve')}
                    disabled={acting === item.event_id}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-all disabled:opacity-50"
                  >
                    {acting === item.event_id ? <Loader2 size={14} className="animate-spin" /> : <ShieldCheck size={14} />}
                    Одобрить
                  </button>
                  <button
                    onClick={() => handleDecision(item.event_id, 'reject', 'Отклонено координатором')}
                    disabled={acting === item.event_id}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-white border border-red-200 text-red-600 rounded-xl text-sm font-medium hover:bg-red-50 transition-all disabled:opacity-50"
                  >
                    <ShieldX size={14} />
                    Отклонить
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <CheckCircle2 size={32} className="mx-auto mb-3 text-emerald-300" />
            <p className="text-neutral-500 text-sm font-medium">Все мероприятия проверены</p>
            <p className="text-xs text-neutral-400 mt-1">Очередь на модерацию пуста</p>
          </div>
        )
      ) : (
        /* History tab */
        history.length > 0 ? (
          <div className="bg-white rounded-xl border border-neutral-200/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-neutral-50/80">
                    <th className="text-left px-5 py-3 text-xs font-semibold text-neutral-500 uppercase">Мероприятие</th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-neutral-500 uppercase">Волонтёр</th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-neutral-500 uppercase max-w-[200px]">Текст</th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-neutral-500 uppercase">Уверенн.</th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-neutral-500 uppercase">Статус</th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-neutral-500 uppercase">Дата</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-50">
                  {history.map((item) => (
                    <tr key={item.id} className="hover:bg-neutral-50/50">
                      <td className="px-5 py-3 text-sm text-neutral-800 font-medium">{item.event_title}</td>
                      <td className="px-5 py-3 text-sm text-neutral-500">{item.volunteer_name}</td>
                      <td className="px-5 py-3 text-xs text-neutral-600 max-w-[220px]">
                        <span className="line-clamp-2" title={item.volunteer_comment || ''}>
                          {(item.volunteer_comment || '').trim() || '—'}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-xs font-semibold text-neutral-700">
                          {item.ai_confidence_percent ?? Math.round((item.ai_score || 0) * 100)}%
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        {item.event_status === 'planned' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-md text-xs font-semibold">
                            <CheckCircle2 size={11} /> Одобрено
                          </span>
                        ) : item.event_status === 'rejected' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-50 text-red-700 rounded-md text-xs font-semibold">
                            <XCircle size={11} /> Отклонено
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-50 text-amber-700 rounded-md text-xs font-semibold">
                            <Clock size={11} /> Ожидает
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-xs text-neutral-400">
                        {new Date(item.created_at).toLocaleDateString('ru-RU')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="text-center py-16">
            <History size={32} className="mx-auto mb-3 text-neutral-300" />
            <p className="text-neutral-500 text-sm font-medium">История пуста</p>
          </div>
        )
      )}
    </div>
  );
}
