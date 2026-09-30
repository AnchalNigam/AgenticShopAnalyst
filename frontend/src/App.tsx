import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { PromptBar } from './components/PromptBar';
import { ExecutiveAnswer } from './components/ExecutiveAnswer';
import { ChartVisualizer } from './components/ChartVisualizer';
import { SQLViewer } from './components/SQLViewer';
import { DataTable } from './components/DataTable';
import { ExecutionTimeline } from './components/ExecutionTimeline';
import { DatabaseCatalog } from './components/DatabaseCatalog';
import { PlanChecklist } from './components/PlanChecklist';
import { fetchSystemOverview, submitAnalystQuery, submitAnalystV2Query } from './services/api';
import { AnalystQueryResponse, AnalystV2QueryResponse, SystemOverviewResponse } from './types/analyst';
import { BarChart3, Code2, Table, GitCommit, Loader2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [overview, setOverview] = useState<SystemOverviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStepText, setLoadingStepText] = useState('Reasoning over schema and business metrics...');
  const [v1Result, setV1Result] = useState<AnalystQueryResponse | null>(null);
  const [v2Result, setV2Result] = useState<AnalystV2QueryResponse | null>(null);
  const [currentMode, setCurrentMode] = useState<'v1' | 'v2'>('v2');
  const [queryDuration, setQueryDuration] = useState<string>('0.00');
  const [activeTab, setActiveTab] = useState<'insights' | 'plan' | 'sql' | 'table' | 'trace'>('insights');
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load system overview on mount
  useEffect(() => {
    fetchSystemOverview()
      .then(setOverview)
      .catch((err) => {
        console.error('Failed to load overview:', err);
        setErrorMessage('Unable to connect to backend API or PostgreSQL database.');
      });
  }, []);

  const handleRunQuery = async (question: string, simulateError: boolean, mode: 'v1' | 'v2') => {
    setIsLoading(true);
    setErrorMessage(null);
    setCurrentMode(mode);
    setV1Result(null);
    setV2Result(null);

    const startTime = performance.now();

    if (mode === 'v2') {
      setLoadingStepText('Planner decomposing question into atomic sub-tasks...');
      const timer1 = setTimeout(() => {
        setLoadingStepText('Executing sub-task SQL queries against PostgreSQL...');
      }, 700);
      const timer2 = setTimeout(() => {
        setLoadingStepText('Reconciling scratchpad metrics and auditing data grain...');
      }, 1800);
      const timer3 = setTimeout(() => {
        setLoadingStepText('Synthesizing verified multi-dimensional executive brief...');
      }, 3000);

      try {
        const data = await submitAnalystV2Query(question);
        const duration = ((performance.now() - startTime) / 1000).toFixed(2);
        setV2Result(data);
        setQueryDuration(duration);
        setActiveTab('insights');
      } catch (err: any) {
        setErrorMessage(err.message || 'V2 analysis failed.');
      } finally {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
        setIsLoading(false);
      }
    } else {
      setLoadingStepText('Evaluating intent against Shoply schema and rules...');
      const timer1 = setTimeout(() => {
        setLoadingStepText('Generating read-only SQL query...');
      }, 400);
      const timer2 = setTimeout(() => {
        setLoadingStepText(
          simulateError
            ? 'Executing tool call (Simulating Turn-1 fault injection & self-correction)...'
            : 'Executing query against PostgreSQL connection pool...'
        );
      }, 900);
      const timer3 = setTimeout(() => {
        setLoadingStepText('Synthesizing executive business answer and formatting metrics...');
      }, 1500);

      try {
        const data = await submitAnalystQuery(question, simulateError);
        const duration = ((performance.now() - startTime) / 1000).toFixed(2);
        setV1Result(data);
        setQueryDuration(duration);
        setActiveTab('insights');
      } catch (err: any) {
        setErrorMessage(err.message || 'V1 query failed.');
      } finally {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
        setIsLoading(false);
      }
    }
  };

  // Helper to extract rows for visualizations
  const getVisualizationRows = (): Record<string, any>[] => {
    if (v2Result) {
      // Find the task result with the richest row data (or the most recent SQL task with rows)
      const tasksWithRows = v2Result.task_results.filter((t) => t.query_results && t.query_results.length > 0);
      if (tasksWithRows.length > 0) {
        return tasksWithRows[tasksWithRows.length - 1].query_results;
      }
      return [];
    }
    return v1Result?.query_results || [];
  };

  // Helper to get SQL query string
  const getSQLQuery = (): string | null => {
    if (v2Result) {
      const sqlParts = v2Result.task_results
        .filter((t) => t.sql_query)
        .map((t) => `-- Task #${t.task_id}: ${t.title}\n${t.sql_query}`);
      return sqlParts.join('\n\n') || null;
    }
    return v1Result?.sql_query || null;
  };

  const hasResult = v2Result !== null || v1Result !== null;

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Navbar */}
      <Header
        overview={overview}
        onToggleCatalog={() => setIsCatalogOpen(true)}
        isCatalogOpen={isCatalogOpen}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Search & Prompt Area */}
        <PromptBar
          onSubmit={handleRunQuery}
          isLoading={isLoading}
          sampleQuestions={
            overview?.sample_questions || [
              'What was our revenue in August?',
              'Which category generated the most revenue last month?',
              'How many orders did we receive in July?',
              'What was our average order value in August?',
            ]
          }
        />

        {/* Global Error Banner */}
        {errorMessage && (
          <div className="max-w-4xl mx-auto p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 flex items-center space-x-3 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Loading Stepper Card */}
        {isLoading && (
          <section className="max-w-4xl mx-auto glass-panel rounded-2xl p-6 border border-indigo-500/25 shadow-2xl animate-pulse">
            <div className="flex items-center space-x-4 mb-2">
              <div className="w-9 h-9 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center animate-spin">
                <Loader2 className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-semibold text-white">Agent Investigating...</h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {currentMode === 'v2' ? 'V2 Plan-and-Solve' : 'V1 Reactive'}
                  </span>
                </div>
                <p className="text-xs text-indigo-300 font-mono mt-0.5">{loadingStepText}</p>
              </div>
            </div>
          </section>
        )}

        {/* Analysis Results View */}
        {hasResult && !isLoading && (
          <section className="max-w-4xl mx-auto space-y-6 animate-fade-in">
            {/* Executive Summary Card */}
            <ExecutiveAnswer
              question={v2Result?.question || v1Result?.question || ''}
              answer={v2Result?.executive_brief || v1Result?.answer || ''}
              timingSec={queryDuration}
            />

            {/* V2 Decomposed Plan Blueprint (Featured prominently if in V2 mode) */}
            {v2Result && (
              <PlanChecklist plan={v2Result.plan} taskResults={v2Result.task_results} />
            )}

            {/* Navigation Tabs */}
            <div className="border-b border-slate-800">
              <nav className="flex space-x-2 flex-wrap">
                <button
                  onClick={() => setActiveTab('insights')}
                  className={`px-4 py-2.5 text-xs font-medium rounded-t-xl flex items-center space-x-2 border-b-2 transition cursor-pointer ${
                    activeTab === 'insights'
                      ? 'border-indigo-500 text-indigo-400 bg-slate-900/80'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  <span>Insights & Chart</span>
                </button>

                <button
                  onClick={() => setActiveTab('sql')}
                  className={`px-4 py-2.5 text-xs font-medium rounded-t-xl flex items-center space-x-2 border-b-2 transition cursor-pointer ${
                    activeTab === 'sql'
                      ? 'border-indigo-500 text-indigo-400 bg-slate-900/80'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                  }`}
                >
                  <Code2 className="w-3.5 h-3.5" />
                  <span>Generated SQL {v2Result ? `(${v2Result.task_results.filter(t => t.sql_query).length})` : ''}</span>
                </button>

                <button
                  onClick={() => setActiveTab('table')}
                  className={`px-4 py-2.5 text-xs font-medium rounded-t-xl flex items-center space-x-2 border-b-2 transition cursor-pointer ${
                    activeTab === 'table'
                      ? 'border-indigo-500 text-indigo-400 bg-slate-900/80'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                  }`}
                >
                  <Table className="w-3.5 h-3.5" />
                  <span>Data Table ({getVisualizationRows().length})</span>
                </button>

                <button
                  onClick={() => setActiveTab('trace')}
                  className={`px-4 py-2.5 text-xs font-medium rounded-t-xl flex items-center space-x-2 border-b-2 transition cursor-pointer ${
                    activeTab === 'trace'
                      ? 'border-indigo-500 text-indigo-400 bg-slate-900/80'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                  }`}
                >
                  <GitCommit className="w-3.5 h-3.5" />
                  <span>
                    Agent Trace ({(v2Result?.execution_steps || v1Result?.execution_steps || []).length})
                  </span>
                </button>
              </nav>
            </div>

            {/* Tab Contents */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 shadow-xl">
              {activeTab === 'insights' && (
                <ChartVisualizer rows={getVisualizationRows()} />
              )}
              {activeTab === 'sql' && (
                <SQLViewer sql={getSQLQuery()} />
              )}
              {activeTab === 'table' && (
                <DataTable rows={getVisualizationRows()} />
              )}
              {activeTab === 'trace' && (
                <ExecutionTimeline steps={v2Result?.execution_steps || v1Result?.execution_steps || []} />
              )}
            </div>
          </section>
        )}
      </main>

      {/* Database Schema Catalog Modal */}
      <DatabaseCatalog
        overview={overview}
        isOpen={isCatalogOpen}
        onClose={() => setIsCatalogOpen(false)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        AgenticShop V2 • Plan-and-Solve Autonomous Business Analyst • Powered by PostgreSQL, Groq/GPT-120B, React & Recharts
      </footer>
    </div>
  );
};
