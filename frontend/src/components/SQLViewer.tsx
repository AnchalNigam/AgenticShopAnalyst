import React, { useState } from 'react';
import { Terminal, Copy, Check } from 'lucide-react';

interface SQLViewerProps {
  sql: string | null;
}

export const SQLViewer: React.FC<SQLViewerProps> = ({ sql }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!sql) return;
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!sql) {
    return (
      <div className="p-6 text-center text-slate-500 text-xs">
        No SQL query was generated for this turn.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 text-slate-400">
          <Terminal className="w-4 h-4 text-indigo-400" />
          <span className="font-semibold text-slate-300">Generated PostgreSQL Query</span>
          <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
            Read-Only Verified
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition text-xs cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy SQL</span>
            </>
          )}
        </button>
      </div>

      <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs overflow-x-auto shadow-inner text-indigo-200 leading-relaxed whitespace-pre-wrap">
        {sql}
      </div>
    </div>
  );
};
