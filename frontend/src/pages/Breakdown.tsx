import { useEffect, useState } from 'react';
import { getMachines, simulateBreakdown, getAffectedOrders, getSimulationState, startSimulation, advanceSimulation } from '../api';
import type { Machine } from '../types/schemas';
import { AlertTriangle, Wrench, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';

export const Breakdown = () => {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [selectedMachine, setSelectedMachine] = useState<string>('');
  const [breakdownTime, setBreakdownTime] = useState<string>('');
  const [repairTime, setRepairTime] = useState<number>(120);
  
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [affectedOrders, setAffectedOrders] = useState<string[]>([]);
  const [simState, setSimState] = useState<any>(null);

  const fetchState = () => {
    getSimulationState().then(res => {
      setSimState(res.data);
      if (res.data.current_time) {
        const d = new Date(res.data.current_time);
        const pad = (n: number) => n.toString().padStart(2, '0');
        setBreakdownTime(`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`);
      }
    }).catch((e: any) => {
      if (e.response?.data?.detail === 'Simulation not started') {
        setSimState({ active: false });
      } else {
        console.error(e);
      }
    });
  };

  useEffect(() => {
    getMachines().then(res => {
      setMachines(res.data);
      if (res.data.length > 0) setSelectedMachine(res.data[0].id);
    }).catch(console.error);

    fetchState();
  }, []);

  const handleStartSimulation = async () => {
    setLoading(true);
    try {
      await startSimulation();
      fetchState();
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Failed to start simulation.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      // We might need to ensure simulation is started and advanced to this point before breakdown? 
      // The API walkthrough says: start, advance to time, then breakdown.
      // We'll just call breakdown. The backend takes care of it or throws error.
      // If it requires advance, we'll try to advance first if needed. But let's just follow direct breakdown call for simplicity unless it errors.
      
      // format time back to a string backend accepts easily, or rely on FlexibleModel
      const bt = breakdownTime; 
      await simulateBreakdown(selectedMachine, repairTime, bt);
      
      const [affectedRes] = await Promise.all([
        getAffectedOrders(),
        getSimulationState().then(r => setSimState(r.data))
      ]);
      
      setAffectedOrders(affectedRes.data);
      setSuccess(true);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Machine Breakdown Simulation</h1>
        <p className="text-slate-500 mt-1">Inject a disruptive event to observe the dynamic rescheduling capabilities.</p>
      </div>

      {simState && !simState.current_time && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm">
          <div>
            <h3 className="font-bold text-blue-800 text-lg">Simulation Not Started</h3>
            <p className="text-blue-600 mt-1 text-sm">You must start the simulation before injecting a breakdown event. This will load the latest schedule into the active state.</p>
          </div>
          <button 
            onClick={handleStartSimulation}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-md font-medium whitespace-nowrap shadow-sm disabled:opacity-50"
          >
            Start Simulation
          </button>
        </div>
      )}

      <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 ${simState && !simState.current_time ? 'opacity-50 pointer-events-none' : ''}`}>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-2">
            <AlertTriangle className="text-amber-500" size={20} />
            <h3 className="font-semibold text-slate-800">Configure Event</h3>
          </div>
          
          <form onSubmit={handleSimulate} className="p-6 space-y-4">
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 flex gap-3">
              <AlertTriangle className="shrink-0 mt-0.5" size={16} />
              <p>This will simulate a machine breakdown and allow you to test the dynamic rescheduling engine.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Select Machine</label>
              <select 
                value={selectedMachine} 
                onChange={e => setSelectedMachine(e.target.value)}
                className="w-full border-slate-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
                required
              >
                {machines.map(m => (
                  <option key={m.id} value={m.id}>{m.id} - {m.name} ({m.status})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Breakdown Time</label>
              <input 
                type="datetime-local" 
                value={breakdownTime}
                onChange={e => setBreakdownTime(e.target.value)}
                className="w-full border-slate-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
                required
              />
              {simState && simState.current_time && (
                <p className="text-xs text-slate-500 mt-1">Current simulation time: {format(new Date(simState.current_time), 'dd MMM yyyy HH:mm')}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Repair Duration (Minutes)</label>
              <div className="flex items-center gap-2">
                <input 
                  type="number" 
                  min="1"
                  value={repairTime}
                  onChange={e => setRepairTime(parseInt(e.target.value))}
                  className="flex-1 border-slate-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
                  required
                />
                <Wrench className="text-slate-400" size={20} />
              </div>
            </div>

            {error && <div className="text-red-600 text-sm font-medium">{error}</div>}

            <button 
              type="submit" 
              disabled={loading}
              className="w-full mt-4 bg-red-600 hover:bg-red-700 text-white py-2.5 rounded-md font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {loading ? 'Simulating...' : <><AlertTriangle size={18} /> Simulate Breakdown</>}
            </button>
          </form>
        </div>

        {success && (
          <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white rounded-xl border border-red-200 shadow-sm overflow-hidden border-t-4 border-t-red-500">
              <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-red-600 flex items-center gap-2 text-lg">
                    <AlertTriangle size={20} /> 
                    MACHINE BREAKDOWN
                  </h3>
                  <div className="text-slate-800 font-semibold text-xl mt-1">{selectedMachine}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</div>
                  <div className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm font-bold mt-1">BREAKDOWN</div>
                </div>
              </div>
              <div className="p-6 bg-slate-50 border-t border-slate-200">
                <div className="text-sm font-medium text-slate-500 mb-3 uppercase tracking-wider">Affected Work Orders</div>
                {affectedOrders.length > 0 ? (
                  <div className="space-y-2">
                    {affectedOrders.map(id => (
                      <div key={id} className="bg-white p-3 rounded-lg border border-red-100 flex items-center gap-3 shadow-sm">
                        <AlertTriangle className="text-red-500" size={16} />
                        <span className="font-semibold text-slate-700">{id}</span>
                        <span className="text-sm text-red-600 ml-auto font-medium">Interrupted</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-600 text-sm p-4 bg-green-50 rounded-lg border border-green-200 font-medium">
                    No active work orders were affected on this machine at the specified time.
                  </div>
                )}

                {affectedOrders.length > 0 && (
                  <div className="mt-6 flex justify-end">
                    <a href="/rescheduling" className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-5 py-2.5 rounded-md font-medium transition-colors shadow-sm">
                      Go to Rescheduling <ArrowRight size={18} />
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
