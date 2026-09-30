import React, { useState } from 'react';
import { CheckCircle2, ChevronDown, ChevronRight, Terminal, ListChecks, Lightbulb } from 'lucide-react';
import { ExecutionPlanModel, TaskExecutionResultModel } from '../types/analyst';

interface PlanChecklistProps {
  plan: ExecutionPlanModel;
  taskResults: TaskExecutionResultModel[];
}

export const PlanChecklist: React.FC<PlanChecklistProps> = ({ plan, taskResults }) => {
  const [expandedTasks, setExpandedTasks] = useState<Record<number, boolean>>({});

  const toggleTask = (taskId: number) => {
    setExpandedTasks((prev) => ({
      ...prev,
      [taskId]: !prev[taskId],
    }));
  };

  if (!plan || !plan.tasks || plan.tasks.length === 0) return null;

  return (
    <div className="p-5 rounded-2xl glass-panel border border-indigo-500/25 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <ListChecks className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white flex items-center space-x-2">
              <span>Execution Plan Blueprint</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                {plan.tasks.length} Sub-Tasks
              </span>
            </h4>
            <p className="text-xs text-slate-400">Plan-and-Solve Task Decomposition Engine</p>
          </div>
        </div>
      </div>

      {/* Strategic Reasoning */}
      {plan.reasoning && (
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 flex items-start space-x-2.5">
          <Lightbulb className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-200 block mb-0.5">Planning Strategy:</span>
            <span>{plan.reasoning}</span>
          </div>
        </div>
      )}

      {/* Tasks Checklist */}
      <div className="space-y-2.5">
        {plan.tasks.map((task) => {
          const result = taskResults.find((r) => r.task_id === task.id);
          const isCompleted = result?.status === 'completed';
          const isExpanded = expandedTasks[task.id] || false;

          return (
            <div
              key={task.id}
              className={`p-3.5 rounded-xl border transition-all ${
                isCompleted
                  ? 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
                  : 'bg-slate-900/40 border-slate-800/60 opacity-80'
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-start space-x-3">
                  <div className="mt-0.5">
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border-2 border-slate-600 flex items-center justify-center text-[9px] font-mono text-slate-400">
                        {task.id}
                      </div>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-semibold text-slate-200">
                        Task #{task.id}: {task.title}
                      </span>
                      {task.sql_needed && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700/60">
                          SQL
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{task.objective}</p>

                    {/* Summary Result from Scratchpad */}
                    {result?.summary && (
                      <div className="mt-2 text-xs font-mono text-emerald-300/90 bg-emerald-950/20 px-2.5 py-1 rounded-md border border-emerald-500/20">
                        ✓ {result.summary}
                      </div>
                    )}
                  </div>
                </div>

                {result?.sql_query && (
                  <button
                    onClick={() => toggleTask(task.id)}
                    className="text-xs text-slate-400 hover:text-slate-200 flex items-center space-x-1 cursor-pointer shrink-0"
                  >
                    <span>{isExpanded ? 'Hide SQL' : 'View SQL'}</span>
                    {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>

              {/* Collapsible Sub-Task SQL Viewer */}
              {isExpanded && result?.sql_query && (
                <div className="mt-3 pt-3 border-t border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span className="flex items-center space-x-1">
                      <Terminal className="w-3 h-3 text-indigo-400" />
                      <span>Task #{task.id} SQL Execution</span>
                    </span>
                    <span>{result.query_results?.length || 0} rows retrieved</span>
                  </div>
                  <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-indigo-200 whitespace-pre-wrap overflow-x-auto">
                    {result.sql_query}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
