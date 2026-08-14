import { apiClient } from "./client";
import type { StockQuote } from "./marketData";

export async function getIndices(): Promise<
  StockQuote[]
> {
  const response =
    await apiClient.get<StockQuote[]>(
      "/market/indices",
    );

  return response.data;
}
