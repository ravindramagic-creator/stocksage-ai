import {
  useSubscribe,
} from "../hooks/useSubscriptions";

import type {
  DiscoveredStock,
} from "../api/stockSearch";


interface Props {
  results: DiscoveredStock[];
}


export function MarketSearchResults({
  results,
}: Props) {

  const mutation =
    useSubscribe();


  if (!results.length) {

    return (
      <div
        className="
          rounded-xl
          border border-slate-800
          bg-slate-900
          p-5
          text-sm
          text-slate-400
        "
      >
        No NSE stocks found.
      </div>
    );
  }


  return (
    <div className="space-y-2">

      {results.map((stock) => (

        <div
          key={stock.symbol}
          className="
            flex
            items-center
            justify-between
            gap-4
            rounded-xl
            border border-slate-800
            bg-slate-900
            p-4
          "
        >

          <div className="min-w-0">

            <div
              className="
                font-semibold
                text-white
              "
            >
              {stock.symbol}
            </div>

            <div
              className="
                truncate
                text-sm
                text-slate-400
              "
            >
              {stock.company_name}
            </div>

            <div
              className="
                mt-1
                text-xs
                text-slate-500
              "
            >
              {stock.exchange}

              {stock.sector
                ? ` • ${stock.sector}`
                : ""}
            </div>

          </div>


          <button
            onClick={() =>
              mutation.mutate({
                symbol:
                  stock.symbol,

                company_name:
                  stock.company_name,

                exchange:
                  stock.exchange,

                sector:
                  stock.sector,
              })
            }
            disabled={
              mutation.isPending
            }
            className="
              shrink-0
              rounded-lg
              bg-emerald-600
              px-4
              py-2
              text-sm
              font-medium
              text-white
              hover:bg-emerald-500
              disabled:opacity-50
            "
          >
            {mutation.isPending
              ? "Subscribing..."
              : "+ Subscribe"}
          </button>

        </div>

      ))}

    </div>
  );
}
