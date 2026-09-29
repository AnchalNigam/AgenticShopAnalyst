import React from 'react';
import { ShoppingBag, Database, Cpu, Layers } from 'lucide-react';
import { SystemOverviewResponse } from '../types/analyst';

interface HeaderProps {
  overview: SystemOverviewResponse | null;
  onToggleCatalog: () => void;
  isCatalogOpen: boolean;
}

export const Header: React.FC<HeaderProps> = ({ overview, onToggleCatalog, isCatalogOpen }) => {
  const isDbConnected = overview?.database_connected ?? false;
  const totalOrders = overview?.table_counts?.orders ?? 0;
  const llmProvider = overview?.llm_provider || 'Groq';
  const llmModel = overview?.llm_model || 'openai/gpt-oss-120b';

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <ShoppingBag className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-white tracking-tight">AgenticShop</h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wider bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 uppercase">
                V1 Analyst
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Business Intelligence & SQL Agent</p>
          </div>
        </div>

        {/* Live System Signals */}
        <div className="flex items-center space-x-3">
          {/* Database Health Badge */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <span className="relative flex h-2 w-2">
              {isDbConnected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  isDbConnected ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
              ></span>
            </span>
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-300 font-medium">
              {isDbConnected ? `PostgreSQL (${totalOrders.toLocaleString()} orders)` : 'Disconnected'}
            </span>
          </div>

          {/* Model Badge */}
          <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span className="font-mono text-slate-400">{llmProvider}:</span>
            <span className="font-mono text-indigo-300">{llmModel}</span>
          </div>

          {/* Table Catalog Toggle */}
          <button
            onClick={onToggleCatalog}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
              isCatalogOpen
                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30'
                : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Database Schema</span>
          </button>
        </div>
      </div>
    </header>
  );
};
