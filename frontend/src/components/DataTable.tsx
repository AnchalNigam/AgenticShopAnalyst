import React from 'react';

interface DataTableProps {
  rows: Record<string, any>[];
}

export const DataTable: React.FC<DataTableProps> = ({ rows }) => {
  if (!rows || rows.length === 0) {
    return (
      <div className="p-6 text-center text-slate-500 text-xs">
        No rows returned by this query.
      </div>
    );
  }

  const columns = Object.keys(rows[0]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>PostgreSQL Query Results</span>
        <span className="font-mono bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
          {rows.length} {rows.length === 1 ? 'row' : 'rows'}
        </span>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/80">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
            <tr>
              {columns.map((col) => (
                <th key={col} className="p-3">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-[12px]">
            {rows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-slate-900/60 transition">
                {columns.map((col) => {
                  const val = row[col];
                  return (
                    <td key={col} className="p-3 text-slate-300">
                      {val === null || val === undefined ? (
                        <span className="text-slate-600">NULL</span>
                      ) : typeof val === 'object' ? (
                        JSON.stringify(val)
                      ) : (
                        String(val)
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
