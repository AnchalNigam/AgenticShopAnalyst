export interface ExecutionStep {
  step_number: number;
  action: 'intent_analysis' | 'tool_call' | 'self_correction_attempt' | 'synthesis' | string;
  tool_name?: string | null;
  tool_input?: Record<string, any> | null;
  tool_output?: Record<string, any> | null;
  notes?: string | null;
}

export interface AnalystQueryResponse {
  question: string;
  answer: string;
  sql_query?: string | null;
  query_results: Record<string, any>[];
  execution_steps: ExecutionStep[];
  success: boolean;
  error?: string | null;
}

export interface SystemOverviewResponse {
  database_connected: boolean;
  table_counts: Record<string, number>;
  llm_provider: string;
  llm_model: string;
  sample_questions: string[];
}

export type ChartType = 'kpi' | 'bar' | 'line' | 'donut' | 'table';

export interface ChartDetectionResult {
  recommendedType: ChartType;
  labelKey: string | null;
  numericKeys: string[];
  isTimeIndexed: boolean;
}

// V2 Plan-and-Solve Types
export interface PlanTaskModel {
  id: number;
  title: string;
  objective: string;
  sql_needed: boolean;
  expected_output_key: string;
}

export interface ExecutionPlanModel {
  reasoning: string;
  tasks: PlanTaskModel[];
}

export interface TaskExecutionResultModel {
  task_id: number;
  title: string;
  objective: string;
  status: string;
  sql_query?: string | null;
  query_results: Record<string, any>[];
  summary: string;
}

export interface AnalystV2QueryResponse {
  question: string;
  plan: ExecutionPlanModel;
  task_results: TaskExecutionResultModel[];
  scratchpad: Record<string, any>;
  executive_brief: string;
  execution_steps: ExecutionStep[];
  success: boolean;
  error?: string | null;
}

