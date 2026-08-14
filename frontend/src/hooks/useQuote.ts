import { useQuery } from "@tanstack/react-query";

import { getQuote } from "../api/marketData";

export function useQuote(symbol: string) {
  return useQuery({
    queryKey: ["quote", symbol],

    queryFn: () => getQuote(symbol),

    enabled: Boolean(symbol),

    staleTime: 30_000,

    refetchInterval: 60_000,
  });
}
