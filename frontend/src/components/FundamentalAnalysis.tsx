import { useFundamentalAnalysis } from "../hooks/useFundamentalAnalysis";

interface Props {
  symbol: string;
}

function fmt(value: number | null, digits = 1): string {
  return value == null ? "—" : value.toFixed(digits);
}

function growthClass(value: number | null): string {
  if (value == null) return "text-slate-500";
  if (value > 0) return "text-emerald-400";
  if (value < 0) return "text-red-400";
  return "text-slate-400";
}

function verdictClass(verdict: string): string {
  switch (verdict) {
    case "STRONG":
      return "text-emerald-300 bg-emerald-400/10 border-emerald-500/30";
    case "GOOD":
      return "text-emerald-400 bg-emerald-400/10 border-emerald-500/20";
    case "AVERAGE":
      return "text-yellow-300 bg-yellow-400/10 border-yellow-500/20";
    case "WEAK":
      return "text-red-400 bg-red-400/10 border-red-500/20";
    default:
      return "text-slate-400 bg-slate-800 border-slate-700";
  }
}

function scoreLabel(score: number | null): string {
  if (score == null) return "Data insufficient";
  if (score >= 80) return "Strong fundamentals";
  if (score >= 65) return "Good fundamentals";
  if (score >= 50) return "Average fundamentals";
  return "Weak fundamentals";
}

function Metric({
  label,
  value,
  suffix = "",
  valueClass = "text-slate-200",
}: {
  label: string;
  value: string;
  suffix?: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-base font-semibold ${valueClass}`}>
        {value}{suffix}
      </div>
    </div>
  );
}

export function FundamentalAnalysis({ symbol }: Props) {
  const { data, isLoading, isError } = useFundamentalAnalysis(symbol);

  if (isLoading) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold text-white">Fundamental Analysis</h2>
        <div className="mt-4 text-sm text-slate-400">Loading fundamental analysis...</div>
      </section>
    );
  }

  if (isError || !data) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold text-white">Fundamental Analysis</h2>
        <div className="mt-4 text-sm text-slate-500">
          Fundamental data is not available yet. The background market snapshot worker needs to populate the stock fundamentals first.
        </div>
      </section>
    );
  }

  const score = data.overall_score == null ? null : Math.round(data.overall_score);

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-white">Fundamental Analysis</h2>
          <p className="mt-1 text-sm text-slate-400">Growth, profitability, valuation, leverage and earnings quality</p>
        </div>
        <div className={`rounded-full border px-3 py-1 text-xs font-semibold ${verdictClass(data.verdict)}`}>
          {data.verdict}
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-[1fr_auto]">
        <div>
          <div className="flex items-end justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-slate-500">Fundamental score</div>
              <div className="mt-1 text-3xl font-bold text-white">{score == null ? "—" : `${score}/100`}</div>
            </div>
            <div className="text-right text-sm text-slate-400">
              {scoreLabel(data.overall_score)}
              <div className="mt-1 text-xs">Data coverage {Math.round(data.data_completeness)}%</div>
            </div>
          </div>

          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800">
            <div className="h-full rounded-full bg-cyan-400 transition-all" style={{ width: `${Math.max(0, Math.min(100, data.overall_score ?? 0))}%` }} />
          </div>
        </div>

        <div className="min-w-[180px] rounded-xl border border-slate-800 bg-slate-950/50 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500">Latest result</div>
          <div className={`mt-2 text-lg font-semibold ${growthClass(data.latest_pat_yoy)}`}>{data.latest_result ?? "—"}</div>
          <div className="mt-1 text-xs text-slate-500">Revenue {fmt(data.latest_revenue_yoy)}% · PAT {fmt(data.latest_pat_yoy)}%</div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label="Revenue Growth" value={fmt(data.revenue_growth)} suffix="%" valueClass={growthClass(data.revenue_growth)} />
        <Metric label="Profit Growth" value={fmt(data.profit_growth)} suffix="%" valueClass={growthClass(data.profit_growth)} />
        <Metric label="EPS Growth" value={fmt(data.eps_growth)} suffix="%" valueClass={growthClass(data.eps_growth)} />
        <Metric label="ROE" value={fmt(data.roe)} suffix="%" />
        <Metric label="ROCE" value={fmt(data.roce)} suffix="%" />
        <Metric label="Debt / Equity" value={fmt(data.debt_to_equity, 2)} />
        <Metric label="P/E" value={fmt(data.pe, 1)} suffix="x" />
        <Metric label="PEG" value={fmt(data.peg, 2)} />
        <Metric label="P/B" value={fmt(data.pb, 2)} suffix="x" />
        <Metric label="Analyst Beat Rate" value={fmt(data.analyst_beat_rate, 0)} suffix="%" />
        <Metric label="Target Upside" value={fmt(data.target_upside)} suffix="%" valueClass={growthClass(data.target_upside)} />
        <Metric label="Latest EPS Growth" value={fmt(data.latest_eps_yoy)} suffix="%" valueClass={growthClass(data.latest_eps_yoy)} />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-emerald-900/40 bg-emerald-950/20 p-4">
          <div className="text-sm font-semibold text-emerald-300">Strengths</div>
          <div className="mt-3 space-y-2">
            {data.strengths.length ? data.strengths.map((strength) => <div key={strength} className="text-sm text-slate-300">✓ {strength}</div>) : <div className="text-sm text-slate-500">No strong fundamental positives were identified from the available snapshot.</div>}
          </div>
        </div>

        <div className="rounded-xl border border-red-900/40 bg-red-950/20 p-4">
          <div className="text-sm font-semibold text-red-300">Risks</div>
          <div className="mt-3 space-y-2">
            {data.risks.length ? data.risks.map((risk) => <div key={risk} className="text-sm text-slate-300">! {risk}</div>) : <div className="text-sm text-slate-500">No major fundamental risk was identified from the available snapshot.</div>}
          </div>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/50 p-3 text-sm text-slate-400">{data.summary}</div>
    </section>
  );
}