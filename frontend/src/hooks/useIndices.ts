import { useQuery } from "@tanstack/react-query";

import { getIndices } from "../api/indices";

export function useIndices() {
  return useQuery({
    queryKey: ["market-indices"],

    queryFn: getIndices,

    staleTime: 30_000,

    refetchInterval: 60_000,
  });
}
