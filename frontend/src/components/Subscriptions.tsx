import { Link } from "react-router-dom";

import {
  useSubscriptions,
  useUnsubscribe,
} from "../hooks/useSubscriptions";

import { WatchlistPrice } from "./WatchlistPrice";


export function Subscriptions() {

  const {
    data,
    isLoading,
    isError,
  } = useSubscriptions();

  const unsubscribeMutation =
    useUnsubscribe();


  if (isLoading) {

    return (
      <div className="text-slate-400">
        Loading subscriptions...
      </div>
    );
  }


  if (isError) {

    return (
      <div className="text-red-400">
        Failed to load subscriptions.
      </div>
    );
  }


  if (!data?.length) {

    return (
      <div
        className="
          rounded-xl
          border border-slate-800
          bg-slate-900
          p-8
          text-center
          text-slate-400
        "
      >
        You haven't subscribed
        to any stocks yet.
      </div>
    );
  }


  return (
    <div className="space-y-3">

      {data.map(
        (subscription) => (

          <div
            key={
              subscription.id
            }
            className="
              flex
              items-center
              justify-between
              gap-4
              rounded-xl
              border
              border-slate-800
              bg-slate-900
              p-4
            "
          >

            <Link
              to={`/stock/${subscription.stock.symbol}`}
              className="
                min-w-0
                flex-1
              "
            >

              <div
                className="
                  font-semibold
                  text-blue-400
                "
              >
                {subscription.stock.symbol}
              </div>

              <div
                className="
                  truncate
                  text-sm
                  text-slate-400
                "
              >
                {
                  subscription.stock
                    .company_name
                }
              </div>

              <div
                className="
                  mt-1
                  text-xs
                  text-slate-500
                "
              >
                {
                  subscription.stock
                    .exchange
                }
              </div>

            </Link>


            <WatchlistPrice
              symbol={
                subscription
                  .stock.symbol
              }
            />


            <button
              onClick={() =>
                unsubscribeMutation.mutate(
                  subscription
                    .stock.symbol,
                )
              }
              disabled={
                unsubscribeMutation
                  .isPending
              }
              className="
                rounded-lg
                px-3
                py-2
                text-sm
                text-red-400
                hover:bg-red-950
                disabled:opacity-50
              "
            >
              Unsubscribe
            </button>

          </div>
        ),
      )}

    </div>
  );
}
