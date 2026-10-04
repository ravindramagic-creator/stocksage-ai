export interface ScreenerResult {
  rank: number;
  symbol: string;
  company_name: string;
  sector: string | null;
  score: number;
  verdict: string;
  price: number | null;
  pe: number | null;
  revenue_growth: number | null;
  profit_growth: number | null;
  eps_growth: number | null;
  quality_score: number | null;
  growth_score: number | null;
  valuation_score: number | null;
  momentum_score: number | null;
}

export interface ScreenerResponse {
  total_universe: number;
  screened: number;
  results: ScreenerResult[];
  data_source: string;
  methodology: string;
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export async function getScreenerResults(options: {
  minScore: number;
  maxPe: number;
  minRevenueGrowth: number;
  minProfitGrowth: number;
  limit: number;
}): Promise<ScreenerResponse> {
  const params = new URLSearchParams({
    min_score: String(options.minScore),
    max_pe: String(options.maxPe),
    min_revenue_growth: String(options.minRevenueGrowth),
    min_profit_growth: String(options.minProfitGrowth),
    limit: String(options.limit),
  });

  const response = await fetch(
    `${API_BASE_URL}/screener?${params.toString()}`,
  );

  if (!response.ok) {
    throw new Error(`Screener request failed: ${response.status}`);
  }

  const raw = (await response.json()) as ScreenerResponse;

  return {
    ...raw,
    results: raw.results.map((item) => ({
      ...item,
      score: toNumber(item.score) ?? 0,
      price: toNumber(item.price),
      pe: toNumber(item.pe),
      revenue_growth: toNumber(item.revenue_growth),
      profit_growth: toNumber(item.profit_growth),
      eps_growth: toNumber(item.eps_growth),
      quality_score: toNumber(item.quality_score),
      growth_score: toNumber(item.growth_score),
      valuation_score: toNumber(item.valuation_score),
      momentum_score: toNumber(item.momentum_score),
    })),
  };
}
