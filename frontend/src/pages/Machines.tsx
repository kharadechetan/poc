import { useEffect, useState } from 'react';
import { getMachines, getSimulationState } from '../api';
import type { Machine } from '../types/schemas';
import { Factory } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';

export const Machines = () => {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [simState, setSimState] = useState<any>(null);

  useEffect(() => {
    getMachines().then(res => setMachines(res.data)).catch(console.error);
    getSimulationState().then(res => setSimState(res.data)).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Machines</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {machines.map(m => {
          const runningJob = simState?.running_orders_per_machine?.[m.id];
          const simStatus = simState ? 
            (runningJob ? 'RUNNING' : 
              (m.status === 'BROKEN_DOWN' ? 'BROKEN_DOWN' : 'IDLE')) : m.status;

          return (
            <div key={m.id} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
              <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
                    <Factory size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">{m.id}</h3>
                    <p className="text-xs text-slate-500 font-medium">{m.name}</p>
                  </div>
                </div>
                <StatusBadge status={simStatus} />
              </div>
              <div className="p-6 flex-1 space-y-4 text-sm">
                
                <div>
                  <div className="text-slate-500 font-medium mb-1">Capabilities</div>
                  <div className="flex flex-wrap gap-2">
                    {m.capabilities.map(c => (
                      <span key={c} className="bg-slate-100 text-slate-700 px-2 py-1 rounded text-xs font-semibold uppercase">{c}</span>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-slate-500 font-medium mb-1">Available From</div>
                    <div className="font-mono text-slate-700">{m.available_from}</div>
                  </div>
                  <div>
                    <div className="text-slate-500 font-medium mb-1">Available To</div>
                    <div className="font-mono text-slate-700">{m.available_to}</div>
                  </div>
                </div>

                {runningJob && (
                  <div className="pt-4 border-t border-slate-100">
                    <div className="text-slate-500 font-medium mb-1">Current Job</div>
                    <div className="font-bold text-blue-700 bg-blue-50 px-3 py-2 rounded-lg border border-blue-100 inline-block">
                      {runningJob}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  );
};
