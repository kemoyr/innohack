export default function StatsCard({ title, value, subtitle, icon: Icon, color = 'primary' }) {
  const colorMap = {
    primary: {
      iconBg: 'bg-primary-100',
      iconText: 'text-primary-700',
    },
    dark: {
      iconBg: 'bg-neutral-100',
      iconText: 'text-neutral-700',
    },
    accent: {
      iconBg: 'bg-accent-100',
      iconText: 'text-accent-600',
    },
    green: {
      iconBg: 'bg-emerald-100',
      iconText: 'text-emerald-600',
    },
    blue: {
      iconBg: 'bg-blue-100',
      iconText: 'text-blue-600',
    },
    purple: {
      iconBg: 'bg-purple-100',
      iconText: 'text-purple-600',
    },
    rose: {
      iconBg: 'bg-rose-100',
      iconText: 'text-rose-600',
    },
  };

  const scheme = colorMap[color] || colorMap.primary;

  return (
    <div className="bg-white rounded-xl border border-neutral-200/60 p-5 transition-all duration-200 hover:shadow-md hover:border-primary-300/50">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
            {title}
          </p>
          <p className="text-2xl font-bold text-neutral-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-sm text-neutral-500 mt-1">{subtitle}</p>
          )}
        </div>
        {Icon && (
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${scheme.iconBg}`}
          >
            <Icon size={20} className={scheme.iconText} />
          </div>
        )}
      </div>
    </div>
  );
}
