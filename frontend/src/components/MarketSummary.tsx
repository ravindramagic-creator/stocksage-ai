import { useIndices } from "../hooks/useIndices";


export function MarketSummary() {
  const {
    data,
    isLoading,
    isError,
  } = useIndices();


  if (isLoading) {
    return (
      <div className="text-slate-400">
        Loading market...
      </div>
    );
  }


  if (isError) {
    return (
      <div className="text-red-400">
        Market data unavailable.
      </div>
    );
  }


  return (
    <div
      className="
        grid
        grid-cols-1
        gap-4
        md:grid-cols-2
      "
    >
      {data?.map((index) => {

        const positive =
          (index.change_percent ?? 0)
          >= 0;

        return (
          <div
            key={index.symbol}
            className="
              rounded-xl
              border border-slate-800
              bg-slate-900
              p-5
            "
          >
            <div className="text-sm text-slate-500">
              {index.symbol}
            </div>

            <div className="mt-2 text-2xl font-bold text-white">
              {index.price?.toLocaleString(
                "en-IN",
                {
                  maximumFractionDigits: 2,
                },
              ) ?? "—"}
            </div>

            <div
              className={
                positive
                  ? "mt-1 text-sm text-emerald-400"
                  : "mt-1 text-sm text-red-400"
              }
            >
              {positive ? "+" : ""}
              {index.change_percent?.toFixed(
                2,
              ) ?? "—"}
              %
            </div>
          </div>
        );
      })}
    </div>
  );
}
