import { useQuery } from "@tanstack/react-query";

import {
  getStocks,
  searchStocks,
} from "../api/stocks";

export function useStocks() {
  return useQuery({
    queryKey: ["stocks"],
    queryFn: getStocks,
  });
}

export function useStockSearch(
  query: string,
) {
  const normalizedQuery =
    query.trim().toUpperCase();

  return useQuery({
    queryKey: [
      "stock-search",
      normalizedQuery,
    ],

    queryFn: () =>
      searchStocks(normalizedQuery),

    enabled:
      normalizedQuery.length >= 2,

    staleTime: 30_000,
  });
}
