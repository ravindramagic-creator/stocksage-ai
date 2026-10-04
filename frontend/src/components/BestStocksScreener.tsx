import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getScreenerResults, type ScreenerResponse, type ScreenerResult } from "../api/screener";

function fmt(value: number | null, digits = 1): string {
  return value === null ? "—" : value.toFixed(digits);
}

function scoreClass(score: number): string {
  if (score >= 85) return "text-emerald-300";
  if (score >= 75) return "text-emerald-400";
  if (score >= 65) return "text-yellow-300";
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
      <td colSpan={9} className="px-4 pb-5 pt-2">
        <div className="grid grid-cols-2 gap-4 rounded-lg border border-slate-800 bg-slate-950 p-4 md:grid-cols-6">
          <Metric label="Fundamental" value={fmt(stock.fundamental_score, 0)} />
          <Metric label="Valuation" value={fmt(stock.valuation_score, 0)} />
          <Metric label="Technical" value={fmt(stock.technical_score, 0)} />
          <Metric label="Analyst" value={fmt(stock.analyst_score, 0)} />
          <Metric label="ROE" value={`${fmt(stock.roe)}%`} />
          <Metric label="ROCE" value={`${fmt(stock.roce)}%`} />
          <Metric label="Debt/Equity" value={fmt(stock.debt_to_equity, 2)} />
          <Metric label="PEG" value={fmt(stock.peg, 2)} />
          <Metric label="P/B" value={fmt(stock.pb, 2)} />
          <Metric label="50 DMA" value={fmt(stock.sma50, 0)} />
          <Metric label="200 DMA" value={fmt(stock.sma200, 0)} />
          <Metric label="RSI-14" value={fmt(stock.rsi14, 1)} />
          <Metric label="6M Momentum" value={`${fmt(stock.momentum_6m)}%`} />
          <Metric label="Analyst Beat" value={`${fmt(stock.analyst_beat_rate, 0)}%`} />
          <Metric label="Target Upside" value={`${fmt(stock.target_upside)}%`} />
          <Metric label="Data Coverage" value={`${fmt(stock.data_completeness, 0)}%`} />
        </div>
      </td>
    </tr>
  );
}

export function BestStocksScreener() {
  const [minScore, setMinScore] = useState(60);
  const [minRoe, setMinRoe] = useState(15);
  const [maxPe, setMaxPe] = useState(45);
  const [maxDebt, setMaxDebt] = useState(1.5);
  const [minRevenueGrowth, setMinRevenueGrowth] = useState(10);
  const [minProfitGrowth, setMinProfitGrowth] = useState(10);
  const [data, setData] = useState<ScreenerResponse | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runScreen() {
    setLoading(true);
    setError(null);
    try {
      setData(await getScreenerResults({
        minScore,
        minRoe,
        maxPe,
        maxDebtToEquity: maxDebt,
        minRevenueGrowth,
        minProfitGrowth,
        minMarketCap: 5000,
        limit: 10,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run screener");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void runScreen();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">AI Best Stocks</h2>
          <p className="mt-1 text-sm text-slate-500">
            Full NSE universe · Fundamental 50% · Valuation 20% · Technical 20% · Analyst 10%
          </p>
        </div>
        <div className="rounded-full bg-slate-950 px-3 py-1 text-xs text-slate-400">
          NSE · Top 10 candidates
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-6">
        <label className="text-xs text-slate-500">Min score<input className="mt-1 w-full rounded bg-slate-950 px-2 py-2 text-white" type="number" value={minScore} onChange={e => setMinScore(Number(e.target.value))} /></label>
        <label className="text-xs text-slate-500">Min ROE %<input className="mt-1 w-full rounded bg-slate-950 px-2 py-2 text-white" type="number" value={minRoe} onChange={e => setMinRoe(Number(e.target.value))} /></label>
        <label className="text-xs text-slate-500">Max PE<input className="mt-1 w-full rounded bg-slate-950 px-2 py-2 text-white" type="number" value={maxPe} onChange={e => setMaxPe(Number(e.target.value))} /></label>
        <label className="text-xs text-slate-500">Max D/E<input className="mt-1 w-full rounded bg-slate-950 px-2 py-2 text-white" type="number" step="0.1" value={maxDebt} onChange={e => setMaxDebt(Number(e.target.value))} /></label>
        <label className="text-xs text-slate-500">Min revenue %<input className="mt-1 w-full rounded bg-slate-950 px-2 py-2 text-white" type="number" value={minRevenueGrowth} onChange={e => setMinRevenueGrowth(Number(e.target.value))} /></label>
        <label className="text-xs text-slate-500">Min PAT %<input className="mt-1 w-full rounded bg-slate-950 px-2 py-2 text-white" type="number" value={minProfitGrowth} onChange={e => setMinProfitGrowth(Number(e.target.value))} /></label>
      </div>

      <button type="button" onClick={() => void runScreen()} disabled={loading} className="mt-4 rounded-lg bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 disabled:opacity-50">
        {loading ? "Analyzing NSE universe…" : "Find Best Stocks"}
      </button>

      {error && <div className="mt-4 rounded-lg border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">{error}</div>}

      {data && (
        <>
          <div className="mt-5 mb-3 flex flex-wrap gap-4 text-xs text-slate-500">
            <span>Universe evaluated: {data.total_universe}</span>
            <span>Top matches: {data.screened}</span>
            <span>Click a row for detailed scores</span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-800 text-[10px] uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-3">#</th><th className="px-3 py-3">Stock</th><th className="px-3 py-3">Score</th><th className="px-3 py-3">PE</th><th className="px-3 py-3">ROE</th><th className="px-3 py-3">ROCE</th><th className="px-3 py-3">RSI</th><th className="px-3 py-3">6M</th><th className="px-3 py-3">Verdict</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map(stock => (
                  <Fragment key={stock.symbol}>
                    <tr onClick={() => setExpanded(expanded === stock.symbol ? null : stock.symbol)} className="cursor-pointer border-b border-slate-800/70 hover:bg-slate-800/50">
                      <td className="px-3 py-3 text-slate-500">{stock.rank}</td>
                      <td className="px-3 py-3"><Link to={`/stock/${stock.symbol}`} onClick={e => e.stopPropagation()} className="font-semibold text-cyan-400">{stock.symbol}</Link><div className="text-[10px] text-slate-500">{stock.company_name}</div></td>
                      <td className={`px-3 py-3 font-bold ${scoreClass(stock.score)}`}>{fmt(stock.score, 0)}</td>
                      <td className="px-3 py-3">{fmt(stock.pe)}</td><td className="px-3 py-3">{fmt(stock.roe)}%</td><td className="px-3 py-3">{fmt(stock.roce)}%</td><td className="px-3 py-3">{fmt(stock.rsi14)}</td><td className="px-3 py-3">{fmt(stock.momentum_6m)}%</td>
                      <td className="px-3 py-3 text-xs font-semibold">{stock.verdict}</td>
                    </tr>
                    {expanded === stock.symbol && <DetailRow stock={stock} />}
                  </Fragment>
                ))}
              </tbody>
            </table>
            {data.results.length === 0 && <div className="p-6 text-center text-sm text-slate-500">No stocks matched the current filters.</div>}
          </div>
        </>
      )}
    </section>
  );
}
