import { useEffect, useState, useMemo } from 'react';
import { getSchedule, generateSchedule, getScheduleMetrics, getMachines } from '../api';
import type { ScheduleResponse, ScheduleMetrics, Machine } from '../types/schemas';
import { } from '../components/common/StatusBadge';
import { format } from 'date-fns';
import { CalendarRange, Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';

export const Schedule = () => {
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [metrics, setMetrics] = useState<ScheduleMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [schRes, metRes, mRes] = await Promise.allSettled([
        getSchedule(),
        getScheduleMetrics(),
        getMachines()
      ]);
      if (schRes.status === 'fulfilled') setSchedule(schRes.value.data);
      if (metRes.status === 'fulfilled') setMetrics(metRes.value.data);
      if (mRes.status === 'fulfilled') setMachines(mRes.value.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await generateSchedule();
      setSchedule(res.data);
      setSuccess(`✓ Schedule generated successfully. ${res.data.metrics.scheduled_orders} work orders scheduled. ${Object.keys(res.data.metrics.machine_utilization).length} machines utilized.`);
      await fetchData();
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Unable to generate schedule.');
    } finally {
      setLoading(false);
    }
  };

  const timelineData = useMemo(() => {
    if (!schedule || !schedule.schedule || schedule.schedule.length === 0) return null;
    
    // Find min and max time for the entire schedule
    let minTime = new Date(schedule.schedule[0].setup_start).getTime();
    let maxTime = new Date(schedule.schedule[0].production_end).getTime();

    schedule.schedule.forEach(job => {
      const start = new Date(job.setup_start).getTime();
      const end = new Date(job.production_end).getTime();
      if (start < minTime) minTime = start;
      if (end > maxTime) maxTime = end;
    });

    const totalDuration = Math.max(1, (maxTime - minTime) / 60000); // in minutes

    return { minTime, maxTime, totalDuration };
  }, [schedule]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Production Schedule</h1>
        <button 
          onClick={handleGenerate} 
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              Generating...
            </span>
          ) : (
            <span className="flex items-center gap-2"><Play size={16} /> Generate Initial Schedule</span>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="mt-0.5 shrink-0" size={18} />
          <div>
            <h4 className="font-semibold">Generation Failed</h4>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 text-green-700 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 shrink-0" size={18} />
          <div>
            <p className="text-sm font-medium">{success}</p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col min-h-[500px]">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
          <h3 className="font-semibold text-slate-800">Gantt Timeline</h3>
          {metrics && (
             <div className="text-sm text-slate-500 font-medium flex gap-4">
               <span>Makespan: <strong className="text-slate-800">{metrics.makespan_minutes} min</strong></span>
               <span>Late Orders: <strong className={metrics.number_of_late_orders > 0 ? "text-red-600" : "text-green-600"}>{metrics.number_of_late_orders}</strong></span>
             </div>
          )}
        </div>
        
        <div className="p-6 overflow-x-auto flex-1 relative">
          {!timelineData ? (
             <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
               <CalendarRange size={48} className="mb-4 text-slate-300" />
               <p>No production schedule available.</p>
               <p className="text-sm mt-1">Generate a schedule to view the production timeline.</p>
             </div>
          ) : (
            <div className="min-w-[800px]">
              {/* Timeline Header (Hours) */}
              <div className="flex border-b border-slate-200 pb-2 mb-4 ml-24 relative h-6">
                {/* Add simple hour ticks based on duration, but just showing relative position for now */}
                <div className="absolute left-0 text-xs text-slate-400 font-medium transform -translate-x-1/2">{format(new Date(timelineData.minTime), 'HH:mm')}</div>
                <div className="absolute left-[50%] text-xs text-slate-400 font-medium transform -translate-x-1/2">{format(new Date(timelineData.minTime + (timelineData.maxTime - timelineData.minTime)/2), 'HH:mm')}</div>
                <div className="absolute right-0 text-xs text-slate-400 font-medium transform translate-x-1/2">{format(new Date(timelineData.maxTime), 'HH:mm')}</div>
              </div>

              {/* Machine Rows */}
              <div className="space-y-6">
                {machines.map(m => {
                  const machineJobs = schedule?.schedule?.filter(s => s.machine_id === m.id) || [];
                  if (machineJobs.length === 0) return null;

                  return (
                    <div key={m.id} className="flex items-center gap-4">
                      <div className="w-20 shrink-0 font-medium text-sm text-slate-700">{m.id}</div>
                      <div className="flex-1 h-12 bg-slate-50 rounded-lg relative border border-slate-100">
                        {machineJobs.map(job => {
                          const start = new Date(job.setup_start).getTime();
                          const end = new Date(job.production_end).getTime();
                          
                          const leftPerc = ((start - timelineData.minTime) / (timelineData.totalDuration * 60000)) * 100;
                          const widthPerc = ((end - start) / (timelineData.totalDuration * 60000)) * 100;

                          const isDelayed = job.lateness_minutes > 0;
                          const isRescheduled = job.status === 'RESCHEDULED';

                          return (
                            <div 
                              key={job.work_order_id}
                              className={clsx(
                                "absolute top-1 bottom-1 rounded shadow-sm border flex items-center justify-center overflow-hidden group cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-md",
                                isDelayed ? 'bg-red-500 border-red-600 text-white' : 
                                isRescheduled ? 'bg-purple-500 border-purple-600 text-white' : 
                                'bg-blue-500 border-blue-600 text-white'
                              )}
                              style={{ left: `${leftPerc}%`, width: `${widthPerc}%` }}
                            >
                              <span className="text-xs font-semibold px-1 truncate">{job.work_order_id}</span>
                              
                              {/* Tooltip */}
                              <div className="hidden group-hover:block absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-48 bg-slate-900 text-white text-xs rounded p-3 shadow-xl z-10 whitespace-normal text-left">
                                <div className="font-bold border-b border-slate-700 pb-1 mb-1">WO: {job.work_order_id}</div>
                                <div className="grid grid-cols-2 gap-1 mt-2">
                                  <span className="text-slate-400">Machine:</span> <span>{job.machine_id}</span>
                                  <span className="text-slate-400">Start:</span> <span>{format(new Date(job.setup_start), 'HH:mm')}</span>
                                  <span className="text-slate-400">End:</span> <span>{format(new Date(job.production_end), 'HH:mm')}</span>
                                  <span className="text-slate-400">Setup:</span> <span>{job.setup_duration_minutes}m</span>
                                  <span className="text-slate-400">Process:</span> <span>{job.processing_duration_minutes}m</span>
                                  <span className="text-slate-400">Status:</span> <span>{job.status}</span>
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
