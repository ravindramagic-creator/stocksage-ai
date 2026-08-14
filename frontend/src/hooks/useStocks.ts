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

export function useStockSearch(query: string) {
  return useQuery({
    queryKey: ["stock-search", query],

    queryFn: () => searchStocks(query),

    enabled: query.trim().length > 0,

    staleTime: 30_000,
  });
}
