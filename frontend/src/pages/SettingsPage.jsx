import { Settings, Server, Bot, User, ExternalLink, Globe, Shield } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Настройки</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          Информация о системе и профиле
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Info */}
        <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
          <div className="flex items-center gap-2 mb-5">
            <Server size={16} className="text-neutral-400" />
            <h2 className="text-sm font-semibold text-neutral-900">Информация о системе</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2.5 border-b border-neutral-100">
              <span className="text-sm text-neutral-500">Версия</span>
              <span className="text-sm font-medium text-neutral-900">1.0.0</span>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-neutral-100">
              <span className="text-sm text-neutral-500">База данных</span>
              <span className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-600">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Подключена
              </span>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-neutral-100">
              <span className="text-sm text-neutral-500">Telegram бот</span>
              <span className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-600">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Активен
              </span>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-sm text-neutral-500">Среда</span>
              <span className="text-sm font-medium text-neutral-900">Production</span>
            </div>
          </div>
        </div>

        {/* Profile */}
        <div className="bg-white rounded-xl border border-neutral-200/60 p-6">
          <div className="flex items-center gap-2 mb-5">
            <User size={16} className="text-neutral-400" />
            <h2 className="text-sm font-semibold text-neutral-900">Ваш профиль</h2>
          </div>
          <div className="flex items-center gap-4 mb-6">
            <div className="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center">
              <Shield size={24} className="text-primary-700" />
            </div>
            <div>
              <p className="font-semibold text-neutral-900">Координатор</p>
              <p className="text-sm text-neutral-500">Полный доступ к панели управления</p>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2.5 border-b border-neutral-100">
              <span className="text-sm text-neutral-500">Роль</span>
              <span className="px-2.5 py-1 bg-primary-100 text-primary-800 rounded-lg text-xs font-semibold">
                Администратор
              </span>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-sm text-neutral-500">Авторизация</span>
              <span className="text-sm font-medium text-neutral-900">Пароль</span>
            </div>
          </div>
        </div>

        {/* Links */}
        <div className="bg-white rounded-xl border border-neutral-200/60 p-6 lg:col-span-2">
          <div className="flex items-center gap-2 mb-5">
            <Globe size={16} className="text-neutral-400" />
            <h2 className="text-sm font-semibold text-neutral-900">Ссылки</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-4 rounded-xl border border-neutral-200/60 hover:bg-neutral-50 hover:border-primary-300/50 transition-all group"
            >
              <div className="w-10 h-10 bg-neutral-100 rounded-xl flex items-center justify-center">
                <Server size={18} className="text-neutral-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-neutral-800">API документация</p>
                <p className="text-xs text-neutral-500">Swagger / OpenAPI</p>
              </div>
              <ExternalLink size={14} className="text-neutral-400 group-hover:text-primary-600 transition-colors" />
            </a>
            <a
              href="https://t.me/Beeline_dashboard_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-4 rounded-xl border border-neutral-200/60 hover:bg-neutral-50 hover:border-primary-300/50 transition-all group"
            >
              <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center">
                <Bot size={18} className="text-primary-700" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-neutral-800">Telegram бот</p>
                <p className="text-xs text-neutral-500">Volunteer+ Bot</p>
              </div>
              <ExternalLink size={14} className="text-neutral-400 group-hover:text-primary-600 transition-colors" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
