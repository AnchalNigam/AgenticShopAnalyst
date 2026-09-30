import { AnalystQueryResponse, AnalystV2QueryResponse, SystemOverviewResponse } from '../types/analyst';

export async function fetchSystemOverview(): Promise<SystemOverviewResponse> {
  const res = await fetch('/api/v1/analyst/overview');
  if (!res.ok) {
    throw new Error(`Failed to load system overview (${res.status})`);
  }
  return res.json();
}

export async function submitAnalystQuery(
  question: string,
  simulateError: boolean = false
): Promise<AnalystQueryResponse> {
  const res = await fetch('/api/v1/analyst/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      simulate_error: simulateError,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Query failed with status ${res.status}`);
  }

  return res.json();
}

export async function submitAnalystV2Query(
  question: string
): Promise<AnalystV2QueryResponse> {
  const res = await fetch('/api/v2/analyst/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `V2 Query failed with status ${res.status}`);
  }

  return res.json();
}

