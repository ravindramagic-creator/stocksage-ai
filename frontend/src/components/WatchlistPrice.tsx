import { useQuote } from "../hooks/useQuote";

interface Props {
  symbol: string;
}

export function WatchlistPrice({
  symbol,
}: Props) {
  const {
    data,
    isLoading,
  } = useQuote(symbol);

  if (isLoading) {
    return (
      <div className="text-sm text-slate-500">
        Loading...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-sm text-red-400">
        —
      </div>
    );
  }

  const positive =
    (data.change_percent ?? 0) >= 0;

  return (
    <div className="text-right">
      <div className="font-semibold text-white">
        ₹
        {data.price?.toLocaleString(
          "en-IN",
          {
            maximumFractionDigits: 2,
          },
        ) ?? "—"}
      </div>

      <div
        className={
          positive
            ? "text-sm text-emerald-400"
            : "text-sm text-red-400"
        }
      >
        {positive ? "+" : ""}
        {data.change_percent?.toFixed(2) ?? "—"}%
      </div>
    </div>
  );
}
