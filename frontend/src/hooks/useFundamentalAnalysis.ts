import { useQuery } from "@tanstack/react-query";

import { getFundamentalAnalysis } from "../api/fundamentalAnalysis";

export function useFundamentalAnalysis(symbol: string) {
  return useQuery({
    queryKey: ["fundamental-analysis", symbol],
    queryFn: () => getFundamentalAnalysis(symbol),
    enabled: Boolean(symbol),
    staleTime: 5 * 60_000,
    refetchOnWindowFocus: false,
  });
}
