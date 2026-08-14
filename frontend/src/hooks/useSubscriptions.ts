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


export function useSubscriptions() {

  return useQuery({
    queryKey: ["subscriptions"],
    queryFn: getSubscriptions,
  });
}


export function useSubscribe() {

  const queryClient =
    useQueryClient();

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

  const queryClient =
    useQueryClient();

  return useMutation({

    mutationFn: unsubscribe,

    onSuccess: () => {

      queryClient.invalidateQueries({
        queryKey: ["subscriptions"],
      });
    },
  });
}
