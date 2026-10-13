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

export async function getQuotes(
  symbols: string[],
): Promise<StockQuote[]> {
  const uniqueSymbols = [
    ...new Set(
      symbols
        .map((symbol) => symbol.trim().toUpperCase())
        .filter(Boolean),
    ),
  ];

  if (!uniqueSymbols.length) {
    return [];
  }

  // The backend intentionally limits each request to 50 symbols.
  // Split larger watchlists into valid batches so the entire quote request
  // does not fail with HTTP 400 when the user follows more than 50 stocks.
  const batchSize = 50;
  const batches: string[][] = [];

  for (let index = 0; index < uniqueSymbols.length; index += batchSize) {
    batches.push(uniqueSymbols.slice(index, index + batchSize));
  }

  const responses = await Promise.all(
    batches.map((batch) =>
      apiClient.get<StockQuote[]>("/market/quotes", {
        params: {
          symbols: batch.join(","),
        },
      }),
    ),
  );

  // Keep results from successful batches and preserve the requested order.
  const quotesBySymbol = new Map<string, StockQuote>();

  for (const response of responses) {
    for (const quote of response.data) {
      quotesBySymbol.set(quote.symbol.toUpperCase(), quote);
    }
  }

  return uniqueSymbols
    .map((symbol) => quotesBySymbol.get(symbol))
    .filter((quote): quote is StockQuote => quote !== undefined);
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
