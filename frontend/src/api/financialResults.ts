export interface FinancialResult {
  id: number;

  symbol: string;

  company_name: string | null;

  period_ended: string | null;

  period_type: string | null;

  consolidated: boolean;

  revenue: number | null;
  revenue_yoy: number | null;
  revenue_qoq: number | null;

  ebitda: number | null;
  ebitda_yoy: number | null;
  ebitda_qoq: number | null;

  pat: number | null;
  pat_yoy: number | null;
  pat_qoq: number | null;

  eps: number | null;
  eps_yoy: number | null;

  market_view: string | null;

  summary: string | null;

  source: string | null;
  source_url: string | null;

  broadcast_date: string | null;

  created_at: string;
}

const API_BASE_URL =
  "http://127.0.0.1:8000";


export async function getLatestFinancialResult(
  symbol: string,
): Promise<FinancialResult> {

  const response = await fetch(
    `${API_BASE_URL}/financial-results/${encodeURIComponent(symbol)}/latest`,
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch financial result: ${response.status}`,
    );
  }

  return response.json();
}


/**
 * Fetch multiple recent financial results.
 *
 * The backend returns the most recent
 * results first.
 */
export async function getFinancialResults(
  symbol: string,
  limit: number = 8,
): Promise<FinancialResult[]> {

  const response = await fetch(
    `${API_BASE_URL}/financial-results?symbol=${encodeURIComponent(symbol)}&limit=${limit}`,
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch financial results: ${response.status}`,
    );
  }

  return response.json();
}
