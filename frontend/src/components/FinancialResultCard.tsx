import { useEffect, useState } from "react";

import { getFinancialResults } from "../api/financialResults";
import type { FinancialResult } from "../api/financialResults";

interface Props {
  symbol: string;
}

const CRORE = 10_000_000;

function formatCrores(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }

  return `₹${(value / CRORE).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} Cr`;
}

function formatEPS(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }

  return `₹${value.toFixed(2)}`;
}

function formatGrowth(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function growthClass(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "text-slate-500";
  }

  if (value > 0) return "text-emerald-400";
  if (value < 0) return "text-red-400";
  return "text-slate-400";
}

function formatPeriod(value: string | null): string {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function resultClass(result: string | null | undefined): string {
  switch (result) {
    case "BEAT":
      return "text-emerald-400";
    case "MISS":
      return "text-red-400";
    case "MEET":
      return "text-yellow-400";
    default:
      return "text-slate-500";
  }
}

function resultLabel(result: string | null | undefined): string {
  switch (result) {
    case "BEAT":
      return "BEAT";
    case "MISS":
      return "MISS";
    case "MEET":
      return "MEET";
    default:
      return "—";
  }
}

function formatSurprise(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "";
  }

  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function EstimateLine({
  estimate,
  result,
  surprise,
  formatter,
}: {
  estimate: number | null;
  result: string | null;
  surprise: number | null;
  formatter: (value: number | null | undefined) => string;
}) {
  if (estimate === null || estimate === undefined || !Number.isFinite(estimate)) {
    return (
      <div className="mt-1 text-xs text-slate-600">
        Analyst estimate unavailable
      </div>
    );
  }

  return (
    <div className="mt-1">
      <div className="text-xs text-slate-500">
        Est. {formatter(estimate)}
      </div>
      <div className={`mt-0.5 text-xs font-semibold ${resultClass(result)}`}>
        {resultLabel(result)}
        {surprise !== null && surprise !== undefined && ` ${formatSurprise(surprise)}`}
      </div>
    </div>
  );
}

function MetricCell({
  actual,
  estimate,
  result,
  surprise,
  yoy,
  formatter,
}: {
  actual: number | null;
  estimate: number | null;
  result: string | null;
  surprise: number | null;
  yoy: number | null | undefined;
  formatter: (value: number | null | undefined) => string;
}) {
  return (
    <td className="px-4 py-4 text-right align-top">
      <div className="font-medium tabular-nums text-slate-200">
        {formatter(actual)}
      </div>

      <EstimateLine
        estimate={estimate}
        result={result}
        surprise={surprise}
        formatter={formatter}
      />

      {yoy !== null && yoy !== undefined && (
        <div className={`mt-1 text-xs font-medium ${growthClass(yoy)}`}>
          YoY {formatGrowth(yoy)}
        </div>
      )}
    </td>
  );
}

export function FinancialResultCard({ symbol }: Props) {
  const [results, setResults] = useState<FinancialResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(false);

    getFinancialResults(symbol, 40)
      .then((data) => {
        if (!cancelled) setResults(data);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [symbol]);

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5 text-slate-400">
        Loading financial results...
      </div>
    );
  }

  if (error || results.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5 text-slate-400">
        No financial results available for {symbol}.
      </div>
    );
  }

  const latest = results[0];
  const hasAnyEstimate = results.some(
    (result) =>
      result.revenue_estimate !== null ||
      result.ebitda_estimate !== null ||
      result.pat_estimate !== null ||
      result.eps_estimate !== null,
  );

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 p-5">
        <div>
          <h2 className="text-lg font-semibold text-white">Financial Results</h2>
          <p className="mt-1 text-sm text-slate-400">
            Quarterly financial performance · values shown in ₹ crore
          </p>
        </div>

        {latest.overall_result && latest.overall_result !== "UNKNOWN" && (
          <div
            className={`rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold ${resultClass(
              latest.overall_result,
            )}`}
          >
            Overall {resultLabel(latest.overall_result)}
          </div>
        )}
      </div>

      {latest.summary && (
        <div className="border-b border-slate-800 bg-slate-900/70 px-5 py-4 text-sm text-slate-300">
          {latest.summary}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4 border-b border-slate-800 px-5 py-3 text-xs">
        <span className="text-slate-500">Estimate = analyst consensus</span>
        <span className="text-emerald-400">BEAT</span>
        <span className="text-red-400">MISS</span>
        <span className="text-yellow-400">MEET</span>
        {!hasAnyEstimate && (
          <span className="text-amber-400">
            Analyst estimates are not available for these periods
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1050px] border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950">
              <th className="sticky left-0 z-10 bg-slate-950 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                Period
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                Revenue
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                EBITDA
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                PAT
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                EPS
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">
                Overall
              </th>
            </tr>
          </thead>

          <tbody>
            {results.map((result) => (
              <tr
                key={result.id}
                className="border-b border-slate-800 last:border-b-0 hover:bg-slate-800/30"
              >
                <td className="sticky left-0 z-[1] bg-slate-900 px-4 py-4 align-top">
                  <div className="whitespace-nowrap font-semibold text-white">
                    {formatPeriod(result.period_ended)}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {result.period_type || "Quarterly"} · {result.consolidated ? "Consolidated" : "Standalone"}
                  </div>
                </td>

                <MetricCell
                  actual={result.revenue}
                  estimate={result.revenue_estimate}
                  result={result.revenue_result}
                  surprise={result.revenue_surprise_pct}
                  yoy={result.revenue_yoy}
                  formatter={formatCrores}
                />

                <MetricCell
                  actual={result.ebitda}
                  estimate={result.ebitda_estimate}
                  result={result.ebitda_result}
                  surprise={result.ebitda_surprise_pct}
                  yoy={result.ebitda_yoy}
                  formatter={formatCrores}
                />

                <MetricCell
                  actual={result.pat}
                  estimate={result.pat_estimate}
                  result={result.pat_result}
                  surprise={result.pat_surprise_pct}
                  yoy={result.pat_yoy}
                  formatter={formatCrores}
                />

                <MetricCell
                  actual={result.eps}
                  estimate={result.eps_estimate}
                  result={result.eps_result}
                  surprise={result.eps_surprise_pct}
                  yoy={result.eps_yoy}
                  formatter={formatEPS}
                />

                <td className="px-4 py-4 text-center align-top">
                  <span
                    className={`inline-flex rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold ${resultClass(
                      result.overall_result,
                    )}`}
                  >
                    {resultLabel(result.overall_result)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-slate-800 px-5 py-3 text-xs text-slate-500">
        Revenue, EBITDA and PAT are displayed in ₹ crore. EPS is ₹ per share. A missing estimate means analyst consensus data was not returned by the estimates provider; it is not treated as a zero.
      </div>

      {latest.source_url && (
        <div className="border-t border-slate-800 px-5 py-4">
          <a
            href={latest.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            View latest filing →
          </a>
        </div>
      )}
    </div>
  );
}
