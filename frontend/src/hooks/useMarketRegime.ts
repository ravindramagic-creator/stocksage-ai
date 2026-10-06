import { useQuery } from "@tanstack/react-query";

import { getMarketRegime } from "../api/marketRegime";

export function useMarketRegime() {
  return useQuery({
    queryKey: ["market-regime"],
    queryFn: getMarketRegime,
    staleTime: 60_000,
    refetchInterval: 60_000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
}
