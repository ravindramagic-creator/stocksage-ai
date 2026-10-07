import { Fragment, useState } from "react";
import { Link } from "react-router-dom";
import {
  getScreenerResults,
  type ScreenerResponse,
  type ScreenerResult,
} from "../api/screener";

type Mode = "fundamental" | "technical";

const TECHNICAL_FILTER_STORAGE_KEY = "stocksage.technicalScreenerFilters";

type TechnicalFilters = {
  dailyRsi: number;
  weeklyRsi: number;
  monthlyRsi: number;
  momentum3m: number;
  momentum6m: number;
};

const DEFAULT_TECHNICAL_FILTERS: TechnicalFilters = {
  dailyRsi: 60,
  weeklyRsi: 60,
  monthlyRsi: 60,
  momentum3m: 0,
  momentum6m: 0,
};

function loadTechnicalFilters(): TechnicalFilters {
  try {
    const stored = window.localStorage.getItem(TECHNICAL_FILTER_STORAGE_KEY);
    if (!stored) return DEFAULT_TECHNICAL_FILTERS;
    const parsed = JSON.parse(stored) as Partial<TechnicalFilters>;
    return {
      dailyRsi: typeof parsed.dailyRsi === "number" ? parsed.dailyRsi : 60,
      weeklyRsi: typeof parsed.weeklyRsi === "number" ? parsed.weeklyRsi : 60,
      monthlyRsi: typeof parsed.monthlyRsi === "number" ? parsed.monthlyRsi : 60,
      momentum3m: typeof parsed.momentum3m === "number" ? parsed.momentum3m : 0,
      momentum6m: typeof parsed.momentum6m === "number" ? parsed.momentum6m : 0,
    };
  } catch {
    return DEFAULT_TECHNICAL_FILTERS;
  }
}

function fmt(value: number | null, digits = 1): string {
  return value === null ? "—" : value.toFixed(digits);
}

function scoreClass(score: number): string {
  if (score >= 85) return "text-emerald-300";
  if (score >= 70) return "text-emerald-400";
  if (score >= 60) return "text-yellow-300";
  return "text-slate-300";
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-sm font-semibold text-slate-200">{value}</div>
    </div>
  );
}

function DetailRow({ stock }: { stock: ScreenerResult }) {
  return (
    <tr className="bg-slate-950/60">
      <td colSpan={12} className="px-4 pb-5 pt-2">
        <div className="grid grid-cols-2 gap-4 rounded-lg border border-slate-800 bg-slate-950 p-4 md:grid-cols-6">
          <Metric label="Fundamental" value={fmt(stock.fundamental_score, 0)} />
          <Metric label="Valuation" value={fmt(stock.valuation_score, 0)} />
          <Metric label="Technical" value={fmt(stock.technical_score, 0)} />
          <Metric label="Analyst" value={fmt(stock.analyst_score, 0)} />
          <Metric label="ROE" value={`${fmt(stock.roe)}%`} />
          <Metric label="ROCE" value={`${fmt(stock.roce)}%`} />
          <Metric label="Debt/Equity" value={fmt(stock.debt_to_equity, 2)} />
          <Metric label="PE" value={fmt(stock.pe, 2)} />
          <Metric label="PEG" value={fmt(stock.peg, 2)} />
          <Metric label="50 DMA" value={fmt(stock.sma50, 0)} />
          <Metric label="200 DMA" value={fmt(stock.sma200, 0)} />
          <Metric label="Daily RSI" value={fmt(stock.rsi14, 1)} />
          <Metric label="Weekly RSI" value={fmt(stock.rsi_weekly, 1)} />
          <Metric label="Monthly RSI" value={fmt(stock.rsi_monthly, 1)} />
          <Metric label="3M Momentum" value={`${fmt(stock.momentum_3m)}%`} />
          <Metric label="6M Momentum" value={`${fmt(stock.momentum_6m)}%`} />
          <Metric label="Analyst Beat" value={`${fmt(stock.analyst_beat_rate, 0)}%`} />
          <Metric label="Target Upside" value={`${fmt(stock.target_upside)}%`} />
          <Metric label="Data Coverage" value={`${fmt(stock.data_completeness, 0)}%`} />
        </div>
      </td>
    </tr>
  );
}

