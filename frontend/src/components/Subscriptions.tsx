import { Link } from "react-router-dom";

import {
  useSubscriptions,
  useSubscriptionQuotes,
  useUnsubscribe,
} from "../hooks/useSubscriptions";

export function Subscriptions() {
  const {
    data,
    isLoading,
    isError,
  } = useSubscriptions();

  const unsubscribeMutation = useUnsubscribe();

  const symbols = (data ?? []).map(
    (subscription) => subscription.stock.symbol,
  );

  const { data: quotes } = useSubscriptionQuotes(symbols);

  const quotesBySymbol = new Map(
    (quotes ?? []).map((quote) => [
      quote.symbol.toUpperCase(),
      quote,
    ]),
  );

  if (isLoading) {
    return <div className="text-slate-400">Loading subscriptions...</div>;
  }

  if (isError) {
    return <div className="text-red-400">Failed to load subscriptions.</div>;
  }

  if (!data?.length) {
    return (
      <div
        className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400"
      >
        You haven't subscribed to any stocks yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {data.map((subscription) => {
        const symbol = subscription.stock.symbol;
        const quote = quotesBySymbol.get(symbol.toUpperCase());
        const positive = (quote?.change_percent ?? 0) >= 0;

        return (
          <div
            key={subscription.id}
            className="flex items-center justify-between gap-4 rounded-xl border border-slate-800 bg-slate-900 p-4"
          >
            <Link
              to={`/stock/${symbol}`}
              className="min-w-0 flex-1"
            >
              <div className="font-semibold text-blue-400">{symbol}</div>
              <div className="truncate text-sm text-slate-400">
                {subscription.stock.company_name}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {subscription.stock.exchange}
              </div>
            </Link>

            <div className="text-right">
              <div className="font-semibold text-white">
                {quote?.price == null
                  ? "—"
                  : `₹${quote.price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`}
              </div>
              <div
                className={
                  quote?.change_percent == null
                    ? "text-sm text-slate-500"
                    : positive
                      ? "text-sm text-emerald-400"
                      : "text-sm text-red-400"
                }
              >
                {quote?.change_percent == null
                  ? "—"
                  : `${positive ? "+" : ""}${quote.change_percent.toFixed(2)}%`}
              </div>
            </div>

            <button
              onClick={() => unsubscribeMutation.mutate(symbol)}
              disabled={unsubscribeMutation.isPending}
              className="rounded-lg px-3 py-2 text-sm text-red-400 hover:bg-red-950 disabled:opacity-50"
            >
              Unsubscribe
            </button>
          </div>
        );
      })}
    </div>
  );
}