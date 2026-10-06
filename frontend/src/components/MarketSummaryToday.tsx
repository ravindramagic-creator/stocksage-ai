import { useMarketSummary } from "../hooks/useMarketSummary";

function format(value: number | null, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return value.toLocaleString("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  });
}

function changeClass(value: number | null): string {
  if (value == null) return "text-slate-500";
  return value >= 0 ? "text-emerald-400" : "text-red-400";
}

function regimeClass(regime: string): string {
  if (regime === "BULL MARKET" || regime === "BULLISH") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
  }

  if (regime === "BEAR MARKET" || regime === "BEARISH") {
    return "border-red-500/30 bg-red-500/10 text-red-300";
  }

  return "border-yellow-500/30 bg-yellow-500/10 text-yellow-300";
}

function IndexRow({
  label,
  value,
  change,
}: {
  label: string;
  value: number | null;
  change: number | null;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-800 py-3 last:border-b-0">
      <span className="text-sm text-slate-400">{label}</span>
      <div className="text-right">
        <div className="font-semibold text-white">{format(value)}</div>
        <div className={"text-xs " + changeClass(change)}>
          {change == null
            ? "—"
            : (change >= 0 ? "+" : "") + change.toFixed(2) + "%"}
        </div>
      </div>
    </div>
  );
}

export function MarketSummaryToday() {
  const { data, isLoading, isError } = useMarketSummary();

  if (isLoading) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <div className="text-sm text-slate-400">
          Preparing today's market summary...
        </div>
      </section>
    );
  }

  if (isError || !data) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <div className="text-sm text-red-400">
          Today's market summary is temporarily unavailable.
        </div>
      </section>
    );
  }

  const asOf = new Date(data.as_of).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
    timeZone: "Asia/Kolkata",
  });

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
            Today's Market Summary
          </div>
          <h2 className="mt-2 text-2xl font-bold text-white">
            {data.headline}
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Updated {asOf} IST
          </p>
        </div>

        <div className="text-right">
          <div
            className={
              "inline-flex rounded-full border px-3 py-1 text-xs font-bold " +
              regimeClass(data.regime)
            }
          >
            {data.regime}
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Market score {data.regime_score}/100
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-[1.15fr_1fr]">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-sm font-semibold text-white">
            Index snapshot
          </div>
          <div className="mt-2">
            <IndexRow label="NIFTY 50" value={data.nifty} change={data.nifty_change_percent} />
            <IndexRow label="BANK NIFTY" value={data.bank_nifty} change={data.bank_nifty_change_percent} />
            <IndexRow label="NIFTY MIDCAP" value={data.midcap} change={data.midcap_change_percent} />
            <IndexRow label="NIFTY SMALLCAP" value={data.smallcap} change={data.smallcap_change_percent} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <MiniMetric
            label="India VIX"
            value={format(data.india_vix)}
            change={data.india_vix_change_percent}
          />
          <MiniMetric
            label="Breadth > 50-DMA"
            value={
              data.breadth_above_50dma_pct == null
                ? "—"
                : data.breadth_above_50dma_pct.toFixed(0) + "%"
            }
          />
          <MiniMetric
            label="Brent Crude"
            value={
              data.brent == null
                ? "—"
                : "$" + format(data.brent)
            }
            change={data.brent_change_percent}
          />
          <MiniMetric
            label="USD/INR"
            value={format(data.usd_inr)}
            change={data.usd_inr_change_percent}
          />
        </div>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <div>
          <div className="text-sm font-semibold text-white">
            What happened today
          </div>
          <div className="mt-3 space-y-2">
            {data.key_points.map((point) => (
              <div
                key={point}
                className="rounded-lg border border-slate-800 bg-slate-950/40 p-3 text-sm text-slate-300"
              >
                • {point}
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
          <div className="text-sm font-semibold text-cyan-300">
            Investor takeaway
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            {data.investor_takeaway}
          </p>
        </div>
      </div>
    </section>
  );
}

function MiniMetric({
  label,
  value,
  change,
}: {
  label: string;
  value: string;
  change?: number | null;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-lg font-bold text-white">
        {value}
      </div>
      {change !== undefined && (
        <div className={"mt-1 text-xs " + changeClass(change ?? null)}>
          {change == null
            ? "—"
            : (change >= 0 ? "+" : "") + change.toFixed(2) + "%"}
        </div>
      )}
    </div>
  );
}
