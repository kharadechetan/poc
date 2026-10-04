import { useEffect, useState } from 'react';
import { getScheduleHistory } from '../api';
import type { ScheduleHistoryResponse } from '../types/schemas';
import { History as HistoryIcon, Clock } from 'lucide-react';
import { format } from 'date-fns';

export const History = () => {
  const [history, setHistory] = useState<ScheduleHistoryResponse | null>(null);

  useEffect(() => {
    getScheduleHistory().then(res => setHistory(res.data)).catch(console.error);
  }, []);

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Schedule History</h1>
        <p className="text-slate-500 mt-1">Audit log of all scheduling and rescheduling events.</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
         <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-2">
            <HistoryIcon className="text-slate-500" size={20} />
            <h3 className="font-semibold text-slate-800">Event Timeline</h3>
          </div>
          <div className="p-6">
            {!history || (history.schedules.length === 0 && history.rescheduling_events.length === 0) ? (
              <div className="text-slate-500 text-center py-8">
                No history available.
              </div>
            ) : (
              <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
                
                {history.schedules.map((s, idx) => (
                  <div key={`s-${s.version}`} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-blue-100 text-blue-600 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                      <Clock size={18} />
                    </div>
                    
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="flex items-center justify-between mb-1">
                        <div className="font-bold text-slate-800 text-lg">Version {s.version}</div>
                        <div className="text-xs font-medium text-slate-500">
                          {format(new Date(s.created_at), 'dd MMM, HH:mm')}
                        </div>
                      </div>
                      <div className="text-slate-600 text-sm">
                        {idx === 0 ? 'Initial Schedule Generated' : 'Schedule Updated'}
                      </div>
                      <div className="mt-3 pt-3 border-t border-slate-100 text-sm text-slate-500 flex gap-4">
                        <span>Jobs: <strong>{s.metrics.scheduled_orders}</strong></span>
                        <span>Makespan: <strong>{s.metrics.makespan_minutes}m</strong></span>
                      </div>
                    </div>

                  </div>
                ))}

                {history.rescheduling_events.map((r) => (
                  <div key={`r-${r.id}`} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-purple-100 text-purple-600 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                      <HistoryIcon size={18} />
                    </div>
                    
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="flex items-center justify-between mb-1">
                        <div className="font-bold text-purple-700 text-lg">Rescheduling Event</div>
                        <div className="text-xs font-medium text-slate-500">
                          {(() => {
                            const sched = history.schedules.find(s => s.version === r.schedule_version);
                            return sched ? format(new Date(sched.created_at), 'dd MMM, HH:mm') : '';
                          })()}
                        </div>
                      </div>
                      <div className="text-slate-600 text-sm font-medium">
                        Triggered by breakdown (Event ID: {r.breakdown_event_id})
                      </div>
                      <div className="mt-3 pt-3 border-t border-slate-100 text-sm text-slate-500">
                        Affected Orders: <strong>{r.changes.length}</strong>
                      </div>
                    </div>

                  </div>
                ))}

              </div>
            )}
          </div>
      </div>
    </div>
  );
};
