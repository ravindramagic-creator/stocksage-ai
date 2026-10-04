import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  getScreenerResults,
  type ScreenerResponse,
} from "../api/screener";


function format(value: number | null, digits = 1): string {
  return value === null ? "—" : value.toFixed(digits);
}


export function ScreenerPage() {
  const [minScore, setMinScore] = useState(60);
  const [maxPe, setMaxPe] = useState(45);
  const [minRevenueGrowth, setMinRevenueGrowth] = useState(10);
  const [minProfitGrowth, setMinProfitGrowth] = useState(10);
  const [limit, setLimit] = useState(20);
  const [data, setData] = useState<ScreenerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runScreen() {
    setLoading(true);
    setError(null);
    try {
      setData(
        await getScreenerResults({
          minScore,
          maxPe,
          minRevenueGrowth,
          minProfitGrowth,
          limit,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run screener");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void runScreen();
    // Initial load only. Filters are applied with the button.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">StockSage AI — Best Stocks</h1>
            <p className="mt-2 text-slate-400">
              Rank stocks using growth, earnings quality, valuation and momentum.
            </p>
          </div>
          <Link to="/" className="text-sm text-cyan-400 hover:text-cyan-300">
            ← Dashboard
          </Link>
        </header>

        <section className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-5">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
            <label className="text-sm text-slate-400">
              Minimum score
              <input
                type="number"
                min={0}
                max={100}
                value={minScore}
                onChange={(event) => setMinScore(Number(event.target.value))}
                className="mt-2 w-full rounded-lg bg-slate-950 px-3 py-2 text-white"
              />
            </label>
            <label className="text-sm text-slate-400">
              Maximum PE
              <input
                type="number"
                min={1}
                value={maxPe}
                onChange={(event) => setMaxPe(Number(event.target.value))}
                className="mt-2 w-full rounded-lg bg-slate-950 px-3 py-2 text-white"
              />
            </label>
            <label className="text-sm text-slate-400">
              Min revenue growth %
              <input
                type="number"
                value={minRevenueGrowth}
                onChange={(event) => setMinRevenueGrowth(Number(event.target.value))}
                className="mt-2 w-full rounded-lg bg-slate-950 px-3 py-2 text-white"
              />
            </label>
            <label className="text-sm text-slate-400">
              Min PAT growth %
              <input
                type="number"
                value={minProfitGrowth}
                onChange={(event) => setMinProfitGrowth(Number(event.target.value))}
                className="mt-2 w-full rounded-lg bg-slate-950 px-3 py-2 text-white"
              />
            </label>
            <label className="text-sm text-slate-400">
              Results
              <select
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
                className="mt-2 w-full rounded-lg bg-slate-950 px-3 py-2 text-white"
              >
                {[10, 20, 50, 100].map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </label>
          </div>

          <button
            type="button"
            onClick={() => void runScreen()}
            disabled={loading}
            className="mt-5 rounded-lg bg-cyan-500 px-5 py-2 font-semibold text-slate-950 disabled:opacity-50"
          >
            {loading ? "Screening…" : "Find Best Stocks"}
          </button>
        </section>

        {error && (
          <div className="mb-6 rounded-lg border border-red-900 bg-red-950/40 p-4 text-red-300">
            {error}
          </div>
        )}

        {data && (
          <>
            <div className="mb-4 flex flex-wrap gap-4 text-sm text-slate-400">
              <span>Universe: {data.total_universe}</span>
              <span>Matches: {data.screened}</span>
              <span>Score: 35% growth · 25% quality · 20% PE · 20% momentum</span>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-slate-800 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-4">#</th>
                    <th className="px-4 py-4">Stock</th>
                    <th className="px-4 py-4">Score</th>
                    <th className="px-4 py-4">Price</th>
                    <th className="px-4 py-4">PE</th>
                    <th className="px-4 py-4">Revenue YoY</th>
                    <th className="px-4 py-4">PAT YoY</th>
                    <th className="px-4 py-4">Quality</th>
                    <th className="px-4 py-4">Verdict</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((stock) => (
                    <tr key={stock.symbol} className="border-b border-slate-800/70 hover:bg-slate-800/50">
                      <td className="px-4 py-4 text-slate-500">{stock.rank}</td>
                      <td className="px-4 py-4">
                        <Link to={`/stock/${stock.symbol}`} className="font-semibold text-cyan-400 hover:text-cyan-300">
                          {stock.symbol}
                        </Link>
                        <div className="mt-1 max-w-xs text-xs text-slate-500">{stock.company_name}</div>
                      </td>
                      <td className="px-4 py-4 font-bold">{format(stock.score, 0)}</td>
                      <td className="px-4 py-4">{format(stock.price, 2)}</td>
                      <td className="px-4 py-4">{format(stock.pe, 1)}</td>
                      <td className="px-4 py-4">{format(stock.revenue_growth)}%</td>
                      <td className="px-4 py-4">{format(stock.profit_growth)}%</td>
                      <td className="px-4 py-4">{format(stock.quality_score, 0)}</td>
                      <td className="px-4 py-4">
                        <span className="rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold">
                          {stock.verdict}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {data.results.length === 0 && (
                <div className="p-8 text-center text-slate-500">
                  No stocks matched these filters. Try lowering the growth/score requirements.
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
