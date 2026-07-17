import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Loader2, AlertCircle, Mail } from 'lucide-react';
import api, { setToken, setUser } from '../api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp;
      tg.ready();
      tg.expand();
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await api.login({ email, password });
      setToken(data.token);
      setUser({ role: data.role, user_id: data.user_id, full_name: data.full_name });
      navigate('/');
    } catch (err) {
      setError(err.message || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-bee-black px-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-500/8 rounded-full blur-3xl" />
        <div className="absolute top-0 left-0 w-full h-2 bg-primary-500" />
      </div>

      <div className="relative w-full max-w-sm">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-primary-500 rounded-2xl mb-4 shadow-lg shadow-primary-500/30">
              <span className="text-black font-extrabold text-xl">V+</span>
            </div>
            <h1 className="text-2xl font-bold text-neutral-900">
              Volunteer<span className="text-primary-500">+</span>
            </h1>
            <p className="text-neutral-500 mt-1 text-sm">Вход в систему</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                required
                autoFocus
                className="w-full pl-10 pr-4 py-3 border border-neutral-200 rounded-xl text-sm placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 transition-all"
              />
            </div>

            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Пароль"
                required
                className="w-full pl-10 pr-4 py-3 border border-neutral-200 rounded-xl text-sm placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 transition-all"
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                <AlertCircle size={16} className="shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary-500 text-black font-bold rounded-xl shadow-lg shadow-primary-500/30 hover:bg-primary-400 transition-all disabled:opacity-50 text-sm"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" /> Вход...
                </span>
              ) : 'Войти'}
            </button>
          </form>

          <p className="text-center text-sm text-neutral-500 mt-5">
            Нет аккаунта?{' '}
            <Link to="/register" className="text-primary-700 font-medium hover:text-primary-800">
              Зарегистрироваться
            </Link>
          </p>

          <Link
            to="/"
            className="block text-center text-xs text-neutral-400 mt-4 hover:text-neutral-600 transition-colors"
          >
            Смотреть без регистрации
          </Link>
        </div>

        <p className="text-center text-neutral-600 text-xs mt-6">Volunteer+ 2026</p>
      </div>
    </div>
  );
}
