import { useMarketRegime } from "../hooks/useMarketRegime";

function regimeClass(regime: string): string {
  if (regime === "BULL MARKET" || regime === "BULLISH") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
  }

  if (regime === "BEAR MARKET" || regime === "BEARISH") {
    return "border-red-500/30 bg-red-500/10 text-red-300";
  }

  return "border-yellow-500/30 bg-yellow-500/10 text-yellow-300";
}

function factorClass(status: string): string {
  if (status === "BULLISH") {
    return "text-emerald-400";
  }

  if (status === "BEARISH") {
    return "text-red-400";
  }

  return "text-slate-400";
}

function format(value: number | null, digits = 1): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }

  return value.toFixed(digits);
}

export function MarketRegime() {
  const { data, isLoading, isError } = useMarketRegime();

  if (isLoading) {
    return (
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <div className="text-sm text-slate-400">
          Calculating market regime...
        </div>
      </section>
    );
  }

  if (isError || !data) {
    return (
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <div className="text-sm text-slate-500">
          Market regime is temporarily unavailable.
        </div>
      </section>
    );
  }

  const bullishSignals = data.bullish_signals;
  const bearishSignals = data.bearish_signals;
  const neutralSignals = data.neutral_signals;

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-white">
            Market Regime
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Trend, momentum, volatility and market breadth
          </p>
        </div>

        <div className={`rounded-full border px-3 py-1 text-xs font-bold ${regimeClass(data.regime)}`}>
          {data.regime}
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-[1.2fr_1fr]">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="flex items-end justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Market score
              </div>
              <div className="mt-1 text-3xl font-bold text-white">
                {data.score}/100
              </div>
            </div>

            <div className="text-right text-xs text-slate-500">
              <div className="text-emerald-400">
                Bullish {bullishSignals}
              </div>
              <div className="text-red-400">
                Bearish {bearishSignals}
              </div>
              <div className="text-slate-400">
                Neutral {neutralSignals}
              </div>
            </div>
          </div>

          <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-cyan-400"
              style={{ width: `${Math.max(0, Math.min(100, data.score))}%` }}
            />
          </div>

          <p className="mt-4 text-sm leading-6 text-slate-400">
            {data.note}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Metric label="Nifty" value={data.nifty == null ? "—" : data.nifty.toLocaleString("en-IN", { maximumFractionDigits: 2 })} />
          <Metric label="Nifty RSI" value={format(data.nifty_rsi)} />
          <Metric label="6M Momentum" value={`${format(data.nifty_momentum_6m)}%`} />
          <Metric label="India VIX" value={format(data.india_vix, 2)} />
          <Metric label="50-DMA" value={data.nifty_50dma == null ? "—" : data.nifty_50dma.toLocaleString("en-IN", { maximumFractionDigits: 0 })} />
          <Metric label="200-DMA" value={data.nifty_200dma == null ? "—" : data.nifty_200dma.toLocaleString("en-IN", { maximumFractionDigits: 0 })} />
          <Metric label="Breadth > 50-DMA" value={`${format(data.breadth_above_50dma_pct, 0)}%`} />
          <Metric label="Signal Count" value={`${bullishSignals} / ${bearishSignals}`} />
        </div>
      </div>

      <div className="mt-5 grid gap-2 md:grid-cols-2">
        {data.factors.map((factor) => (
          <div
            key={factor.name}
            className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-slate-300">
                {factor.name}
              </span>
              <span className={`text-xs font-semibold ${factorClass(factor.status)}`}>
                {factor.status}
              </span>
            </div>
            <div className="mt-1 text-xs text-slate-500">
              {factor.detail}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 text-xs text-slate-600">
        Market regime is a decision-support indicator, not a standalone buy/sell signal.
      </div>
    </section>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-200">
        {value}
      </div>
    </div>
  );
}
