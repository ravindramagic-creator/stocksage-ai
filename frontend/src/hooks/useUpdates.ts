import { useQuery } from "@tanstack/react-query";

import { getUpdates } from "../api/updates";


export function useUpdates(
  symbol?: string,
) {

  return useQuery({

    queryKey: [
      "updates",
      symbol ?? "all",
    ],

    queryFn: () =>
      getUpdates(symbol),

    refetchInterval: 60_000,

    staleTime: 30_000,
  });
}