function ResultsTable({
  data,
  mode,
}: {
  data: ScreenerResponse | null;
  mode: Mode;
}) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (!data) return null;

  return (
    <div className="mt-5">
      <div className="mb-3 flex flex-wrap gap-4 text-xs text-slate-500">
        <span>Universe evaluated: {data.total_universe}</span>
        <span>{mode === "fundamental" ? "Fundamental matches" : "Technical matches"}: {data.screened}</span>
        <span>Click a row for detailed scores</span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-slate-800 text-[10px] uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-3 py-3">#</th>
              <th className="px-3 py-3">Stock</th>
              <th className="px-3 py-3">Score</th>
              {mode === "fundamental" ? (
                <>
                  <th className="px-3 py-3">PE</th>
                  <th className="px-3 py-3">ROE</th>
                  <th className="px-3 py-3">ROCE</th>
                  <th className="px-3 py-3">Revenue</th>
                  <th className="px-3 py-3">PAT</th>
                  <th className="px-3 py-3">D/E</th>
                </>
              ) : (
                <>
                  <th className="px-3 py-3">D RSI</th>
                  <th className="px-3 py-3">W RSI</th>
                  <th className="px-3 py-3">M RSI</th>
                  <th className="px-3 py-3">3M</th>
                  <th className="px-3 py-3">6M</th>
                  <th className="px-3 py-3">50 DMA</th>
                  <th className="px-3 py-3">200 DMA</th>
                </>
              )}
              <th className="px-3 py-3">Verdict</th>
            </tr>
          </thead>

          <tbody>
            {data.results.map((stock) => (
              <Fragment key={stock.symbol}>
                <tr
                  onClick={() => setExpanded(expanded === stock.symbol ? null : stock.symbol)}
                  className="cursor-pointer border-b border-slate-800/70 hover:bg-slate-800/50"
                >
                  <td className="px-3 py-3 text-slate-500">{stock.rank}</td>
                  <td className="px-3 py-3">
                    <Link
                      to={`/stock/${stock.symbol}`}
                      onClick={(e) => e.stopPropagation()}
                      className="font-semibold text-cyan-400"
                    >
                      {stock.symbol}
                    </Link>
                    <div className="text-[10px] text-slate-500">{stock.company_name}</div>
                  </td>
                  <td className={`px-3 py-3 font-bold ${scoreClass(stock.score)}`}>
                    {fmt(stock.score, 0)}
                  </td>

                  {mode === "fundamental" ? (
                    <>
                      <td className="px-3 py-3">{fmt(stock.pe)}</td>
                      <td className="px-3 py-3">{fmt(stock.roe)}%</td>
                      <td className="px-3 py-3">{fmt(stock.roce)}%</td>
                      <td className="px-3 py-3">{fmt(stock.revenue_growth)}%</td>
                      <td className="px-3 py-3">{fmt(stock.profit_growth)}%</td>
                      <td className="px-3 py-3">{fmt(stock.debt_to_equity, 2)}</td>
                    </>
                  ) : (
                    <>
                      <td className="px-3 py-3">{fmt(stock.rsi14)}</td>
                      <td className="px-3 py-3">{fmt(stock.rsi_weekly)}</td>
                      <td className="px-3 py-3">{fmt(stock.rsi_monthly)}</td>
                      <td className="px-3 py-3">{fmt(stock.momentum_3m)}%</td>
                      <td className="px-3 py-3">{fmt(stock.momentum_6m)}%</td>
                      <td className="px-3 py-3">{fmt(stock.sma50, 0)}</td>
                      <td className="px-3 py-3">{fmt(stock.sma200, 0)}</td>
                    </>
                  )}

                  <td className="px-3 py-3 text-xs font-semibold">{stock.verdict}</td>
                </tr>
                {expanded === stock.symbol && <DetailRow stock={stock} />}
              </Fragment>
            ))}
          </tbody>
        </table>

        {data.results.length === 0 && (
          <div className="p-6 text-center text-sm text-slate-500">
            No stocks matched the {mode} filters.
          </div>
        )}
      </div>
    </div>
  );
}

