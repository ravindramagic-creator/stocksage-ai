import { apiClient } from "./client";

export interface MarketSummary {
  as_of: string;
  headline: string;
  regime: string;
  regime_score: number;
  nifty: number | null;
  nifty_change_percent: number | null;
  bank_nifty: number | null;
  bank_nifty_change_percent: number | null;
  midcap: number | null;
  midcap_change_percent: number | null;
  smallcap: number | null;
  smallcap_change_percent: number | null;
  india_vix: number | null;
  india_vix_change_percent: number | null;
  brent: number | null;
  brent_change_percent: number | null;
  usd_inr: number | null;
  usd_inr_change_percent: number | null;
  breadth_above_50dma_pct: number | null;
  positive_indices: string[];
  negative_indices: string[];
  key_points: string[];
  investor_takeaway: string;
}

export async function getMarketSummary(): Promise<MarketSummary> {
  const response = await apiClient.get<MarketSummary>(
    "/market-summary",
  );

  return response.data;
}
