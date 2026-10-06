export interface FundamentalAnalysis {
  symbol: string;
  company_name: string | null;
  overall_score: number | null;
  verdict: string;
  data_completeness: number;

  revenue_growth: number | null;
  profit_growth: number | null;
  eps_growth: number | null;

  roe: number | null;
  roce: number | null;
  debt_to_equity: number | null;

  pe: number | null;
  peg: number | null;
  pb: number | null;

  analyst_beat_rate: number | null;
  target_upside: number | null;

  latest_revenue_yoy: number | null;
  latest_pat_yoy: number | null;
  latest_eps_yoy: number | null;
  latest_result: string | null;

  strengths: string[];
  risks: string[];
  summary: string;
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function normalize(
  raw: FundamentalAnalysis,
): FundamentalAnalysis {
  return {
    ...raw,
    overall_score: toNumber(raw.overall_score),
    data_completeness: toNumber(raw.data_completeness) ?? 0,
    revenue_growth: toNumber(raw.revenue_growth),
    profit_growth: toNumber(raw.profit_growth),
    eps_growth: toNumber(raw.eps_growth),
    roe: toNumber(raw.roe),
    roce: toNumber(raw.roce),
    debt_to_equity: toNumber(raw.debt_to_equity),
    pe: toNumber(raw.pe),
    peg: toNumber(raw.peg),
    pb: toNumber(raw.pb),
    analyst_beat_rate: toNumber(raw.analyst_beat_rate),
    target_upside: toNumber(raw.target_upside),
    latest_revenue_yoy: toNumber(raw.latest_revenue_yoy),
    latest_pat_yoy: toNumber(raw.latest_pat_yoy),
    latest_eps_yoy: toNumber(raw.latest_eps_yoy),
  };
}

export async function getFundamentalAnalysis(
  symbol: string,
): Promise<FundamentalAnalysis> {
  const response = await fetch(
    `${API_BASE_URL}/fundamental-analysis/${encodeURIComponent(symbol)}`,
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch fundamental analysis: ${response.status}`,
    );
  }

  return normalize(
    (await response.json()) as FundamentalAnalysis,
  );
}
