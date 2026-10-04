import { useState } from 'react';
import { reschedule, } from '../api';
import type { RescheduleResponse } from '../types/schemas';
import { RefreshCcw, CheckCircle2, ArrowRight, ShieldAlert } from 'lucide-react';
import { format } from 'date-fns';

export const Rescheduling = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RescheduleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleReschedule = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await reschedule();
      setResult(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Rescheduling failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">AI Rescheduling Recommendation</h1>
          <p className="text-slate-500 mt-1">Automatically resolve disruptions and optimize the revised schedule.</p>
        </div>
        
        <button 
          onClick={handleReschedule} 
          disabled={loading || !!result}
          className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm font-medium transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? 'Processing AI constraints...' : <><RefreshCcw size={18} /> Trigger Rescheduling</>}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg">
          <p className="font-semibold text-sm">{error}</p>
        </div>
      )}

      {result && (
        <div className="space-y-6 animate-in fade-in duration-700">
          
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-purple-50">
              <h3 className="font-semibold text-purple-900 flex items-center gap-2">
                <ShieldAlert size={18} className="text-purple-600" /> 
                Rescheduling Summary
              </h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                 <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                    <div className="text-sm text-slate-500 font-medium mb-1">Orders Rescheduled</div>
                    <div className="text-2xl font-bold text-slate-800">{result.changes.length}</div>
                 </div>
                 <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                    <div className="text-sm text-slate-500 font-medium mb-1">Previous Makespan</div>
                    <div className="text-2xl font-bold text-slate-800">{result.optimization_metrics_before.makespan_minutes}m</div>
                 </div>
                 <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                    <div className="text-sm text-slate-500 font-medium mb-1">New Makespan</div>
                    <div className="text-2xl font-bold text-slate-800">{result.optimization_metrics_after.makespan_minutes}m</div>
                 </div>
              </div>

              <h4 className="font-semibold text-slate-800 mb-4 text-lg">AI Decisions</h4>
              <div className="space-y-4">
                {result.changes.map((change) => {
                  const reason = result.reasons.find(r => r.work_order_id === change.work_order_id)?.reason || 'Re-optimized for capacity constraints.';
                  return (
                    <div key={change.work_order_id} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                      <div className="p-4 border-b border-slate-100 flex items-center gap-4">
                        <div className="font-bold text-lg text-slate-700 w-24">{change.work_order_id}</div>
                        <div className="flex-1 flex items-center gap-6">
                          <div className="flex flex-col">
                            <span className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Original</span>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-slate-800 bg-slate-100 px-2 py-1 rounded text-sm">{change.from_machine}</span>
                              <span className="text-sm text-slate-600 font-mono">{format(new Date(change.old_start), 'HH:mm')}</span>
                            </div>
                          </div>
                          
                          <ArrowRight className="text-slate-300" size={24} />
                          
                          <div className="flex flex-col">
                            <span className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Revised</span>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-purple-700 bg-purple-100 px-2 py-1 rounded text-sm">{change.to_machine}</span>
                              <span className="text-sm text-slate-600 font-mono">{format(new Date(change.new_start), 'HH:mm')}</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`text-sm font-bold ${change.delay_delta_minutes > 0 ? 'text-amber-600' : 'text-green-600'}`}>
                            {change.delay_delta_minutes > 0 ? `+${change.delay_delta_minutes}m delay` : 'No added delay'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="p-4 bg-slate-50 text-sm">
                        <div className="font-semibold text-slate-700 mb-2">Why was {change.work_order_id} moved?</div>
                        <ul className="space-y-1.5">
                          {/* If backend returns bullet points in string or we format it. The backend provides plain english. */}
                          <li className="flex items-start gap-2 text-slate-600">
                            <CheckCircle2 size={16} className="text-green-500 shrink-0 mt-0.5" />
                            <span>{reason}</span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  )
                })}
                {result.changes.length === 0 && (
                  <div className="text-slate-500 p-4 border border-slate-200 rounded-lg text-center bg-slate-50">
                    No orders needed to be moved.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {!result && !loading && !error && (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
           <RefreshCcw size={48} className="mx-auto mb-4 text-slate-300" />
           <h3 className="text-lg font-medium text-slate-800">Ready to Reschedule</h3>
           <p className="text-slate-500 mt-2">Trigger the AI to resolve conflicts and rebuild the production schedule.</p>
        </div>
      )}
    </div>
  );
};
