import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { PromptBar } from './components/PromptBar';
import { ExecutiveAnswer } from './components/ExecutiveAnswer';
import { ChartVisualizer } from './components/ChartVisualizer';
import { SQLViewer } from './components/SQLViewer';
import { DataTable } from './components/DataTable';
import { ExecutionTimeline } from './components/ExecutionTimeline';
import { DatabaseCatalog } from './components/DatabaseCatalog';
import { fetchSystemOverview, submitAnalystQuery } from './services/api';
import { AnalystQueryResponse, SystemOverviewResponse } from './types/analyst';
import { BarChart3, Code2, Table, GitCommit, Loader2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [overview, setOverview] = useState<SystemOverviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStepText, setLoadingStepText] = useState('Reasoning over schema and business metrics...');
  const [result, setResult] = useState<AnalystQueryResponse | null>(null);
  const [queryDuration, setQueryDuration] = useState<string>('0.00');
  const [activeTab, setActiveTab] = useState<'insights' | 'sql' | 'table' | 'trace'>('insights');
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

  const handleRunQuery = async (question: string, simulateError: boolean) => {
    setIsLoading(true);
    setErrorMessage(null);
    setLoadingStepText('Evaluating intent against Shoply schema and rules...');
    const startTime = performance.now();

    // Cyclic loading animation messages to inform user of agent phases
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
      setResult(data);
      setQueryDuration(duration);
      setActiveTab('insights');
    } catch (err: any) {
      setErrorMessage(err.message || 'An unexpected error occurred during analysis.');
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setIsLoading(false);
    }
  };

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
                <h3 className="text-base font-semibold text-white">Agent Investigating...</h3>
                <p className="text-xs text-indigo-300 font-mono mt-0.5">{loadingStepText}</p>
              </div>
            </div>
          </section>
        )}

        {/* Analysis Results View */}
        {result && !isLoading && (
          <section className="max-w-4xl mx-auto space-y-6 animate-fade-in">
            {/* Executive Summary Card */}
            <ExecutiveAnswer
              question={result.question}
              answer={result.answer}
              timingSec={queryDuration}
            />

            {/* Navigation Tabs */}
            <div className="border-b border-slate-800">
              <nav className="flex space-x-2">
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
                  <span>Generated SQL</span>
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
                  <span>Data Table ({result.query_results?.length || 0})</span>
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
                  <span>Agent Trace ({result.execution_steps?.length || 0})</span>
                </button>
              </nav>
            </div>

            {/* Tab Contents */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 shadow-xl">
              {activeTab === 'insights' && (
                <ChartVisualizer rows={result.query_results || []} />
              )}
              {activeTab === 'sql' && (
                <SQLViewer sql={result.sql_query || null} />
              )}
              {activeTab === 'table' && (
                <DataTable rows={result.query_results || []} />
              )}
              {activeTab === 'trace' && (
                <ExecutionTimeline steps={result.execution_steps || []} />
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
        AgenticShop V1 • Autonomous Business Analyst • Powered by PostgreSQL, Groq/GPT-120B, React & Recharts
      </footer>
    </div>
  );
};
