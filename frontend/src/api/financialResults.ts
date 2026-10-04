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
  revenue_estimate: number | null;
  revenue_surprise_pct: number | null;
  revenue_result: string | null;

  ebitda: number | null;
  ebitda_yoy: number | null;
  ebitda_qoq: number | null;
  ebitda_estimate: number | null;
  ebitda_surprise_pct: number | null;
  ebitda_result: string | null;

  pat: number | null;
  pat_yoy: number | null;
  pat_qoq: number | null;
  pat_estimate: number | null;
  pat_surprise_pct: number | null;
  pat_result: string | null;

  eps: number | null;
  eps_yoy: number | null;
  eps_estimate: number | null;
  eps_surprise_pct: number | null;
  eps_result: string | null;

  overall_result: string | null;
  market_view: string | null;
  summary: string | null;
  source: string | null;
  source_url: string | null;
  broadcast_date: string | null;
  created_at: string;
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

/**
 * FastAPI/Pydantic can serialize Python Decimal values as JSON strings.
 * Normalize financial values at the API boundary so UI components always
 * receive JavaScript numbers and do not silently render valid values as —.
 */
function toNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }

  if (typeof value === "string") {
    const parsed = Number(value.trim());
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function normalizeFinancialResult(raw: FinancialResult): FinancialResult {
  return {
    ...raw,
    revenue: toNumber(raw.revenue),
    revenue_yoy: toNumber(raw.revenue_yoy),
    revenue_qoq: toNumber(raw.revenue_qoq),
    revenue_estimate: toNumber(raw.revenue_estimate),
    revenue_surprise_pct: toNumber(raw.revenue_surprise_pct),
    ebitda: toNumber(raw.ebitda),
    ebitda_yoy: toNumber(raw.ebitda_yoy),
    ebitda_qoq: toNumber(raw.ebitda_qoq),
    ebitda_estimate: toNumber(raw.ebitda_estimate),
    ebitda_surprise_pct: toNumber(raw.ebitda_surprise_pct),
    pat: toNumber(raw.pat),
    pat_yoy: toNumber(raw.pat_yoy),
    pat_qoq: toNumber(raw.pat_qoq),
    pat_estimate: toNumber(raw.pat_estimate),
    pat_surprise_pct: toNumber(raw.pat_surprise_pct),
    eps: toNumber(raw.eps),
    eps_yoy: toNumber(raw.eps_yoy),
    eps_estimate: toNumber(raw.eps_estimate),
    eps_surprise_pct: toNumber(raw.eps_surprise_pct),
  };
}

function normalizeFinancialResults(raw: unknown): FinancialResult[] {
  if (!Array.isArray(raw)) {
    throw new Error("Invalid financial results response");
  }

  return raw.map((item) => normalizeFinancialResult(item as FinancialResult));
}

export async function getLatestFinancialResult(
  symbol: string,
): Promise<FinancialResult> {
  const response = await fetch(
    `${API_BASE_URL}/financial-results/${encodeURIComponent(symbol)}/latest`,
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch financial result: ${response.status}`);
  }

  return normalizeFinancialResult(
    (await response.json()) as FinancialResult,
  );
}

export async function getFinancialResults(
  symbol: string,
  limit: number = 40,
): Promise<FinancialResult[]> {
  const response = await fetch(
    `${API_BASE_URL}/financial-results?symbol=${encodeURIComponent(symbol)}&limit=${limit}`,
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch financial results: ${response.status}`);
  }

  return normalizeFinancialResults(await response.json());
}
