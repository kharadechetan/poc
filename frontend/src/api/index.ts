import { apiClient } from './client';
import type {
  Machine,
  WorkOrder,
  ScheduleResponse,
  ScheduleMetrics,
  SimulationStateResponse,
  RescheduleResponse,
  ScheduleHistoryResponse,
} from '../types/schemas';

// Admin
export const getHealth = () => apiClient.get<{ status: string }>('/health');
export const resetAdmin = () => apiClient.post('/admin/reset');

// Machines
export const getMachines = () => apiClient.get<Machine[]>('/machines');
export const getMachine = (id: string) => apiClient.get<Machine>(`/machines/${id}`);

// Work Orders
export const getWorkOrders = () => apiClient.get<WorkOrder[]>('/work-orders');
export const getWorkOrder = (id: string) => apiClient.get<WorkOrder>(`/work-orders/${id}`);

// Schedule
export const generateSchedule = () => apiClient.post<ScheduleResponse>('/schedule/generate');
export const getSchedule = () => apiClient.get<ScheduleResponse>('/schedule');
export const getScheduleMetrics = () => apiClient.get<ScheduleMetrics>('/schedule/metrics');
export const getScheduleHistory = () => apiClient.get<ScheduleHistoryResponse>('/schedule/history');
export const reschedule = () => apiClient.post<RescheduleResponse>('/schedule/reschedule');

// Simulation
export const startSimulation = (startTime?: string) => 
  apiClient.post('/simulation/start', startTime ? { start_time: startTime } : {});
export const advanceSimulation = (minutes: number) => 
  apiClient.post('/simulation/advance', { minutes });
export const getSimulationState = () => apiClient.get<SimulationStateResponse>('/simulation/state');
export const simulateBreakdown = (machineId: string, repairTimeMinutes: number, breakdownTime: string) => 
  apiClient.post('/simulation/breakdown', { machine_id: machineId, repair_time_minutes: repairTimeMinutes, breakdown_time: breakdownTime });
export const getAffectedOrders = () => apiClient.get<string[]>('/simulation/affected-orders');
export const getAlternatives = () => apiClient.get<any>('/simulation/alternatives');
