import { apiClient } from "./client";
import type { Stock } from "../types/stock";

export async function getStocks(): Promise<Stock[]> {
  const response = await apiClient.get<Stock[]>("/stocks");

  return response.data;
}

export async function searchStocks(
  query: string,
): Promise<Stock[]> {
  const response = await apiClient.get<Stock[]>(
    "/stocks/search",
    {
      params: {
        q: query,
      },
    },
  );

  return response.data;
}

export async function getStock(
  symbol: string,
): Promise<Stock> {
  const response = await apiClient.get<Stock>(
    `/stocks/${symbol}`,
  );

  return response.data;
}
