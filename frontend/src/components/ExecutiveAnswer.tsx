import React from 'react';
import { Sparkles, MessageSquareQuote } from 'lucide-react';

interface ExecutiveAnswerProps {
  question: string;
  answer: string;
  timingSec?: string;
}

export const ExecutiveAnswer: React.FC<ExecutiveAnswerProps> = ({ question, answer, timingSec }) => {
  // Simple markdown renderer for bolding, code, and linebreaks
  const renderFormattedAnswer = (text: string) => {
    if (!text) return <p className="text-slate-500">No answer generated.</p>;

    // Split paragraphs
    const paragraphs = text.split(/\n\n+/);

    return (
      <div className="space-y-3">
        {paragraphs.map((p, idx) => {
          // Replace **bold** with <strong>
          const formatted = p
            .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
            .replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 bg-slate-800 text-indigo-300 rounded font-mono text-xs">$1</code>')
            .replace(/\n/g, '<br/>');

          return (
            <p
              key={idx}
              className="text-slate-200 leading-relaxed text-sm sm:text-base"
              dangerouslySetInnerHTML={{ __html: formatted }}
            />
          );
        })}
      </div>
    );
  };

  return (
    <div className="glass-panel p-6 rounded-2xl border border-indigo-500/25 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center justify-between gap-4 mb-4">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="text-xs font-semibold tracking-wider text-indigo-300 uppercase">
            Executive Summary
          </span>
        </div>
        {timingSec && (
          <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800">
            ⚡ {timingSec}s total
          </span>
        )}
      </div>

      <div className="mb-4 pl-3 border-l-2 border-indigo-500/50 flex items-start space-x-2 text-xs text-slate-400 italic">
        <MessageSquareQuote className="w-3.5 h-3.5 mt-0.5 shrink-0 text-slate-500" />
        <span>"{question}"</span>
      </div>

      <div className="pt-1">
        {renderFormattedAnswer(answer)}
      </div>
    </div>
  );
};
