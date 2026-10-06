import { useQuery } from "@tanstack/react-query";

import { getUpdates } from "../api/updates";

export function useUpdates(
  symbol?: string,
  eventType?: string,
) {
  return useQuery({
    queryKey: ["updates", symbol, eventType],
    queryFn: () =>
      getUpdates({
        symbol,
        eventType,
      }),
    staleTime: 60_000,
    refetchInterval: 120_000,
    refetchOnWindowFocus: false,
  });
}
