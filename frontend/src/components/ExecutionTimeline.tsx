import React, { useState } from 'react';
import { Compass, Terminal, AlertTriangle, Sparkles, ChevronDown, ChevronRight, CheckCircle2 } from 'lucide-react';
import { ExecutionStep } from '../types/analyst';

interface ExecutionTimelineProps {
  steps: ExecutionStep[];
}

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({ steps }) => {
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({});

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [stepNumber]: !prev[stepNumber],
    }));
  };

  if (!steps || steps.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <h4 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
          <span>Agent Execution Trace</span>
          <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            {steps.length} {steps.length === 1 ? 'step' : 'steps'}
          </span>
        </h4>
        <span className="text-xs text-slate-500">Autonomous Reasoning Loop</span>
      </div>

      <div className="space-y-2.5">
        {steps.map((step) => {
          const isError = step.action === 'self_correction_attempt';
          const isExpanded = expandedSteps[step.step_number] || false;

          let badgeStyle = 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30';
          let label = step.action;
          let Icon = Terminal;

          if (step.action === 'intent_analysis') {
            badgeStyle = 'bg-sky-500/15 text-sky-300 border-sky-500/30';
            label = 'Intent & Schema Mapping';
            Icon = Compass;
          } else if (step.action === 'tool_call') {
            badgeStyle = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
            label = 'SQL Tool Execution';
            Icon = CheckCircle2;
          } else if (isError) {
            badgeStyle = 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse';
            label = '⚠️ Self-Correction Attempt';
            Icon = AlertTriangle;
          } else if (step.action === 'synthesis') {
            badgeStyle = 'bg-violet-500/15 text-violet-300 border-violet-500/30';
            label = 'Executive Synthesis';
            Icon = Sparkles;
          }

          return (
            <div
              key={step.step_number}
              className={`p-3.5 rounded-xl bg-slate-900/90 border transition-all ${
                isError ? 'border-rose-500/50 shadow-rose-950/20 shadow-lg' : 'border-slate-800/90'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center space-x-2.5 flex-wrap">
                  <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-medium border ${badgeStyle} flex items-center space-x-1.5`}>
                    <Icon className="w-3.5 h-3.5" />
                    <span>Step {step.step_number}: {label}</span>
                  </span>
                  {step.tool_name && (
                    <span className="text-xs font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/60">
                      tool: {step.tool_name}
                    </span>
                  )}
                </div>

                <button
                  onClick={() => toggleStep(step.step_number)}
                  className="text-xs text-slate-400 hover:text-slate-200 flex items-center space-x-1 cursor-pointer"
                >
                  <span>{isExpanded ? 'Hide Payload' : 'View Payload'}</span>
                  {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                </button>
              </div>

              {/* Note / Description */}
              {step.notes && (
                <p className={`text-xs mt-2 pl-1 ${isError ? 'text-rose-300 font-medium' : 'text-slate-300'}`}>
                  {step.notes}
                </p>
              )}

              {/* Raw Payload Accordion */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
                  {step.tool_input && (
                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 overflow-x-auto">
                      <span className="text-slate-500 block mb-1 text-[11px] font-sans">Input Arguments:</span>
                      <pre className="text-indigo-300 whitespace-pre-wrap">
                        {JSON.stringify(step.tool_input, null, 2)}
                      </pre>
                    </div>
                  )}
                  {step.tool_output && (
                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 overflow-x-auto">
                      <span className="text-slate-500 block mb-1 text-[11px] font-sans">Output Results:</span>
                      <pre className={isError ? 'text-rose-400 whitespace-pre-wrap' : 'text-emerald-400 whitespace-pre-wrap'}>
                        {JSON.stringify(step.tool_output, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
