import { clsx } from 'clsx';


interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  if (!status) return <span className="px-2.5 py-1 text-xs font-semibold rounded-full border bg-slate-100 text-slate-700 border-slate-200">--</span>;

  let colorClass = 'bg-slate-100 text-slate-700 border-slate-200';
  const upper = String(status).toUpperCase();

  // Priority
  if (upper === 'URGENT') colorClass = 'bg-red-100 text-red-700 border-red-200';
  else if (upper === 'HIGH') colorClass = 'bg-orange-100 text-orange-700 border-orange-200';
  else if (upper === 'MEDIUM') colorClass = 'bg-blue-100 text-blue-700 border-blue-200';
  else if (upper === 'LOW') colorClass = 'bg-slate-100 text-slate-700 border-slate-200';
  
  // Machine Status
  else if (upper === 'AVAILABLE') colorClass = 'bg-green-100 text-green-700 border-green-200';
  else if (upper === 'UNAVAILABLE') colorClass = 'bg-slate-100 text-slate-700 border-slate-200';
  else if (upper === 'BROKEN_DOWN') colorClass = 'bg-red-100 text-red-700 border-red-200';
  
  // Schedule Status
  else if (upper === 'WAITING') colorClass = 'bg-yellow-100 text-yellow-700 border-yellow-200';
  else if (upper === 'RUNNING') colorClass = 'bg-blue-100 text-blue-700 border-blue-200';
  else if (upper === 'COMPLETED') colorClass = 'bg-green-100 text-green-700 border-green-200';
  else if (upper === 'INTERRUPTED') colorClass = 'bg-red-100 text-red-700 border-red-200';
  else if (upper === 'RESCHEDULED') colorClass = 'bg-purple-100 text-purple-700 border-purple-200';
  
  // On Time / Delayed
  else if (upper === 'ON TIME') colorClass = 'bg-green-100 text-green-700 border-green-200';
  else if (upper === 'DELAYED') colorClass = 'bg-red-100 text-red-700 border-red-200';
  
  return (
    <span className={clsx("px-2.5 py-1 text-xs font-semibold rounded-full border", colorClass)}>
      {String(status).replace(/_/g, ' ')}
    </span>
  );
};
