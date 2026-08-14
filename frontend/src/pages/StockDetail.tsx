import { useParams } from "react-router-dom";

import { useQuote } from "../hooks/useQuote";

function formatNumber(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  return value.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  });
}

function formatVolume(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  if (value >= 1_000_000) {
    return `${(
      value / 1_000_000
    ).toFixed(2)}M`;
  }

  if (value >= 1_000) {
    return `${(
      value / 1_000
    ).toFixed(2)}K`;
  }

  return value.toString();
}

export function StockDetail() {
  const { symbol = "" } = useParams();

  const {
    data: quote,
    isLoading,
    isError,
  } = useQuote(symbol);

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-950 p-8">
        <div className="text-slate-400">
          Loading {symbol}...
        </div>
      </main>
    );
  }

  if (isError || !quote) {
    return (
      <main className="min-h-screen bg-slate-950 p-8">
        <div className="text-red-400">
          Unable to load market data for {symbol}.
        </div>
      </main>
    );
  }

  const positive =
    (quote.change_percent ?? 0) >= 0;

  return (
    <main className="min-h-screen bg-slate-950">
      <div className="mx-auto max-w-6xl px-6 py-8">

        <div className="mb-8">
          <div className="text-sm text-slate-500">
            NSE
          </div>

          <h1 className="mt-1 text-3xl font-bold text-white">
            {quote.symbol}
          </h1>
        </div>

        <section
          className="
            rounded-2xl
            border border-slate-800
            bg-slate-900
            p-6
          "
        >
          <div className="flex flex-wrap items-end gap-4">

            <div>
              <div className="text-4xl font-bold text-white">
                ₹{formatNumber(quote.price)}
              </div>

              <div
                className={
                  positive
                    ? "mt-2 text-emerald-400"
                    : "mt-2 text-red-400"
                }
              >
                {positive ? "+" : ""}
                {formatNumber(
                  quote.change,
                )}{" "}
                ({positive ? "+" : ""}
                {formatNumber(
                  quote.change_percent,
                )}
                %)
              </div>
            </div>

          </div>

          <div
            className="
              mt-8 grid
              grid-cols-2
              gap-4
              md:grid-cols-5
            "
          >
            <Metric
              label="Previous Close"
              value={formatNumber(
                quote.previous_close,
              )}
            />

            <Metric
              label="Open"
              value={formatNumber(
                quote.open,
              )}
            />

            <Metric
              label="Day High"
              value={formatNumber(
                quote.day_high,
              )}
            />

            <Metric
              label="Day Low"
              value={formatNumber(
                quote.day_low,
              )}
            />

            <Metric
              label="Volume"
              value={formatVolume(
                quote.volume,
              )}
            />
          </div>
        </section>

        <section className="mt-6">
          <h2 className="mb-4 text-xl font-semibold text-white">
            Price History
          </h2>

          <div
            className="
              flex h-80
              items-center
              justify-center
              rounded-2xl
              border border-slate-800
              bg-slate-900
              text-slate-500
            "
          >
            Chart coming next.
          </div>
        </section>

      </div>
    </main>
  );
}

interface MetricProps {
  label: string;
  value: string;
}

function Metric({
  label,
  value,
}: MetricProps) {
  return (
    <div>
      <div className="text-sm text-slate-500">
        {label}
      </div>

      <div className="mt-1 font-medium text-slate-200">
        {value}
      </div>
    </div>
  );
}
