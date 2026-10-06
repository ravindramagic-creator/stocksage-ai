import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getSubscriptions,
  subscribe,
  unsubscribe,
} from "../api/subscriptions";
import { getQuotes, type StockQuote } from "../api/marketData";

export function useSubscriptions() {
  return useQuery({
    queryKey: ["subscriptions"],
    queryFn: getSubscriptions,
    staleTime: 5 * 60_000,
    refetchOnWindowFocus: false,
  });
}

export function useSubscriptionQuotes(
  symbols: string[],
) {
  const normalized = [
    ...new Set(
      symbols
        .map((symbol) => symbol.trim().toUpperCase())
        .filter(Boolean),
    ),
  ];

  return useQuery<StockQuote[]>({
    queryKey: ["subscription-quotes", normalized],
    queryFn: () => getQuotes(normalized),
    enabled: normalized.length > 0,
    staleTime: 30_000,
    refetchInterval: 60_000,
    refetchOnWindowFocus: false,
  });
}

export function useSubscribe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: subscribe,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["subscriptions"],
      });
    },
  });
}

export function useUnsubscribe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: unsubscribe,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["subscriptions"],
      });
    },
  });
}
