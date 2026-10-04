export type Priority = 'URGENT' | 'HIGH' | 'MEDIUM' | 'LOW';

export type MachineStatus = 'AVAILABLE' | 'UNAVAILABLE' | 'BROKEN_DOWN';

export type ScheduleStatus = 'WAITING' | 'RUNNING' | 'COMPLETED' | 'INTERRUPTED' | 'RESCHEDULED';

export interface Machine {
  id: string;
  name: string;
  capabilities: string[];
  available_from: string;
  available_to: string;
  status: MachineStatus;
  unavailable_from?: string | null;
  unavailable_until?: string | null;
}

export interface WorkOrder {
  id: string;
  quantity: number;
  setup_time_minutes: number;
  processing_time_minutes: number;
  required_capability: string;
  release_time: string;
  delivery_date: string;
  priority: Priority;
  name?: string;
}

export interface ScheduleEntry {
  work_order_id: string;
  machine_id: string;
  setup_start: string;
  production_start: string;
  production_end: string;
  setup_duration_minutes: number;
  processing_duration_minutes: number;
  priority: Priority;
  delivery_date: string;
  status: ScheduleStatus;
  lateness_minutes: number;
}

export interface ScheduleMetrics {
  scheduled_orders: number;
  unscheduled_orders: string[];
  total_completion_time_minutes: number;
  makespan_minutes: number;
  total_lateness_minutes: number;
  number_of_late_orders: number;
  weighted_lateness: number;
  machine_utilization: Record<string, number>;
  overall_machine_utilization: number;
  idle_time_per_machine: Record<string, number>;
  total_idle_minutes: number;
  objective_value: number;
}

export interface ScheduleResponse {
  schedule: ScheduleEntry[];
  metrics: ScheduleMetrics;
}

export interface SimulationStateResponse {
  current_time: string;
  order_states: Record<string, ScheduleStatus>;
  running_orders_per_machine: Record<string, string | null>;
  occupied_machines: string[];
  free_machines: string[];
  completed_orders: string[];
  waiting_orders: string[];
}

export interface Change {
  work_order_id: string;
  from_machine: string;
  to_machine: string;
  old_start: string;
  old_end: string;
  new_start: string;
  new_end: string;
  delay_delta_minutes: number;
}

export interface Reason {
  work_order_id: string;
  reason: string;
}

export interface RescheduleResponse {
  old_schedule: ScheduleEntry[];
  breakdown_event: any;
  affected_work_orders: string[];
  alternatives_evaluated: Record<string, any>;
  new_schedule: ScheduleEntry[];
  changes: Change[];
  optimization_metrics_before: ScheduleMetrics;
  optimization_metrics_after: ScheduleMetrics;
  reasons: Reason[];
}

export interface ScheduleHistoryResponse {
  schedules: any[];
  rescheduling_events: any[];
}
