import { useQuery } from "@tanstack/react-query";

import { getMarketSummary } from "../api/marketSummary";

export function useMarketSummary() {
  return useQuery({
    queryKey: ["market-summary"],
    queryFn: getMarketSummary,
    staleTime: 60_000,
    refetchInterval: 60_000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
}
