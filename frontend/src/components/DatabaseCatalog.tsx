import React from 'react';
import { Database, X, Table, Hash, ShieldCheck } from 'lucide-react';
import { SystemOverviewResponse } from '../types/analyst';

interface DatabaseCatalogProps {
  overview: SystemOverviewResponse | null;
  isOpen: boolean;
  onClose: () => void;
}

const TABLE_SCHEMAS: Record<string, { desc: string; columns: string[] }> = {
  customers: {
    desc: 'Registered Shoply shoppers and demographic regions.',
    columns: ['customer_id', 'name', 'signup_date', 'region', 'city'],
  },
  products: {
    desc: 'Available catalog items, categories, and unit list prices.',
    columns: ['product_id', 'name', 'category', 'price', 'created_at'],
  },
  orders: {
    desc: 'Order header transactions with statuses, order dates, and total amounts.',
    columns: ['order_id', 'customer_id', 'order_date', 'status', 'total_amount'],
  },
  order_items: {
    desc: 'Line items within an order with quantity and captured unit price.',
    columns: ['order_item_id', 'order_id', 'product_id', 'quantity', 'unit_price'],
  },
  refunds: {
    desc: 'Customer refund and return processing ledger.',
    columns: ['refund_id', 'order_id', 'amount', 'reason', 'refund_date'],
  },
};

export const DatabaseCatalog: React.FC<DatabaseCatalogProps> = ({ overview, isOpen, onClose }) => {
  if (!isOpen) return null;

  const tableCounts = overview?.table_counts || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-3xl glass-panel rounded-2xl p-6 border border-slate-700 shadow-2xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Shoply PostgreSQL Schema Catalog</h3>
              <p className="text-xs text-slate-400">Canonical tables, live record counts, and column definitions</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto py-4 space-y-3 pr-1">
          {Object.entries(TABLE_SCHEMAS).map(([tableName, meta]) => {
            const count = tableCounts[tableName] ?? 0;
            return (
              <div
                key={tableName}
                className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Table className="w-4 h-4 text-indigo-400" />
                    <span className="font-mono text-sm font-semibold text-white">{tableName}</span>
                  </div>
                  <span className="flex items-center space-x-1 text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                    <Hash className="w-3 h-3" />
                    <span>{count.toLocaleString()} rows</span>
                  </span>
                </div>

                <p className="text-xs text-slate-400">{meta.desc}</p>

                <div className="flex flex-wrap gap-1.5 pt-1">
                  {meta.columns.map((col) => (
                    <span
                      key={col}
                      className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700/60"
                    >
                      {col}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer info */}
        <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Guarded with 5000ms timeout and read-only transaction limits</span>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
