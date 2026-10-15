import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getSectorAnalysis,
  getSectorIndices,
  type SectorAnalysisResponse,
  type SectorConstituent,
} from "../api/sectors";

const PERIODS = [
  { value: "1d", label: "1D" },
  { value: "5d", label: "5D" },
  { value: "1mo", label: "1M" },
  { value: "3mo", label: "3M" },
  { value: "6mo", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "5y", label: "5Y" },
];

function formatPercent(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function percentClass(value: number | null | undefined): string {
  if (value == null) return "text-slate-400";
  return value > 0 ? "text-emerald-400" : value < 0 ? "text-red-400" : "text-slate-300";
}

function formatPrice(value: number | null): string {
  return value == null
    ? "—"
    : `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: number | null;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-bold ${percentClass(value)}`}>
        {formatPercent(value)}
      </div>
    </div>
  );
}

function ConstituentsTable({
  constituents,
  selectedSymbols,
  onToggleSymbol,
}: {
  constituents: SectorConstituent[];
  selectedSymbols: string[];
  onToggleSymbol: (symbol: string) => void;
}) {
  const [filter, setFilter] = useState("");
  const [sortBy, setSortBy] = useState<"change" | "symbol">("change");

  const visible = useMemo(() => {
    const query = filter.trim().toLowerCase();
    return [...constituents]
      .filter((item) =>
        !query ||
        item.symbol.toLowerCase().includes(query) ||
        item.company_name.toLowerCase().includes(query),
      )
      .sort((a, b) => {
        if (sortBy === "symbol") return a.symbol.localeCompare(b.symbol);
        return (b.change_percent ?? -Infinity) - (a.change_percent ?? -Infinity);
      });
  }, [constituents, filter, sortBy]);

  return (
    <div className="mt-5">
      <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="font-semibold text-white">Sector constituents</h3>
          <p className="text-xs text-slate-500">
            {constituents.length} constituents · Latest available NSE quote data
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="Filter stock or company"
            aria-label="Filter sector constituents"
            className="min-w-0 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
          />
          <select
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value as "change" | "symbol")}
            aria-label="Sort sector constituents"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
          >
            <option value="change">Top movers first</option>
            <option value="symbol">Symbol A–Z</option>
          </select>
        </div>
      </div>

      {constituents.length === 0 ? (
        <div className="rounded-lg border border-slate-800 bg-slate-950 p-5 text-sm text-slate-400">
          Constituents are temporarily unavailable. The sector index chart can still be used.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-950 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-3">#</th>
                <th className="px-3 py-3">Compare</th>
                <th className="px-3 py-3">Stock</th>
                <th className="px-3 py-3 text-right">Price</th>
                <th className="px-3 py-3 text-right">Day change</th>
                <th className="px-3 py-3 text-right">Volume</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((stock, index) => (
                <tr key={stock.symbol} className="border-t border-slate-800/70 hover:bg-slate-800/40">
                  <td className="px-3 py-3 text-slate-500">{index + 1}</td>
                  <td className="px-3 py-3">
                    <input
                      type="checkbox"
                      checked={selectedSymbols.includes(stock.symbol)}
                      disabled={!selectedSymbols.includes(stock.symbol) && selectedSymbols.length >= 8}
                      onChange={() => onToggleSymbol(stock.symbol)}
                      aria-label={`Compare ${stock.symbol}`}
                    />
                  </td>
                  <td className="px-3 py-3">
                    <Link to={`/stock/${stock.symbol}`} className="font-semibold text-cyan-400 hover:text-cyan-300">
                      {stock.symbol}
                    </Link>
                    <div className="max-w-sm truncate text-xs text-slate-500">{stock.company_name}</div>
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-slate-200">{formatPrice(stock.price)}</td>
                  <td className={`px-3 py-3 text-right font-semibold tabular-nums ${percentClass(stock.change_percent)}`}>
                    {formatPercent(stock.change_percent)}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-slate-400">
                    {stock.volume == null ? "—" : Number(stock.volume).toLocaleString("en-IN")}
                  </td>
                </tr>
              ))}
              {visible.length === 0 && (
                <tr><td colSpan={6} className="p-5 text-center text-slate-500">No constituents match your filter.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function SectorAnalysis() {
  const [sectorKey, setSectorKey] = useState("it");
  const [period, setPeriod] = useState("6mo");
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);

  // A selection belongs to the current sector only; clear it when switching sectors.
  useEffect(() => {
    setSelectedSymbols([]);
  }, [sectorKey]);

  const sectorsQuery = useQuery({
    queryKey: ["sector-indices"],
    queryFn: getSectorIndices,
    staleTime: 60 * 60 * 1000,
  });

  const analysisQuery = useQuery({
    queryKey: ["sector-analysis", sectorKey, period, selectedSymbols],
    queryFn: () => getSectorAnalysis(sectorKey, period, selectedSymbols),
    enabled: Boolean(sectorKey),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  const data: SectorAnalysisResponse | undefined = analysisQuery.data;

  const chartData = useMemo(() => {
    if (!data) return [];
    const histories = data.constituent_histories ?? {};
    const dates = new Set([
      ...data.sector_history.map((point) => point.date),
      ...data.nifty50_history.map((point) => point.date),
      ...Object.values(histories).flatMap((series) => series.map((point) => point.date)),
    ]);
    const sectorByDate = new Map(data.sector_history.map((point) => [point.date, point.value]));
    const niftyByDate = new Map(data.nifty50_history.map((point) => [point.date, point.value]));
    const selectedBySymbol = Object.fromEntries(
      Object.entries(histories).map(([symbol, series]) => [
        symbol,
        new Map(series.map((point) => [point.date, point.value])),
      ]),
    );
    return [...dates].sort().map((date) => ({
      date,
      sector: sectorByDate.get(date) ?? null,
      nifty50: niftyByDate.get(date) ?? null,
      ...Object.fromEntries(
        Object.entries(selectedBySymbol).map(([symbol, values]) => [symbol, values.get(date) ?? null]),
      ),
    }));
  }, [data]);

  function toggleSymbol(symbol: string) {
    setSelectedSymbols((current) =>
      current.includes(symbol)
        ? current.filter((item) => item !== symbol)
        : current.length < 8
          ? [...current, symbol]
          : current,
    );
  }

  return (
    <section className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Sector Index Analysis</h2>
          <p className="mt-1 max-w-3xl text-sm text-slate-400">
            Compare sector trends against NIFTY 50, then inspect and rank every constituent in that index.
          </p>
        </div>
        <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-400">
          Normalized to 100
        </span>
      </div>

      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <label className="flex-1 text-xs text-slate-500">
          Sector index
          <select
            value={sectorKey}
            onChange={(event) => setSectorKey(event.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-white"
          >
            {(sectorsQuery.data ?? []).map((sector) => (
              <option key={sector.key} value={sector.key}>{sector.name}</option>
            ))}
          </select>
        </label>
        <div className="text-xs text-slate-500">
          Comparison period
          <div className="mt-1 flex flex-wrap gap-1 rounded-lg border border-slate-800 bg-slate-950 p-1">
            {PERIODS.map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setPeriod(item.value)}
                className={`rounded-md px-3 py-2 text-sm font-semibold ${period === item.value ? "bg-cyan-400 text-slate-950" : "text-slate-400 hover:bg-slate-800"}`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {analysisQuery.isLoading && (
        <div className="flex h-64 items-center justify-center text-sm text-slate-400">Loading sector and NIFTY 50 history…</div>
      )}

      {analysisQuery.isError && (
        <div className="rounded-lg border border-red-900/70 bg-red-950/30 p-4 text-sm text-red-300">
          Unable to load sector analysis. Check that the backend is running and can access the market-data provider, then retry.
          <button type="button" onClick={() => void analysisQuery.refetch()} className="ml-3 underline">Retry</button>
        </div>
      )}

      {data && !analysisQuery.isLoading && (
        <>
          <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <SummaryCard label={`${data.name} return`} value={data.sector_return_percent} />
            <SummaryCard label="NIFTY 50 return" value={data.nifty50_return_percent} />
            <SummaryCard label="Outperformance vs NIFTY 50" value={data.excess_return_percent} />
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
            <div className="mb-2">
              <h3 className="font-semibold text-white">{data.name} vs NIFTY 50</h3>
              <p className="text-xs text-slate-500">
                Both lines start at 100; a higher ending value means stronger performance over the selected period.
              </p>
            </div>
            {chartData.length === 0 ? (
              <div className="flex h-64 items-center justify-center text-sm text-slate-500">No chart history returned for this period.</div>
            ) : (
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.55} />
                    <XAxis dataKey="date" minTickGap={30} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                    <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "#94a3b8" }} width={48} />
                    <Tooltip
                      contentStyle={{ background: "#020617", border: "1px solid #334155", borderRadius: 8 }}
                      labelStyle={{ color: "#cbd5e1" }}
                      formatter={(value, name) => [value == null ? "—" : Number(value).toFixed(2), name === "sector" ? data.name : "NIFTY 50"]}
                    />
                    <Legend formatter={(value) => value === "sector" ? data.name : "NIFTY 50"} />
                    <Line type="monotone" dataKey="sector" name="sector" stroke="#22c55e" strokeWidth={2} dot={false} connectNulls />
                    <Line type="monotone" dataKey="nifty50" name="nifty50" stroke="#60a5fa" strokeWidth={2} dot={false} connectNulls />
                    {selectedSymbols.map((symbol, index) => (
                      <Line
                        key={symbol}
                        type="monotone"
                        dataKey={symbol}
                        name={symbol}
                        stroke={["#f59e0b", "#f472b6", "#a78bfa", "#fb7185", "#2dd4bf", "#c084fc", "#facc15", "#94a3b8"][index]}
                        strokeWidth={1.8}
                        dot={false}
                        connectNulls
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {data.constituents_error && (
            <p className="mt-3 text-xs text-amber-300">{data.constituents_error}</p>
          )}
          <div className="mt-5 rounded-lg border border-slate-800 bg-slate-950 p-3">
            <div className="font-semibold text-white">Compare individual stocks</div>
            <p className="mt-1 text-xs text-slate-500">
              Select up to 8 constituents below. Each selected stock is normalized to 100 at the start of the chosen period and plotted with the sector index and NIFTY 50.
            </p>
            {selectedSymbols.length > 0 && analysisQuery.isFetching && (
              <p className="mt-2 text-xs text-cyan-300">Loading selected stock history for comparison…</p>
            )}
            {selectedSymbols.length > 0 && !analysisQuery.isFetching &&
              selectedSymbols.some((symbol) => !(data.constituent_histories?.[symbol]?.length)) && (
                <p className="mt-2 text-xs text-amber-300">
                  Some selected stocks have no history for this period. Try 1M or 6M if the selected 1D/5D data is unavailable.
                </p>
              )}
            <div className="mt-2 text-xs text-cyan-300">
              {selectedSymbols.length}/8 selected{selectedSymbols.length ? `: ${selectedSymbols.join(", ")}` : ""}
            </div>
          </div>
          <ConstituentsTable
            constituents={data.constituents}
            selectedSymbols={selectedSymbols}
            onToggleSymbol={toggleSymbol}
          />
          <p className="mt-3 text-xs text-slate-600">
            Market data can be delayed. Returns are calculated from available daily closing prices and exclude dividends.
          </p>
        </>
      )}
    </section>
  );
}
