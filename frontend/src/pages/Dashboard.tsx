import { useEffect, useState } from 'react';
import { getMachines, getWorkOrders, getScheduleMetrics, getSimulationState, getSchedule } from '../api';
import type { Machine, WorkOrder, ScheduleMetrics, SimulationStateResponse, ScheduleResponse } from '../types/schemas';
import { KpiCard } from '../components/common/KpiCard';
import { Factory, Settings, CalendarCheck, Activity, Clock, AlertCircle } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { format } from 'date-fns';
import { clsx } from 'clsx';

export const Dashboard = () => {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [metrics, setMetrics] = useState<ScheduleMetrics | null>(null);
  const [simState, setSimState] = useState<SimulationStateResponse | null>(null);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);

  const fetchData = async () => {
    try {
      const [mRes, woRes, metRes, simRes, schRes] = await Promise.allSettled([
        getMachines(),
        getWorkOrders(),
        getScheduleMetrics(),
        getSimulationState(),
        getSchedule()
      ]);

      if (mRes.status === 'fulfilled') setMachines(mRes.value.data);
      if (woRes.status === 'fulfilled') setWorkOrders(woRes.value.data);
      if (metRes.status === 'fulfilled') setMetrics(metRes.value.data);
      if (simRes.status === 'fulfilled') setSimState(simRes.value.data);
      if (schRes.status === 'fulfilled') setSchedule(schRes.value.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <div className="flex gap-2">
          <button 
            onClick={async () => {
              try {
                await import('../api').then(m => m.resetAdmin());
                fetchData();
              } catch (e) {
                console.error(e);
              }
            }} 
            className="px-4 py-2 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm font-medium hover:bg-red-100 transition-colors shadow-sm"
          >
            Reset Database
          </button>
          <button onClick={fetchData} className="px-4 py-2 bg-white border border-slate-200 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm">
            Refresh Data
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        <KpiCard title="Total Machines" value={machines.length} icon={<Factory />} />
        <KpiCard title="Work Orders" value={workOrders.length} icon={<Settings />} />
        <KpiCard 
          title="Scheduled" 
          value={metrics ? `${metrics.scheduled_orders} / ${workOrders.length}` : '-'} 
          icon={<CalendarCheck />} 
        />
        <KpiCard 
          title="Machine Util." 
          value={metrics ? `${Math.round(metrics.overall_machine_utilization)}%` : '-'} 
          icon={<Activity />} 
        />
        <KpiCard 
          title="On-Time Orders" 
          value={metrics ? `${metrics.scheduled_orders - metrics.number_of_late_orders} / ${metrics.scheduled_orders}` : '-'} 
          icon={<Clock />} 
        />
        <KpiCard 
          title="Delayed Orders" 
          value={metrics?.number_of_late_orders ?? '-'} 
          icon={<AlertCircle />} 
          className={metrics?.number_of_late_orders && metrics.number_of_late_orders > 0 ? "border-red-200 bg-red-50" : ""}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-200">
            <h3 className="font-semibold text-slate-800">Production Status</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-medium">Machine</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Current Job</th>
                  <th className="px-6 py-3 font-medium">Utilization</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {machines.map(m => {
                  const runningJob = simState?.running_orders_per_machine?.[m.id];
                  const simStatus = simState ? 
                    (runningJob ? 'RUNNING' : 
                      (m.status === 'BROKEN_DOWN' ? 'BROKEN_DOWN' : 'IDLE')) : m.status;
                  const util = metrics?.machine_utilization?.[m.id];

                  return (
                    <tr key={m.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium text-slate-700">{m.id}</td>
                      <td className="px-6 py-4"><StatusBadge status={simStatus} /></td>
                      <td className="px-6 py-4 font-mono text-xs">{runningJob || '--'}</td>
                      <td className="px-6 py-4">
                        {util !== undefined ? (
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                              <div className="h-full bg-blue-500" style={{ width: `${util}%` }} />
                            </div>
                            <span className="text-xs font-medium text-slate-600">{Math.round(util)}%</span>
                          </div>
                        ) : '--'}
                      </td>
                    </tr>
                  )
                })}
                {machines.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">No machines found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-200">
            <h3 className="font-semibold text-slate-800">Active Schedule Overview</h3>
          </div>
          <div className="p-6 overflow-x-auto flex-1">
            {schedule && schedule.schedule.length > 0 ? (
               <div className="space-y-4">
                 {machines.map(m => {
                   const machineJobs = schedule.schedule.filter(s => s.machine_id === m.id).sort((a,b) => new Date(a.setup_start).getTime() - new Date(b.setup_start).getTime());
                   return (
                     <div key={m.id} className="flex flex-col gap-1">
                       <div className="text-xs font-semibold text-slate-500">{m.id}</div>
                       <div className="flex h-10 bg-slate-100 rounded-md overflow-hidden relative">
                         {machineJobs.map((job) => {
                           // For visual purposes in overview, just render them in order with equal width chunks, or we'd need a real timeline.
                           // A real timeline requires calculating start/end offset percentages based on a min/max time window.
                           // Let's do a simple flex layout for the overview.
                           const isDelayed = job.lateness_minutes > 0;
                           const isRescheduled = job.status === 'RESCHEDULED';
                           return (
                             <div 
                               key={job.work_order_id} 
                               className={clsx(
                                 "flex-1 border-r border-white/20 px-2 py-1 flex items-center justify-center min-w-0 transition-colors cursor-default group relative",
                                 isDelayed ? 'bg-red-500' : isRescheduled ? 'bg-purple-500' : 'bg-blue-500',
                                 "hover:brightness-110"
                               )}
                             >
                               <span className="truncate text-xs font-medium text-white group-hover:opacity-0 transition-opacity">
                                 {job.work_order_id}
                               </span>
                               <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-[10px] text-white font-bold px-1 text-center leading-tight">
                                 {format(new Date(job.setup_start), 'HH:mm')} - {format(new Date(job.production_end), 'HH:mm')}
                               </div>
                             </div>
                           )
                         })}
                         {machineJobs.length === 0 && <div className="flex-1 flex items-center justify-center text-xs text-slate-400">No jobs assigned</div>}
                       </div>
                     </div>
                   );
                 })}
               </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 py-12">
                <CalendarCheck size={48} className="mb-4 text-slate-300" />
                <p>No production schedule available.</p>
                <p className="text-sm mt-1">Generate a schedule to view the production timeline.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
