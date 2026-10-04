import { useEffect, useState } from 'react';
import { getWorkOrders, getSimulationState } from '../api';
import type { WorkOrder } from '../types/schemas';
import { StatusBadge } from '../components/common/StatusBadge';
import { format } from 'date-fns';

export const WorkOrders = () => {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [simState, setSimState] = useState<any>(null);
  
  const [search, setSearch] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  useEffect(() => {
    getWorkOrders().then(res => setWorkOrders(res.data)).catch(console.error);
    getSimulationState().then(res => setSimState(res.data)).catch(console.error);
  }, []);

  const filtered = workOrders.filter(wo => {
    if (search && !wo.id.toLowerCase().includes(search.toLowerCase()) && !(wo.name && wo.name.toLowerCase().includes(search.toLowerCase()))) {
      return false;
    }
    if (priorityFilter && wo.priority !== priorityFilter) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Work Orders</h1>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-4">
           <input 
             type="text"
             placeholder="Search work orders..."
             value={search}
             onChange={e => setSearch(e.target.value)}
             className="border-slate-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border text-sm w-64"
           />
           <select 
             value={priorityFilter}
             onChange={e => setPriorityFilter(e.target.value)}
             className="border-slate-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border text-sm"
           >
             <option value="">All Priorities</option>
             <option value="URGENT">Urgent</option>
             <option value="HIGH">High</option>
             <option value="MEDIUM">Medium</option>
             <option value="LOW">Low</option>
           </select>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-3 font-medium">WO ID</th>
                <th className="px-6 py-3 font-medium">Name</th>
                <th className="px-6 py-3 font-medium">Priority</th>
                <th className="px-6 py-3 font-medium">Operation</th>
                <th className="px-6 py-3 font-medium">Delivery Date</th>
                <th className="px-6 py-3 font-medium">Time (S+P)</th>
                <th className="px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map(wo => {
                const status = simState?.order_states?.[wo.id] || 'WAITING';
                return (
                  <tr key={wo.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-bold text-slate-700">{wo.id}</td>
                    <td className="px-6 py-4 text-slate-600">{wo.name || '--'}</td>
                    <td className="px-6 py-4"><StatusBadge status={wo.priority} /></td>
                    <td className="px-6 py-4 text-slate-600 uppercase text-xs font-semibold">{wo.required_capability}</td>
                    <td className="px-6 py-4 font-mono text-slate-600">{format(new Date(wo.delivery_date), 'dd MMM yyyy')}</td>
                    <td className="px-6 py-4 text-slate-600 font-medium">{wo.setup_time_minutes}m + {wo.processing_time_minutes}m</td>
                    <td className="px-6 py-4"><StatusBadge status={status} /></td>
                  </tr>
                )
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">No work orders found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
