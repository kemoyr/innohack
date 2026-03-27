import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Clock, CheckCircle2, XCircle, Upload, Loader2, CalendarDays, MapPin, Brain } from 'lucide-react';
import api from '../api';

const statusMap = {
  pending: { label: 'Ожидает проверки', icon: Clock, cls: 'bg-amber-100 text-amber-800' },
  planned: { label: 'Одобрено', icon: CheckCircle2, cls: 'bg-emerald-50 text-emerald-700' },
  completed: { label: 'Завершено', icon: CheckCircle2, cls: 'bg-blue-50 text-blue-700' },
  cancelled: { label: 'Отменено', icon: XCircle, cls: 'bg-neutral-100 text-neutral-500' },
  rejected: { label: 'Отклонено', icon: XCircle, cls: 'bg-red-50 text-red-700' },
};

export default function MyEvents() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', location_name: '', scheduled_date: '' });

  // Verification state
  const [verifying, setVerifying] = useState(null);
  const [verFiles, setVerFiles] = useState([]);
  const [verText, setVerText] = useState('');
  const [verResult, setVerResult] = useState(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchEvents();
  }, []);

  async function fetchEvents() {
    try {
      const data = await api.getMyEvents();
      setEvents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    setCreating(true);
    try {
      await api.createEvent(form);
      setShowCreate(false);
      setForm({ title: '', description: '', location_name: '', scheduled_date: '' });
      await fetchEvents();
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  }

  async function handleVerify(eventId) {
    if (verFiles.length === 0) return;
    const comment = verText.trim();
    if (comment.length < 10) return;
    setUploading(true);
    try {
      const fd = new FormData();
      verFiles.forEach((f) => fd.append('photos', f));
      fd.append('volunteer_comment', comment);

      // Try to get geolocation
      let lat = 0, lon = 0;
      try {
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
        });
        lat = pos.coords.latitude;
        lon = pos.coords.longitude;
      } catch {
        // Geolocation not available
      }
      fd.append('location_lat', lat);
      fd.append('location_lon', lon);

      const result = await api.uploadVerification(eventId, fd);
      setVerResult(result);
      await fetchEvents();
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-neutral-900">Мои мероприятия</h1>
          <p className="text-sm text-neutral-500 mt-0.5">{events.length} создано</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-primary-500 text-black rounded-xl text-sm font-bold hover:bg-primary-400 shadow-sm transition-all"
        >
          <Plus size={16} />
          Создать
        </button>
      </div>

      {/* Events list */}
      {events.length > 0 ? (
        <div className="space-y-3">
          {events.map((ev) => {
            const st = statusMap[ev.status] || statusMap.pending;
            const StIcon = st.icon;
            const isPending = ev.status === 'pending' && !ev.has_verification;
            const isVerifying = verifying === ev.id;

            return (
              <div key={ev.id} className="bg-white rounded-xl border border-neutral-200/60 p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-neutral-900 text-sm">{ev.title}</h3>
                    <div className="flex flex-wrap gap-3 mt-1.5 text-xs text-neutral-500">
                      {ev.location_name && (
                        <span className="flex items-center gap-1"><MapPin size={11} />{ev.location_name}</span>
                      )}
                      {ev.scheduled_date && (
                        <span className="flex items-center gap-1">
                          <CalendarDays size={11} />
                          {new Date(ev.scheduled_date).toLocaleDateString('ru-RU')}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold shrink-0 ${st.cls}`}>
                    <StIcon size={12} /> {st.label}
                  </span>
                </div>

                {/* Pending: show verification upload */}
                {isPending && !isVerifying && (
                  <button
                    onClick={() => { setVerifying(ev.id); setVerFiles([]); setVerText(''); setVerResult(null); }}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-800 rounded-lg text-xs font-semibold hover:bg-primary-200 transition-all"
                  >
                    <Upload size={14} />
                    Загрузить подтверждение
                  </button>
                )}

                {/* Verification form */}
                {isVerifying && !verResult && (
                  <div className="mt-3 p-4 bg-neutral-50 rounded-lg space-y-3">
                    <p className="text-xs font-semibold text-neutral-600">Фото и описание для координатора</p>
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      onChange={(e) => setVerFiles([...e.target.files])}
                      className="block w-full text-xs text-neutral-500 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-primary-100 file:text-primary-800 hover:file:bg-primary-200"
                    />
                    {verFiles.length > 0 && (
                      <p className="text-xs text-neutral-400">{verFiles.length} файл(ов) выбрано</p>
                    )}
                    <label className="block text-xs font-medium text-neutral-600 mt-2">
                      Текст о мероприятии (увидит координатор)
                    </label>
                    <textarea
                      value={verText}
                      onChange={(e) => setVerText(e.target.value)}
                      placeholder="Как прошло мероприятие, сколько было участников, что сделали…"
                      rows={4}
                      className="w-full px-3 py-2 border border-neutral-200 rounded-lg text-xs text-neutral-800 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 resize-y min-h-[88px]"
                    />
                    <p className="text-xs text-neutral-400">Геолокация запрашивается автоматически. ИИ оценивает уверенность; решение всегда за координатором.</p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleVerify(ev.id)}
                        disabled={uploading || verFiles.length === 0 || verText.trim().length < 10}
                        className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-black rounded-lg text-xs font-bold hover:bg-primary-400 transition-all disabled:opacity-50"
                      >
                        {uploading ? <Loader2 size={14} className="animate-spin" /> : <Brain size={14} />}
                        Отправить на модерацию
                      </button>
                      <button
                        onClick={() => { setVerifying(null); setVerResult(null); setVerText(''); }}
                        className="px-4 py-2 text-neutral-500 text-xs font-medium hover:text-neutral-700"
                      >
                        Отмена
                      </button>
                    </div>
                  </div>
                )}

                {/* Verification result */}
                {isVerifying && verResult && (
                  <div className="mt-3 p-4 rounded-lg bg-primary-50 border border-primary-200/60">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock size={16} className="text-primary-700" />
                      <span className="text-sm font-semibold text-neutral-800">
                        Отправлено на проверку координатору
                      </span>
                    </div>
                    <p className="text-xs text-neutral-600">
                      Уверенность модели:{' '}
                      <span className="font-bold text-primary-800">
                        {verResult.ai_confidence_percent ?? Math.round((verResult.ai_score || 0) * 100)}%
                      </span>
                    </p>
                    {verResult.ai_reasons?.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {verResult.ai_reasons.map((r, i) => (
                          <li key={i} className="text-xs text-neutral-600">• {r}</li>
                        ))}
                      </ul>
                    )}
                    <button
                      onClick={() => { setVerifying(null); setVerResult(null); }}
                      className="mt-2 text-xs text-neutral-500 hover:text-neutral-700"
                    >
                      Закрыть
                    </button>
                  </div>
                )}

                {/* Already verified but pending coordinator */}
                {ev.status === 'pending' && ev.has_verification && !isVerifying && (
                  <div className="mt-3 flex items-center gap-2 text-xs text-amber-600">
                    <Brain size={14} />
                    <span>Подтверждение загружено, ожидает проверки координатором</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-16">
          <CalendarDays size={32} className="mx-auto mb-3 text-neutral-300" />
          <p className="text-neutral-500 text-sm font-medium">У вас пока нет мероприятий</p>
          <button
            onClick={() => setShowCreate(true)}
            className="mt-4 px-4 py-2 bg-primary-500 text-black rounded-xl text-sm font-bold hover:bg-primary-400 transition-all"
          >
            Создать первое
          </button>
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 relative">
            <h2 className="text-base font-semibold text-neutral-900 mb-4">Новое мероприятие</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <input
                type="text"
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Название *"
                className="w-full px-3.5 py-2.5 border border-neutral-200 rounded-xl text-sm placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500"
              />
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Описание"
                rows={3}
                className="w-full px-3.5 py-2.5 border border-neutral-200 rounded-xl text-sm placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 resize-none"
              />
              <input
                type="text"
                value={form.location_name}
                onChange={(e) => setForm({ ...form, location_name: e.target.value })}
                placeholder="Место проведения"
                className="w-full px-3.5 py-2.5 border border-neutral-200 rounded-xl text-sm placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500"
              />
              <input
                type="datetime-local"
                required
                value={form.scheduled_date}
                onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })}
                className="w-full px-3.5 py-2.5 border border-neutral-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500"
              />
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="flex-1 py-2.5 border border-neutral-200 rounded-xl text-sm font-medium text-neutral-600 hover:bg-neutral-50"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 py-2.5 bg-primary-500 text-black rounded-xl text-sm font-bold hover:bg-primary-400 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {creating ? <Loader2 size={14} className="animate-spin" /> : null}
                  Создать
                </button>
              </div>
            </form>
            <p className="text-xs text-neutral-400 mt-3 text-center">
              После создания — фото, текст и модерация координатора
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
