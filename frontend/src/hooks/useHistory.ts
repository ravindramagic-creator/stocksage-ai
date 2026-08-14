import { useQuery } from "@tanstack/react-query";

import { getHistory } from "../api/marketData";

export function useHistory(
  symbol: string,
  period: string,
  interval: string,
) {
  return useQuery({
    queryKey: [
      "history",
      symbol,
      period,
      interval,
    ],

    queryFn: () =>
      getHistory(
        symbol,
        period,
        interval,
      ),

    enabled: Boolean(symbol),

    staleTime: 60_000,
  });
}
