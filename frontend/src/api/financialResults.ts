export interface FinancialResult {
  id: number;

  symbol: string;

  company_name: string | null;

  period_ended: string | null;

  period_type: string | null;

  consolidated: boolean;

  // =========================================================
  // Revenue
  // =========================================================

  revenue: number | null;

  revenue_yoy: number | null;

  revenue_qoq: number | null;

  revenue_estimate: number | null;

  revenue_surprise_pct: number | null;

  revenue_result: string | null;

  // =========================================================
  // EBITDA
  // =========================================================

  ebitda: number | null;

  ebitda_yoy: number | null;

  ebitda_qoq: number | null;

  ebitda_estimate: number | null;

  ebitda_surprise_pct: number | null;

  ebitda_result: string | null;

  // =========================================================
  // PAT
  // =========================================================

  pat: number | null;

  pat_yoy: number | null;

  pat_qoq: number | null;

  pat_estimate: number | null;

  pat_surprise_pct: number | null;

  pat_result: string | null;

  // =========================================================
  // EPS
  // =========================================================

  eps: number | null;

  eps_yoy: number | null;

  eps_estimate: number | null;

  eps_surprise_pct: number | null;

  eps_result: string | null;

  // =========================================================
  // Overall
  // =========================================================

  overall_result: string | null;

  market_view: string | null;

  summary: string | null;

  source: string | null;

  source_url: string | null;

  broadcast_date: string | null;

  created_at: string;
}


// =========================================================
// API configuration
// =========================================================

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


// =========================================================
// Latest result
// =========================================================

export async function getLatestFinancialResult(
  symbol: string,
): Promise<FinancialResult> {

  const response = await fetch(
    `${API_BASE_URL}/financial-results/${encodeURIComponent(
      symbol,
    )}/latest`,
  );

  if (!response.ok) {

    throw new Error(
      `Failed to fetch financial result: ${response.status}`,
    );
  }

  return response.json();
}


// =========================================================
// Recent results
// =========================================================

export async function getFinancialResults(
  symbol: string,
  limit: number = 8,
): Promise<FinancialResult[]> {

  const response = await fetch(
    `${API_BASE_URL}/financial-results?symbol=${encodeURIComponent(
      symbol,
    )}&limit=${limit}`,
  );

  if (!response.ok) {

    throw new Error(
      `Failed to fetch financial results: ${response.status}`,
    );
  }

  const data = await response.json();

  if (!Array.isArray(data)) {

    throw new Error(
      "Invalid financial results response",
    );
  }

  return data;
}
