import {
  useRemoveFromWatchlist,
  useWatchlist,
} from "../hooks/useWatchlist";

export function Watchlist() {
  const {
    data: watchlist,
    isLoading,
    isError,
  } = useWatchlist();

  const removeMutation =
    useRemoveFromWatchlist();

  if (isLoading) {
    return (
      <div className="text-slate-400">
        Loading watchlist...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-red-400">
        Failed to load watchlist.
      </div>
    );
  }

  if (!watchlist?.length) {
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
        Your watchlist is empty.
        <br />
        Search for a stock above to add one.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {watchlist.map((item) => (
        <div
          key={item.id}
          className="
            flex items-center
            justify-between
            rounded-xl
            border border-slate-800
            bg-slate-900
            p-4
          "
        >
          <div>
            <div className="font-semibold text-white">
              {item.stock.symbol}
            </div>

            <div className="text-sm text-slate-400">
              {item.stock.company_name}
            </div>

            <div className="mt-1 text-xs text-slate-500">
              {item.stock.sector ?? "Unknown sector"}
            </div>
          </div>

          <button
            onClick={() =>
              removeMutation.mutate(
                item.stock.symbol,
              )
            }
            disabled={removeMutation.isPending}
            className="
              rounded-lg
              px-3 py-2
              text-sm
              text-red-400
              hover:bg-red-950
              disabled:opacity-50
            "
          >
            Remove
          </button>
        </div>
      ))}
    </div>
  );
}
