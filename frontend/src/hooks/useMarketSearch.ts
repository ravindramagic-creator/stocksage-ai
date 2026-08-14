import { useQuery } from "@tanstack/react-query";

import { searchMarket } from "../api/stockSearch";


export function useMarketSearch(
  query: string,
) {

  const normalized =
    query.trim();


  return useQuery({

    queryKey: [
      "market-search",
      normalized,
    ],

    queryFn: () =>
      searchMarket(normalized),

    enabled:
      normalized.length >= 2,

    staleTime: 60_000,
  });
}
