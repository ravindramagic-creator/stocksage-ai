import { apiClient } from "./client";


export interface DiscoveredStock {
  symbol: string;
  company_name: string;
  exchange: string;
  sector: string | null;
  yahoo_symbol: string | null;
}


export interface StockSearchResponse {
  query: string;
  results: DiscoveredStock[];
}


export async function searchMarket(
  query: string,
): Promise<StockSearchResponse> {

  const response =
    await apiClient.get<StockSearchResponse>(
      "/stock-search",
      {
        params: {
          q: query,
        },
      },
    );

  return response.data;
}
