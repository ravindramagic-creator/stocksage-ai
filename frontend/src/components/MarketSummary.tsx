import { useIndices } from "../hooks/useIndices";

const DISPLAY_ORDER = [
  "NIFTY50",
  "BANK NIFTY",
  "NIFTY MIDCAP",
  "NIFTY SMALLCAP",
  "GIFT NIFTY",
  "GOLD",
  "CRUDE OIL",
  "NASDAQ",
  "DOW JONES",
];

export function MarketSummary() {
  const { data, isLoading, isError } = useIndices();

  if (isLoading) {
    return <div className="text-slate-400">Loading market...</div>;
  }

  if (isError) {
    return <div className="text-red-400">Market data unavailable.</div>;
  }

  const bySymbol = new Map((data ?? []).map((item) => [item.symbol, item]));

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {DISPLAY_ORDER.map((symbol) => {
        const index = bySymbol.get(symbol);
        const positive = (index?.change_percent ?? 0) >= 0;

        return (
          <div
            key={symbol}
            className="rounded-xl border border-slate-800 bg-slate-900 p-4"
          >
            <div className="text-xs font-medium text-slate-500">{symbol}</div>
            <div className="mt-2 text-xl font-bold text-white">
              {index?.price?.toLocaleString("en-IN", {
                maximumFractionDigits: 2,
              }) ?? "—"}
            </div>
            <div
              className={positive ? "mt-1 text-sm text-emerald-400" : "mt-1 text-sm text-red-400"}
            >
              {index?.change_percent == null
                ? "—"
                : `${positive ? "+" : ""}${index.change_percent.toFixed(2)}%`}
            </div>
          </div>
        );
      })}
    </div>
  );
}
