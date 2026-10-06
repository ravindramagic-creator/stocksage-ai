import { useQuery } from "@tanstack/react-query";

import { getUpdateStats } from "../api/updateStats";

export function useUpdateStats() {
  return useQuery({
    queryKey: ["update-stats"],
    queryFn: getUpdateStats,
    staleTime: 60_000,
    refetchInterval: 120_000,
    refetchOnWindowFocus: false,
  });
}
