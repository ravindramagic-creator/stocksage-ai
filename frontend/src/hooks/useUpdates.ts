import { useQuery } from "@tanstack/react-query";

import { getUpdates } from "../api/updates";


export function useUpdates(
  symbol?: string,
  eventType?: string,
) {

  return useQuery({
    queryKey: [
      "updates",
      symbol,
      eventType,
    ],

    queryFn: () =>
      getUpdates({
        symbol,
        eventType,
      }),
  
     refetchInterval: 60_000,

     staleTime: 30_000,
  });
}

