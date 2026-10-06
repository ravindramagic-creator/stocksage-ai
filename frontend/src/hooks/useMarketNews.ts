import { useQuery } from "@tanstack/react-query";

import { getMarketNews } from "../api/marketNews";

export function useMarketNews(limit = 12) {
  return useQuery({
    queryKey: ["market-news", limit],
    queryFn: () => getMarketNews(limit),
    staleTime: 5 * 60_000,
    refetchInterval: 5 * 60_000,
    refetchOnWindowFocus: false,
  });
}
