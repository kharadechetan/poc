import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Settings, Factory, CalendarRange, AlertTriangle, RefreshCcw, History } from 'lucide-react';
import { clsx } from 'clsx';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/machines', label: 'Machines', icon: Factory },
  { path: '/work-orders', label: 'Work Orders', icon: Settings },
  { path: '/schedule', label: 'Schedule', icon: CalendarRange },
  { path: '/breakdown', label: 'Breakdown Simulation', icon: AlertTriangle },
  { path: '/rescheduling', label: 'Rescheduling', icon: RefreshCcw },
  { path: '/history', label: 'History', icon: History },
];

export const Sidebar = () => {
  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen fixed left-0 top-0">
      <div className="p-4 bg-slate-950 text-white text-lg font-bold flex items-center gap-2">
        <Factory size={24} className="text-blue-500" />
        AI Scheduler POC
      </div>
      <nav className="flex-1 py-4 flex flex-col gap-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-4 py-3 mx-2 rounded-md transition-colors',
              isActive ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 hover:text-white'
            )}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-4 text-xs text-slate-500 border-t border-slate-800">
        Demo Version
      </div>
    </aside>
  );
};
