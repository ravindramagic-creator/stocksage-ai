export interface MarketRegimeFactor {
  name: string;
  status: "BULLISH" | "BEARISH" | "NEUTRAL";
  detail: string;
}

export interface MarketRegime {
  regime: string;
  score: number;
  bullish_signals: number;
  bearish_signals: number;
  neutral_signals: number;
  nifty: number | null;
  nifty_50dma: number | null;
  nifty_200dma: number | null;
  nifty_rsi: number | null;
  nifty_momentum_6m: number | null;
  india_vix: number | null;
  breadth_above_50dma_pct: number | null;
  factors: MarketRegimeFactor[];
  note: string;
}

import { apiClient } from "./client";

export async function getMarketRegime(): Promise<MarketRegime> {
  const response = await apiClient.get<MarketRegime>(
    "/market-regime",
  );
  return response.data;
}
