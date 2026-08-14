import { apiClient } from "./client";

export interface StockQuote {
  symbol: string;
  price: number | null;
  previous_close: number | null;
  open: number | null;
  day_high: number | null;
  day_low: number | null;
  volume: number | null;
  change: number | null;
  change_percent: number | null;
  currency: string | null;
  market_state: string | null;
  updated_at: string;
}

export interface PricePoint {
  timestamp: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface HistoricalPrices {
  symbol: string;
  interval: string;
  points: PricePoint[];
}

export async function getQuote(
  symbol: string,
): Promise<StockQuote> {
  const response =
    await apiClient.get<StockQuote>(
      `/market/quote/${symbol}`,
    );

  return response.data;
}

export async function getHistory(
  symbol: string,
  period = "1mo",
  interval = "1d",
): Promise<HistoricalPrices> {
  const response =
    await apiClient.get<HistoricalPrices>(
      `/market/history/${symbol}`,
      {
        params: {
          period,
          interval,
        },
      },
    );

  return response.data;
}
