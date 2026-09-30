import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { fetchAutoSales } from "../api/autoSales";
import type { AutoSales } from "../types/autoSales";

const SEGMENTS = [
  { value: "", label: "All segments" },
  { value: "PV", label: "Passenger Vehicles" },
  { value: "2W", label: "Two Wheelers" },
  { value: "3W", label: "Three Wheelers" },
  { value: "CV", label: "Commercial Vehicles" },
  { value: "TRACTOR", label: "Tractors" },
];

function formatNumber(value: number | null) {
  return value == null ? "-" : new Intl.NumberFormat("en-IN").format(value);
}

function formatMonth(value: string) {
  return new Date(value).toLocaleDateString("en-IN", {
    month: "short",
    year: "numeric",
  });
}

function formatPercent(value: number | null) {
  return value == null ? "-" : `${value.toFixed(1)}%`;
}

export function AutoSalesPage() {
  const [data, setData] = useState<AutoSales[]>([]);
  const [segment, setSegment] = useState("");
  const [symbol, setSymbol] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchAutoSales({
          symbol: symbol || undefined,
          segment: segment || undefined,
        });
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load auto sales");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [segment, symbol]);

  const companies = useMemo(() => {
    const values = new Map<string, string>();
    data.forEach((row) => values.set(row.symbol, row.company_name));
    return Array.from(values.entries()).sort((a, b) =>
      a[1].localeCompare(b[1]),
    );
  }, [data]);

  const chartData = useMemo(() => {
    const grouped = new Map<string, number>();
    data.forEach((row) => {
      const key = row.month;
      grouped.set(key, (grouped.get(key) || 0) + (row.registrations || 0));
    });

    return Array.from(grouped.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, registrations]) => ({
        month: formatMonth(month),
        registrations,
      }));
  }, [data]);

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-white">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Monthly Auto Sales</h1>
          <p className="mt-2 text-slate-400">
            Company-wise and segment-wise monthly vehicle registrations.
          </p>
        </div>

        <div className="mb-6 grid gap-4 rounded-2xl border border-slate-800 bg-slate-900 p-5 md:grid-cols-2">
          <label className="text-sm text-slate-300">
            Company
            <select
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-white"
            >
              <option value="">All companies</option>
              {companies.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-slate-300">
            Segment
            <select
              value={segment}
              onChange={(event) => setSegment(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-white"
            >
              {SEGMENTS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {loading && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-400">
            Loading auto-sales data...
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-6 text-red-300">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <section className="mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <h2 className="mb-5 text-xl font-semibold">Monthly Trend</h2>
              <div className="h-[420px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatNumber(Number(value))} />
                    <Line
                      type="monotone"
                      dataKey="registrations"
                      name="Registrations"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="px-4 py-3 text-left">Month</th>
                    <th className="px-4 py-3 text-left">Company</th>
                    <th className="px-4 py-3 text-left">Segment</th>
                    <th className="px-4 py-3 text-right">Registrations</th>
                    <th className="px-4 py-3 text-right">YoY</th>
                    <th className="px-4 py-3 text-right">Market Share</th>
                    <th className="px-4 py-3 text-left">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((row) => (
                    <tr
                      key={`${row.symbol}-${row.segment}-${row.month}`}
                      className="border-b border-slate-800/80"
                    >
                      <td className="px-4 py-3">{formatMonth(row.month)}</td>
                      <td className="px-4 py-3 font-medium">{row.company_name}</td>
                      <td className="px-4 py-3">{row.segment}</td>
                      <td className="px-4 py-3 text-right">
                        {formatNumber(row.registrations)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {formatPercent(row.yoy_growth)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {formatPercent(row.market_share)}
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {row.source}
                        {row.is_projected ? " (projected)" : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {data.length === 0 && (
                <div className="p-8 text-center text-slate-400">
                  No auto-sales records found. Run the backend sync first.
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