export function BestStocksScreener() {
  const [activeMode, setActiveMode] = useState<Mode>("fundamental");
  const [fundamentalScore, setFundamentalScore] = useState(60);
  const [minRoe, setMinRoe] = useState(15);
  const [maxPe, setMaxPe] = useState(45);
  const [maxDebt, setMaxDebt] = useState(1.5);
  const [minRevenueGrowth, setMinRevenueGrowth] = useState(10);
  const [minProfitGrowth, setMinProfitGrowth] = useState(10);

  const [technicalScore, setTechnicalScore] = useState(60);
  const [technicalFilters, setTechnicalFilters] = useState<TechnicalFilters>(loadTechnicalFilters);

  const [fundamentalData, setFundamentalData] = useState<ScreenerResponse | null>(null);
  const [technicalData, setTechnicalData] = useState<ScreenerResponse | null>(null);
  const [loading, setLoading] = useState<Mode | null>(null);
  const [error, setError] = useState<string | null>(null);

  function updateTechnicalFilter(key: keyof TechnicalFilters, value: number) {
    setTechnicalFilters((current) => ({
      ...current,
      [key]: Number.isFinite(value) ? value : 0,
    }));
    const next = { ...technicalFilters, [key]: Number.isFinite(value) ? value : 0 };
    window.localStorage.setItem(TECHNICAL_FILTER_STORAGE_KEY, JSON.stringify(next));
  }

  function resetTechnicalFilters() {
    setTechnicalFilters(DEFAULT_TECHNICAL_FILTERS);
    window.localStorage.setItem(
      TECHNICAL_FILTER_STORAGE_KEY,
      JSON.stringify(DEFAULT_TECHNICAL_FILTERS),
    );
  }

  async function runScreen(mode: Mode) {
    setActiveMode(mode);
    setLoading(mode);
    setError(null);

    try {
      const response = await getScreenerResults({
        minScore: mode === "fundamental" ? fundamentalScore : technicalScore,
        minRoe,
        maxPe,
        maxDebtToEquity: maxDebt,
        minRevenueGrowth,
        minProfitGrowth,
        minMarketCap: 5000,
        limit: 10,
        minDailyRsi: technicalFilters.dailyRsi,
        minWeeklyRsi: technicalFilters.weeklyRsi,
        minMonthlyRsi: technicalFilters.monthlyRsi,
        minMomentum3m: technicalFilters.momentum3m,
        minMomentum6m: technicalFilters.momentum6m,
        mode,
      });

      if (mode === "fundamental") setFundamentalData(response);
      else setTechnicalData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load screener");
    } finally {
      setLoading(null);
    }
  }

  return (
    <section className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">AI Best Stocks</h2>
          <p className="mt-1 text-sm text-slate-500">
            NSE universe · Independent fundamental and technical screening
          </p>
        </div>
        <div className="rounded-full bg-slate-950 px-3 py-1 text-xs text-slate-400">
          NSE · Top 10 candidates
        </div>
      </div>

      <div className="mb-5 grid grid-cols-2 rounded-lg border border-slate-800 bg-slate-950 p-1">
        <button
          type="button"
          onClick={() => setActiveMode("fundamental")}
          className={`rounded-md px-4 py-2 text-sm font-semibold ${activeMode === "fundamental" ? "bg-cyan-500 text-slate-950" : "text-slate-400 hover:bg-slate-800"}`}
        >
          Fundamental Stocks
        </button>
        <button
          type="button"
          onClick={() => setActiveMode("technical")}
          className={`rounded-md px-4 py-2 text-sm font-semibold ${activeMode === "technical" ? "bg-cyan-500 text-slate-950" : "text-slate-400 hover:bg-slate-800"}`}
        >
          Technical Stocks
        </button>
      </div>

      {activeMode === "fundamental" ? (
        <div className="rounded-lg border border-emerald-900/50 bg-slate-950/60 p-4">
          <h3 className="text-base font-semibold text-white">Fundamental Filter</h3>
          <p className="mt-1 text-xs text-slate-500">
            Business quality, growth, valuation and leverage only. No RSI, moving averages or momentum are used.
          </p>

          <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-6">
            {[
              ["Min score", fundamentalScore, setFundamentalScore, ""],
              ["Min ROE %", minRoe, setMinRoe, ""],
              ["Max PE", maxPe, setMaxPe, ""],
              ["Max D/E", maxDebt, setMaxDebt, "0.1"],
              ["Min revenue %", minRevenueGrowth, setMinRevenueGrowth, ""],
              ["Min PAT %", minProfitGrowth, setMinProfitGrowth, ""],
            ].map(([label, value, setter, step]) => (
              <label key={String(label)} className="text-xs text-slate-500">
                {label}
                <input
                  className="mt-1 w-full rounded bg-slate-900 px-2 py-2 text-white"
                  type="number"
                  step={String(step) || undefined}
                  value={Number(value)}
                  onChange={(e) => (setter as (v: number) => void)(Number(e.target.value))}
                />
              </label>
            ))}
          </div>

          <button
            type="button"
            onClick={() => void runScreen("fundamental")}
            disabled={loading !== null}
            className="mt-4 rounded-lg bg-emerald-500 px-5 py-2 text-sm font-semibold text-slate-950 disabled:opacity-50"
          >
            {loading === "fundamental" ? "Finding Fundamental Stocks…" : "Find Fundamental Stocks"}
          </button>

          <ResultsTable data={fundamentalData} mode="fundamental" />
        </div>
      ) : (
        <div className="rounded-lg border border-cyan-900/50 bg-slate-950/60 p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <h3 className="text-base font-semibold text-white">Technical Filter</h3>
              <p className="mt-1 text-xs text-slate-500">
                Price trend, 50/200 DMA, RSI and momentum only. Fundamental ratios are not used for technical qualification.
              </p>
            </div>
            <button
              type="button"
              onClick={resetTechnicalFilters}
              className="rounded border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800"
            >
              Reset Technical Filters
            </button>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-6">
            <label className="text-xs text-slate-500">
              Min technical score
              <input className="mt-1 w-full rounded bg-slate-900 px-2 py-2 text-white" type="number" value={technicalScore} onChange={(e) => setTechnicalScore(Number(e.target.value))} />
            </label>
            <label className="text-xs text-slate-500">
              Daily RSI &gt;
              <input className="mt-1 w-full rounded bg-slate-900 px-2 py-2 text-white" type="number" min="0" max="100" value={technicalFilters.dailyRsi} onChange={(e) => updateTechnicalFilter("dailyRsi", Number(e.target.value))} />
            </label>
            <label className="text-xs text-slate-500">
              Weekly RSI &gt;
              <input className="mt-1 w-full rounded bg-slate-900 px-2 py-2 text-white" type="number" min="0" max="100" value={technicalFilters.weeklyRsi} onChange={(e) => updateTechnicalFilter("weeklyRsi", Number(e.target.value))} />
            </label>
            <label className="text-xs text-slate-500">
              Monthly RSI &gt;
              <input className="mt-1 w-full rounded bg-slate-900 px-2 py-2 text-white" type="number" min="0" max="100" value={technicalFilters.monthlyRsi} onChange={(e) => updateTechnicalFilter("monthlyRsi", Number(e.target.value))} />
            </label>
            <label className="text-xs text-slate-500">
              3M Momentum &gt;
              <input className="mt-1 w-full rounded bg-slate-900 px-2 py-2 text-white" type="number" step="0.5" value={technicalFilters.momentum3m} onChange={(e) => updateTechnicalFilter("momentum3m", Number(e.target.value))} />
            </label>
            <label className="text-xs text-slate-500">
              6M Momentum &gt;
              <input className="mt-1 w-full rounded bg-slate-900 px-2 py-2 text-white" type="number" step="0.5" value={technicalFilters.momentum6m} onChange={(e) => updateTechnicalFilter("momentum6m", Number(e.target.value))} />
            </label>
          </div>

          <div className="mt-3 text-xs text-cyan-300">
            Technical rule: Daily RSI &gt; {technicalFilters.dailyRsi} · Weekly RSI &gt; {technicalFilters.weeklyRsi} · Monthly RSI &gt; {technicalFilters.monthlyRsi} · 3M Momentum &gt; {technicalFilters.momentum3m}% · 6M Momentum &gt; {technicalFilters.momentum6m}% · Price &gt; 50-DMA · 50-DMA &gt; 200-DMA
          </div>

          <button
            type="button"
            onClick={() => void runScreen("technical")}
            disabled={loading !== null}
            className="mt-4 rounded-lg bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 disabled:opacity-50"
          >
            {loading === "technical" ? "Finding Technical Stocks…" : "Find Technical Stocks"}
          </button>

          <ResultsTable data={technicalData} mode="technical" />
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">
          {error}
        </div>
      )}
    </section>
  );
}
