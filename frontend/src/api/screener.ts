export interface ScreenerResult {
  rank: number;
  symbol: string;
  company_name: string;
  sector: string | null;
  score: number;
  verdict: string;
  data_completeness: number;
  price: number | null;
  market_cap: number | null;
  pe: number | null;
  peg: number | null;
  pb: number | null;
  roe: number | null;
  roce: number | null;
  debt_to_equity: number | null;
  revenue_growth: number | null;
  profit_growth: number | null;
  eps_growth: number | null;
  sma50: number | null;
  sma200: number | null;
  rsi14: number | null;
  momentum_6m: number | null;
  target_upside: number | null;
  analyst_beat_rate: number | null;
  fundamental_score: number | null;
  valuation_score: number | null;
  technical_score: number | null;
  analyst_score: number | null;
}

export interface ScreenerResponse {
  total_universe: number;
  screened: number;
  results: ScreenerResult[];
  data_source: string;
  methodology: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export async function getScreenerResults(options: {
  minScore: number;
  minRoe: number;
  maxPe: number;
  maxDebtToEquity: number;
  minRevenueGrowth: number;
  minProfitGrowth: number;
  minMarketCap: number;
  limit: number;
}): Promise<ScreenerResponse> {
  const params = new URLSearchParams({
    min_score: String(options.minScore),
    min_roe: String(options.minRoe),
    max_pe: String(options.maxPe),
    max_debt_to_equity: String(options.maxDebtToEquity),
    min_revenue_growth: String(options.minRevenueGrowth),
    min_profit_growth: String(options.minProfitGrowth),
    min_market_cap: String(options.minMarketCap),
    limit: String(options.limit),
  });

  const response = await fetch(`${API_BASE_URL}/screener?${params.toString()}`);
  if (!response.ok) throw new Error(`Screener request failed: ${response.status}`);

  const raw = (await response.json()) as ScreenerResponse;
  return {
    ...raw,
    results: raw.results.map((item) => ({
      ...item,
      score: toNumber(item.score) ?? 0,
      data_completeness: toNumber(item.data_completeness) ?? 0,
      price: toNumber(item.price),
      market_cap: toNumber(item.market_cap),
      pe: toNumber(item.pe),
      peg: toNumber(item.peg),
      pb: toNumber(item.pb),
      roe: toNumber(item.roe),
      roce: toNumber(item.roce),
      debt_to_equity: toNumber(item.debt_to_equity),
      revenue_growth: toNumber(item.revenue_growth),
      profit_growth: toNumber(item.profit_growth),
      eps_growth: toNumber(item.eps_growth),
      sma50: toNumber(item.sma50),
      sma200: toNumber(item.sma200),
      rsi14: toNumber(item.rsi14),
      momentum_6m: toNumber(item.momentum_6m),
      target_upside: toNumber(item.target_upside),
      analyst_beat_rate: toNumber(item.analyst_beat_rate),
      fundamental_score: toNumber(item.fundamental_score),
      valuation_score: toNumber(item.valuation_score),
      technical_score: toNumber(item.technical_score),
      analyst_score: toNumber(item.analyst_score),
    })),
  };
}
