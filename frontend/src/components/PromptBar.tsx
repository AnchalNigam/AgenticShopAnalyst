import React, { useState } from 'react';
import { ArrowRight, Loader2, Sparkles, Zap } from 'lucide-react';

interface PromptBarProps {
  onSubmit: (question: string, simulateError: boolean) => void;
  isLoading: boolean;
  sampleQuestions: string[];
}

export const PromptBar: React.FC<PromptBarProps> = ({ onSubmit, isLoading, sampleQuestions }) => {
  const [question, setQuestion] = useState('');
  const [simulateError, setSimulateError] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;
    onSubmit(question.trim(), simulateError);
  };

  const handleSelectSample = (sample: string) => {
    setQuestion(sample);
    onSubmit(sample, simulateError);
  };

  return (
    <section className="max-w-4xl mx-auto space-y-4">
      {/* Title & Tagline */}
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-indigo-300">
          Ask any question about Shoply's business
        </h2>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          The AI analyst reasons over business rules, writes safe SQL, self-heals database errors, and renders executive visualizations.
        </p>
      </div>

      {/* Main Input Bar */}
      <form onSubmit={handleSubmit} className="relative group">
        <div className="relative flex items-center">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Which category generated the most revenue last month?"
            disabled={isLoading}
            className="w-full pl-5 pr-36 py-4 bg-slate-900/90 border border-slate-700/80 rounded-2xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-base shadow-2xl transition-all disabled:opacity-60"
            required
          />
          <button
            type="submit"
            disabled={isLoading || !question.trim()}
            className="absolute right-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl text-sm flex items-center space-x-2 transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Thinking...</span>
              </>
            ) : (
              <>
                <span>Ask Analyst</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>

        {/* Self-Correction Chaos Mode Toggle */}
        <div className="flex items-center justify-between mt-3 px-2">
          <label className="flex items-center space-x-2.5 text-xs text-slate-400 hover:text-slate-200 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={simulateError}
              onChange={(e) => setSimulateError(e.target.checked)}
              className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-amber-500 focus:ring-amber-500/30 focus:ring-offset-0 cursor-pointer accent-amber-500"
            />
            <span className="flex items-center space-x-1.5">
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center space-x-1">
                <Zap className="w-3 h-3 text-amber-400" />
                <span>Test Self-Correction</span>
              </span>
              <span>Inject deliberate column error on Turn 1 to verify agent self-healing</span>
            </span>
          </label>
        </div>
      </form>

      {/* Suggested Question Chips */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-1 text-xs">
        <span className="text-slate-500 font-medium flex items-center space-x-1">
          <Sparkles className="w-3 h-3 text-indigo-400" />
          <span>Try asking:</span>
        </span>
        {sampleQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSelectSample(q)}
            disabled={isLoading}
            className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-slate-300 hover:text-white transition disabled:opacity-50 cursor-pointer text-left"
          >
            {q}
          </button>
        ))}
      </div>
    </section>
  );
};
