import type { Stock } from "../types/stock";
import { useAddToWatchlist } from "../hooks/useWatchlist";

interface Props {
  stocks: Stock[];
}

export function StockSearchResults({
  stocks,
}: Props) {
  const mutation = useAddToWatchlist();

  if (!stocks.length) {
    return (
      <div className="text-sm text-slate-400">
        No stocks found.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {stocks.map((stock) => (
        <div
          key={stock.id}
          className="
            flex items-center
            justify-between
            rounded-lg
            border border-slate-800
            bg-slate-900
            p-3
          "
        >
          <div>
            <div className="font-medium text-white">
              {stock.symbol}
            </div>

            <div className="text-sm text-slate-400">
              {stock.company_name}
            </div>
          </div>

          <button
            onClick={() =>
              mutation.mutate({
                symbol: stock.symbol,
              })
            }
            disabled={mutation.isPending}
            className="
              rounded-lg
              bg-emerald-600
              px-3 py-2
              text-sm
              text-white
              hover:bg-emerald-500
              disabled:opacity-50
            "
          >
            + Watch
          </button>
        </div>
      ))}
    </div>
  );
}
