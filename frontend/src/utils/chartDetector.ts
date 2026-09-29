import { ChartDetectionResult } from '../types/analyst';

/**
 * Heuristic analyzer to inspect SQL query results and determine the most appropriate
 * visualization chart (KPI Card, Bar Chart, Line/Area Chart, Donut Chart, or Data Table).
 */
export function detectChartType(rows: Record<string, any>[]): ChartDetectionResult {
  if (!rows || rows.length === 0) {
    return {
      recommendedType: 'table',
      labelKey: null,
      numericKeys: [],
      isTimeIndexed: false,
    };
  }

  const firstRow = rows[0];
  const allKeys = Object.keys(firstRow);

  // Identify numeric columns (measures)
  const numericKeys = allKeys.filter((key) => {
    const val = firstRow[key];
    return typeof val === 'number' || (!isNaN(Number(val)) && val !== null && val !== '');
  });

  // Identify temporal columns (dates, months, timestamps)
  const dateKey = allKeys.find((key) => {
    const lower = key.toLowerCase();
    const val = String(firstRow[key] || '');
    return (
      lower.includes('date') ||
      lower.includes('month') ||
      lower.includes('year') ||
      lower.includes('day') ||
      /^\d{4}-\d{2}(-\d{2})?/.test(val)
    );
  });

  // Identify categorical columns (labels, dimensions)
  const labelKey =
    allKeys.find((key) => {
      return !numericKeys.includes(key) && key !== dateKey;
    }) ||
    dateKey ||
    allKeys[0];

  // Case 1: Single scalar metric (e.g. 1 row with 1 number) -> KPI Card
  if (rows.length === 1 && numericKeys.length === 1) {
    return {
      recommendedType: 'kpi',
      labelKey,
      numericKeys,
      isTimeIndexed: false,
    };
  }

  // Case 2: Time-series trend (e.g. date + revenue over multiple periods) -> Line / Area Chart
  if (dateKey && numericKeys.length > 0 && rows.length > 1) {
    return {
      recommendedType: 'line',
      labelKey: dateKey,
      numericKeys,
      isTimeIndexed: true,
    };
  }

  // Case 3: Categorical breakdown (e.g. category or city + revenue/count)
  if (numericKeys.length > 0 && rows.length > 1) {
    // If only 2 to 5 distinct categories, Donut is also a great candidate; default to bar
    return {
      recommendedType: 'bar',
      labelKey,
      numericKeys,
      isTimeIndexed: false,
    };
  }

  // Default: Tabular view for lists without clear metrics
  return {
    recommendedType: 'table',
    labelKey: null,
    numericKeys: [],
    isTimeIndexed: false,
  };
}

/**
 * Currency and number formatter for charts and tables (INR formatting)
 */
export function formatMetricValue(val: number | string, keyName: string = ''): string {
  const num = typeof val === 'number' ? val : parseFloat(String(val));
  if (isNaN(num)) return String(val ?? '');

  const isCurrency =
    /revenue|amount|price|spend|total|cost|sales/i.test(keyName) ||
    (!keyName.includes('count') && !keyName.includes('id') && !keyName.includes('qty'));

  if (isCurrency) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(num);
  }

  return new Intl.NumberFormat('en-IN').format(num);
}
