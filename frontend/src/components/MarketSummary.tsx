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

const PULSE_ORDER = ["INDIA VIX", "USD/INR", "BRENT CRUDE"];

function MarketCard({
  symbol,
  price,
  changePercent,
}: {
  symbol: string;
  price?: number | null;
  changePercent?: number | null;
}) {
  const positive = (changePercent ?? 0) >= 0;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="text-xs font-medium text-slate-500">{symbol}</div>
      <div className="mt-2 text-xl font-bold text-white">
        {price?.toLocaleString("en-IN", { maximumFractionDigits: 2 }) ?? "—"}
      </div>
      <div
        className={
          changePercent == null
            ? "mt-1 text-sm text-slate-500"
            : positive
              ? "mt-1 text-sm text-emerald-400"
              : "mt-1 text-sm text-red-400"
        }
      >
        {changePercent == null
          ? "—"
          : `${positive ? "+" : ""}${changePercent.toFixed(2)}%`}
      </div>
    </div>
  );
}

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
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {DISPLAY_ORDER.map((symbol) => {
          const index = bySymbol.get(symbol);
          return (
            <MarketCard
              key={symbol}
              symbol={symbol}
              price={index?.price}
              changePercent={index?.change_percent}
            />
          );
        })}
      </div>

      <div>
        <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Market Pulse
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {PULSE_ORDER.map((symbol) => {
            const index = bySymbol.get(symbol);
            return (
              <MarketCard
                key={symbol}
                symbol={symbol}
                price={index?.price}
                changePercent={index?.change_percent}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
