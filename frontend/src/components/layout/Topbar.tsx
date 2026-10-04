import { useEffect, useState } from 'react';
import { getHealth } from '../../api';

export const Topbar = () => {
  const [health, setHealth] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const { data } = await getHealth();
        setHealth(data.status === 'ok');
      } catch (e) {
        setHealth(false);
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 sticky top-0 z-10 shadow-sm">
      <h1 className="text-xl font-semibold text-slate-800">Manufacturing Dashboard</h1>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-slate-600">Backend</span>
        <div className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
          <div className={`w-2.5 h-2.5 rounded-full ${health === true ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : health === false ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]' : 'bg-slate-300'}`} />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
            {health === true ? 'Online' : health === false ? 'Offline' : 'Checking'}
          </span>
        </div>
      </div>
    </header>
  );
};
