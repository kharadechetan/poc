import { clsx } from 'clsx';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  className?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({ title, value, subtitle, icon, className }) => {
  return (
    <div className={clsx("bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col", className)}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">{title}</h3>
        {icon && <div className="text-blue-500">{icon}</div>}
      </div>
      <div className="text-3xl font-bold text-slate-800">{value}</div>
      {subtitle && <p className="text-sm text-slate-500 mt-2 font-medium">{subtitle}</p>}
    </div>
  );
};
