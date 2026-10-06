import { apiClient } from "./client";

export interface MarketNewsItem {
  title: string;
  url: string;
  source: string;
  published_at: string;
  category: string;
  importance: string;
}

export async function getMarketNews(
  limit = 12,
): Promise<MarketNewsItem[]> {
  const response =
    await apiClient.get<MarketNewsItem[]>(
      "/market-news",
      {
        params: { limit },
      },
    );

  return response.data;
}
