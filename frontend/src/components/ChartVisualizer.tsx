import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { BarChart3, TrendingUp, PieChart as PieIcon, Table as TableIcon, DollarSign, Award } from 'lucide-react';
import { ChartType } from '../types/analyst';
import { detectChartType, formatMetricValue } from '../utils/chartDetector';
import { DataTable } from './DataTable';

interface ChartVisualizerProps {
  rows: Record<string, any>[];
}

const PALETTE = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#3b82f6'];

export const ChartVisualizer: React.FC<ChartVisualizerProps> = ({ rows }) => {
  const [activeChart, setActiveChart] = useState<ChartType>('bar');
  const detection = detectChartType(rows);

  // Sync active chart with auto-detection on rows change
  useEffect(() => {
    setActiveChart(detection.recommendedType);
  }, [rows]);

  if (!rows || rows.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 bg-slate-900/60 rounded-xl border border-slate-800">
        No query rows returned to visualize.
      </div>
    );
  }

  const { labelKey, numericKeys } = detection;
  const primaryMetric = numericKeys[0] || '';

  // Case 1: Single Scalar Metric -> Executive KPI Card
  if (detection.recommendedType === 'kpi' && activeChart === 'kpi') {
    const val = rows[0][primaryMetric];
    const formatted = formatMetricValue(val, primaryMetric);
    const metricTitle = primaryMetric.replace(/_/g, ' ').toUpperCase();

    return (
      <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-900 border border-indigo-500/30 shadow-xl flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-indigo-400 tracking-wider uppercase block mb-1">
            {metricTitle}
          </span>
          <div className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            {formatted}
          </div>
          <p className="text-xs text-slate-400 mt-2 flex items-center space-x-1">
            <Award className="w-3.5 h-3.5 text-emerald-400" />
            <span>Verified from PostgreSQL completed order records</span>
          </p>
        </div>
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
          <DollarSign className="w-7 h-7" />
        </div>
      </div>
    );
  }

  // Custom Recharts Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-panel p-3 rounded-lg border border-slate-700 shadow-xl text-xs">
          <p className="font-semibold text-slate-200 mb-1">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="font-mono">
              {entry.name}: {formatMetricValue(entry.value, entry.name)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      {/* Chart Selector Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-slate-800">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Visualization Mode
        </span>
        <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveChart('bar')}
            className={`px-2.5 py-1.5 rounded-lg flex items-center space-x-1.5 transition cursor-pointer ${
              activeChart === 'bar' ? 'bg-indigo-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Bar</span>
          </button>
          <button
            onClick={() => setActiveChart('line')}
            className={`px-2.5 py-1.5 rounded-lg flex items-center space-x-1.5 transition cursor-pointer ${
              activeChart === 'line' ? 'bg-indigo-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Trend</span>
          </button>
          <button
            onClick={() => setActiveChart('donut')}
            className={`px-2.5 py-1.5 rounded-lg flex items-center space-x-1.5 transition cursor-pointer ${
              activeChart === 'donut' ? 'bg-indigo-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <PieIcon className="w-3.5 h-3.5" />
            <span>Donut</span>
          </button>
          <button
            onClick={() => setActiveChart('table')}
            className={`px-2.5 py-1.5 rounded-lg flex items-center space-x-1.5 transition cursor-pointer ${
              activeChart === 'table' ? 'bg-indigo-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <TableIcon className="w-3.5 h-3.5" />
            <span>Table</span>
          </button>
        </div>
      </div>

      {/* Render Selected View */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 min-h-[320px] flex items-center justify-center">
        {activeChart === 'table' ? (
          <div className="w-full">
            <DataTable rows={rows} />
          </div>
        ) : activeChart === 'line' ? (
          <div className="w-full h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={rows} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                <defs>
                  <linearGradient id="colorMetric" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey={labelKey || undefined}
                  stroke="#64748b"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickLine={false}
                />
                <YAxis
                  stroke="#64748b"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickFormatter={(val) => (val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                {numericKeys.map((k, idx) => (
                  <Area
                    key={k}
                    type="monotone"
                    dataKey={k}
                    stroke={PALETTE[idx % PALETTE.length]}
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorMetric)"
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : activeChart === 'donut' ? (
          <div className="w-full h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Pie
                  data={rows}
                  dataKey={primaryMetric}
                  nameKey={labelKey || undefined}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                >
                  {rows.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        ) : (
          /* Default: Bar Chart */
          <div className="w-full h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey={labelKey || undefined}
                  stroke="#64748b"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickLine={false}
                />
                <YAxis
                  stroke="#64748b"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickFormatter={(val) => (val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                {numericKeys.map((k, idx) => (
                  <Bar
                    key={k}
                    dataKey={k}
                    fill={PALETTE[idx % PALETTE.length]}
                    radius={[6, 6, 0, 0]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};
