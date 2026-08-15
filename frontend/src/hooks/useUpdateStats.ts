import { useQuery } from "@tanstack/react-query";

import { getUpdateStats } from "../api/updateStats";


export function useUpdateStats() {

  return useQuery({
    queryKey: ["update-stats"],
    queryFn: getUpdateStats,
    refetchInterval: 60_000,
  });
}
