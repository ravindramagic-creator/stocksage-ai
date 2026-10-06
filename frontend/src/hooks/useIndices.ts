import { useQuery } from "@tanstack/react-query";

import { getIndices } from "../api/indices";

export function useIndices() {
  return useQuery({
    queryKey: ["market-indices"],
    queryFn: getIndices,
    staleTime: 60_000,
    refetchInterval: 120_000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
}
