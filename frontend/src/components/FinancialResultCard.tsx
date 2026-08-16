import { useEffect, useState } from "react";

import {
  getLatestFinancialResult,
} from "../api/financialResults";

import type {
  FinancialResult,
} from "../api/financialResults";

interface Props {
  symbol: string;
}


function growthClass(
  value: number | null | undefined,
): string {

  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return "text-slate-400";
  }

  if (value > 0) {
    return "text-green-400";
  }

  if (value < 0) {
    return "text-red-400";
  }

  return "text-slate-400";
}

function formatGrowth(
  value: number | null | undefined,
): string {

  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  const sign =
    value > 0 ? "+" : "";

  return `${sign}${value.toFixed(1)}%`;
}

export function FinancialResultCard({
  symbol,
}: Props) {

  const [
    result,
    setResult,
  ] = useState<FinancialResult | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState(false);


  useEffect(() => {

    let cancelled = false;

    setLoading(true);
    setError(false);

    getLatestFinancialResult(symbol)
      .then((data) => {

        if (!cancelled) {
          setResult(data);
        }

      })
      .catch(() => {

        if (!cancelled) {
          setError(true);
        }

      })
      .finally(() => {

        if (!cancelled) {
          setLoading(false);
        }

      });


    return () => {
      cancelled = true;
    };

  }, [symbol]);


  if (loading) {

    return (
      <div
        className="
          rounded-xl
          border
          border-slate-800
          bg-slate-900
          p-5
          text-slate-400
        "
      >
        Loading financial results...
      </div>
    );
  }


  if (error || !result) {

    return (
      <div
        className="
          rounded-xl
          border
          border-slate-800
          bg-slate-900
          p-5
          text-slate-400
        "
      >
        No financial results available
        for {symbol}.
      </div>
    );
  }


  return (
    <div
      className="
        rounded-xl
        border
        border-slate-800
        bg-slate-900
        p-5
      "
    >

      <div
        className="
          flex
          items-center
          justify-between
        "
      >

        <div>

          <h2
            className="
              text-lg
              font-semibold
              text-white
            "
          >
            Latest Results
          </h2>

          <p
            className="
              text-sm
              text-slate-400
            "
          >
            {result.symbol}
          </p>

        </div>


        {result.market_view && (
          <span
            className="
              rounded-full
              bg-green-500/10
              px-3
              py-1
              text-xs
              font-medium
              text-green-400
            "
          >
            {result.market_view}
          </span>
        )}

      </div>


      {result.summary && (
        <p
          className="
            mt-4
            text-sm
            text-slate-300
          "
        >
          {result.summary}
        </p>
      )}


      <div
        className="
          mt-5
          grid
          grid-cols-2
          gap-3
          md:grid-cols-4
        "
      >

        <Metric
          label="Revenue YoY"
          value={formatGrowth(
            result.revenue_yoy,
          )}
          className={growthClass(
            result.revenue_yoy,
          )}
        />

        <Metric
          label="EBITDA YoY"
          value={formatGrowth(
            result.ebitda_yoy,
          )}
          className={growthClass(
            result.ebitda_yoy,
          )}
        />

        <Metric
          label="PAT YoY"
          value={formatGrowth(
            result.pat_yoy,
          )}
          className={growthClass(
            result.pat_yoy,
          )}
        />

        <Metric
          label="EPS"
          value={
            result.eps !== null
              ? Number(result.eps).toFixed(2) 
              : "—"
          }
          className="text-white"
        />

      </div>


      {result.source_url && (
        <a
          href={result.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="
            mt-4
            inline-block
            text-sm
            text-blue-400
            hover:text-blue-300
          "
        >
          View filing →
        </a>
      )}

    </div>
  );
}


interface MetricProps {
  label: string;
  value: string;
  className: string;
}


function Metric({
  label,
  value,
  className,
}: MetricProps) {

  return (
    <div
      className="
        rounded-lg
        bg-slate-950
        p-3
      "
    >

      <div
        className="
          text-xs
          text-slate-500
        "
      >
        {label}
      </div>

      <div
        className={`
          mt-1
          text-lg
          font-semibold
          ${className}
        `}
      >
        {value}
      </div>

    </div>
  );
}
