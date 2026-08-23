import { useEffect, useState } from "react";

import {
  getFinancialResults,
} from "../api/financialResults";

import type {
  FinancialResult,
} from "../api/financialResults";


interface Props {
  symbol: string;
}


// =========================================================
// Number
// =========================================================

function formatNumber(
  value: number | null | undefined,
): string {

  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  return Number(
    value,
  ).toLocaleString(
    "en-IN",
    {
      maximumFractionDigits: 2,
    },
  );
}


// =========================================================
// EPS
// =========================================================

function formatEPS(
  value: number | null | undefined,
): string {

  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  return Number(
    value,
  ).toFixed(2);
}


// =========================================================
// Growth
// =========================================================

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
    value > 0
      ? "+"
      : "";

  return (
    `${sign}${value.toFixed(1)}%`
  );
}


function growthClass(
  value: number | null | undefined,
): string {

  if (
    value === null ||
    value === undefined
  ) {
    return "text-slate-400";
  }

  if (value > 0) {
    return "text-emerald-400";
  }

  if (value < 0) {
    return "text-red-400";
  }

  return "text-slate-400";
}


// =========================================================
// Period
// =========================================================

function formatPeriod(
  value: string | null,
): string {

  if (!value) {
    return "—";
  }

  const date = new Date(
    value,
  );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return date.toLocaleDateString(
    "en-IN",
    {
      month: "short",
      year: "numeric",
    },
  );
}


// =========================================================
// Result color
// =========================================================

function resultClass(
  result: string | null | undefined,
): string {

  switch (
    result
  ) {

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


// =========================================================
// Result label
// =========================================================

function resultLabel(
  result: string | null | undefined,
): string {

  switch (
    result
  ) {

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


// =========================================================
// Surprise
// =========================================================

function formatSurprise(
  value: number | null | undefined,
): string {

  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return "";
  }

  const sign =
    value >= 0
      ? "+"
      : "";

  return (
    `${sign}${value.toFixed(1)}%`
  );
}


// =========================================================
// Estimate line
// =========================================================

function EstimateLine({
  estimate,
  result,
  surprise,
  formatter = formatNumber,
}: {
  estimate: number | null;
  result: string | null;
  surprise: number | null;
  formatter?: (
    value: number | null | undefined,
  ) => string;
}) {

  if (
    estimate === null ||
    estimate === undefined
  ) {

    return (
      <div className="mt-1 text-xs text-slate-500">
        Estimate —
      </div>
    );
  }

  return (
    <div className="mt-1">

      <div className="text-xs text-slate-500">
        Est. {formatter(estimate)}
      </div>

      <div
        className={`
          mt-0.5
          text-xs
          font-semibold
          ${resultClass(result)}
        `}
      >
        {resultLabel(result)}

        {surprise !== null &&
          surprise !== undefined &&
          ` ${formatSurprise(surprise)}`}
      </div>

    </div>
  );
}


// =========================================================
// Metric cell
// =========================================================

function MetricCell({
  actual,
  estimate,
  result,
  surprise,
  yoy,
  formatter = formatNumber,
}: {
  actual: number | null;
  estimate: number | null;
  result: string | null;
  surprise: number | null;
  yoy?: number | null;
  formatter?: (
    value: number | null | undefined,
  ) => string;
}) {

  return (
    <td
      className="
        px-4
        py-4
        text-right
        align-top
      "
    >

      <div
        className="
          font-medium
          text-slate-200
        "
      >
        {formatter(actual)}
      </div>

      <EstimateLine
        estimate={estimate}
        result={result}
        surprise={surprise}
        formatter={formatter}
      />

      {yoy !== undefined && (
        <div
          className={`
            mt-1
            text-xs
            font-medium
            ${growthClass(yoy)}
          `}
        >
          YoY {formatGrowth(yoy)}
        </div>
      )}

    </td>
  );
}


// =========================================================
// Financial Result Card
// =========================================================

export function FinancialResultCard({
  symbol,
}: Props) {

  const [
    results,
    setResults,
  ] = useState<FinancialResult[]>(
    [],
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

    getFinancialResults(
      symbol,
      8,
    )
      .then(
        (data) => {

          if (!cancelled) {

            setResults(
              data,
            );
          }
        },
      )
      .catch(
        () => {

          if (!cancelled) {

            setError(
              true,
            );
          }
        },
      )
      .finally(
        () => {

          if (!cancelled) {

            setLoading(
              false,
            );
          }
        },
      );

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


  if (
    error ||
    results.length === 0
  ) {

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


  const latest =
    results[0];


  return (
    <div
      className="
        overflow-hidden
        rounded-xl
        border
        border-slate-800
        bg-slate-900
      "
    >

      {/* =====================================================
          Header
      ===================================================== */}

      <div
        className="
          flex
          flex-wrap
          items-center
          justify-between
          gap-3
          border-b
          border-slate-800
          p-5
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
            Financial Results
          </h2>

          <p
            className="
              mt-1
              text-sm
              text-slate-400
            "
          >
            Quarterly financial performance
          </p>

        </div>


        {latest.overall_result &&
          latest.overall_result !==
            "UNKNOWN" && (

          <div
            className={`
              rounded-full
              px-3
              py-1
              text-xs
              font-semibold
              ${resultClass(
                latest.overall_result,
              )}
              bg-slate-950
            `}
          >
            Overall{" "}
            {resultLabel(
              latest.overall_result,
            )}
          </div>

        )}

      </div>


      {/* =====================================================
          Latest summary
      ===================================================== */}

      {latest.summary && (

        <div
          className="
            border-b
            border-slate-800
            bg-slate-900/70
            px-5
            py-4
            text-sm
            text-slate-300
          "
        >
          {latest.summary}
        </div>

      )}


      {/* =====================================================
          Legend
      ===================================================== */}

      <div
        className="
          flex
          flex-wrap
          gap-4
          border-b
          border-slate-800
          px-5
          py-3
          text-xs
        "
      >

        <span className="text-slate-500">
          Estimate = analyst consensus
        </span>

        <span className="text-emerald-400">
          BEAT
        </span>

        <span className="text-red-400">
          MISS
        </span>

        <span className="text-yellow-400">
          MEET
        </span>

      </div>


      {/* =====================================================
          Desktop table
      ===================================================== */}

      <div
        className="
          hidden
          overflow-x-auto
          md:block
        "
      >

        <table
          className="
            w-full
            min-w-[1250px]
            border-collapse
          "
        >

          <thead>

            <tr
              className="
                border-b
                border-slate-800
                bg-slate-950
              "
            >

              <th
                className="
                  px-4
                  py-3
                  text-left
                  text-xs
                  font-semibold
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                Period
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-right
                  text-xs
                  font-semibold
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                Revenue
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-right
                  text-xs
                  font-semibold
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                EBITDA
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-right
                  text-xs
                  font-semibold
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                PAT
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-right
                  text-xs
                  font-semibold
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                EPS
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-center
                  text-xs
                  font-semibold
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                Overall
              </th>

            </tr>

          </thead>


          <tbody>

            {results.map(
              (result) => (

                <tr
                  key={result.id}
                  className="
                    border-b
                    border-slate-800
                    last:border-b-0
                    hover:bg-slate-800/30
                  "
                >

                  {/* Period */}

                  <td
                    className="
                      px-4
                      py-4
                      align-top
                    "
                  >

                    <div
                      className="
                        font-semibold
                        text-white
                      "
                    >
                      {formatPeriod(
                        result.period_ended,
                      )}
                    </div>

                    <div
                      className="
                        mt-1
                        text-xs
                        text-slate-500
                      "
                    >
                      {result.period_type ||
                        "Quarterly"}

                      {" • "}

                      {result.consolidated
                        ? "Consolidated"
                        : "Standalone"}
                    </div>

                  </td>


                  {/* Revenue */}

                  <MetricCell
                    actual={
                      result.revenue
                    }
                    estimate={
                      result.revenue_estimate
                    }
                    result={
                      result.revenue_result
                    }
                    surprise={
                      result.revenue_surprise_pct
                    }
                    yoy={
                      result.revenue_yoy
                    }
                  />


                  {/* EBITDA */}

                  <MetricCell
                    actual={
                      result.ebitda
                    }
                    estimate={
                      result.ebitda_estimate
                    }
                    result={
                      result.ebitda_result
                    }
                    surprise={
                      result.ebitda_surprise_pct
                    }
                    yoy={
                      result.ebitda_yoy
                    }
                  />


                  {/* PAT */}

                  <MetricCell
                    actual={
                      result.pat
                    }
                    estimate={
                      result.pat_estimate
                    }
                    result={
                      result.pat_result
                    }
                    surprise={
                      result.pat_surprise_pct
                    }
                    yoy={
                      result.pat_yoy
                    }
                  />


                  {/* EPS */}

                  <MetricCell
                    actual={
                      result.eps
                    }
                    estimate={
                      result.eps_estimate
                    }
                    result={
                      result.eps_result
                    }
                    surprise={
                      result.eps_surprise_pct
                    }
                    formatter={
                      formatEPS
                    }
                    yoy={
                      result.eps_yoy
                    }
                  />


                  {/* Overall */}

                  <td
                    className="
                      px-4
                      py-4
                      text-center
                      align-top
                    "
                  >

                    <span
                      className={`
                        inline-flex
                        rounded-full
                        bg-slate-950
                        px-3
                        py-1
                        text-xs
                        font-semibold
                        ${resultClass(
                          result.overall_result,
                        )}
                      `}
                    >
                      {resultLabel(
                        result.overall_result,
                      )}
                    </span>

                  </td>

                </tr>

              ),
            )}

          </tbody>

        </table>

      </div>


      {/* =====================================================
          Mobile
      ===================================================== */}

      <div
        className="
          divide-y
          divide-slate-800
          md:hidden
        "
      >

        {results.map(
          (result) => (

            <div
              key={result.id}
              className="p-5"
            >

              <div
                className="
                  flex
                  items-start
                  justify-between
                  gap-3
                "
              >

                <div>

                  <div
                    className="
                      font-semibold
                      text-white
                    "
                  >
                    {formatPeriod(
                      result.period_ended,
                    )}
                  </div>

                  <div
                    className="
                      mt-1
                      text-xs
                      text-slate-500
                    "
                  >
                    {result.period_type ||
                      "Quarterly"}

                    {" • "}

                    {result.consolidated
                      ? "Consolidated"
                      : "Standalone"}
                  </div>

                </div>


                <span
                  className={`
                    rounded-full
                    bg-slate-950
                    px-3
                    py-1
                    text-xs
                    font-semibold
                    ${resultClass(
                      result.overall_result,
                    )}
                  `}
                >
                  {resultLabel(
                    result.overall_result,
                  )}
                </span>

              </div>


              <div
                className="
                  mt-4
                  grid
                  grid-cols-1
                  gap-3
                "
              >

                <MobileMetric
                  label="Revenue"
                  actual={
                    result.revenue
                  }
                  estimate={
                    result.revenue_estimate
                  }
                  result={
                    result.revenue_result
                  }
                  surprise={
                    result.revenue_surprise_pct
                  }
                  yoy={
                    result.revenue_yoy
                  }
                />

                <MobileMetric
                  label="EBITDA"
                  actual={
                    result.ebitda
                  }
                  estimate={
                    result.ebitda_estimate
                  }
                  result={
                    result.ebitda_result
                  }
                  surprise={
                    result.ebitda_surprise_pct
                  }
                  yoy={
                    result.ebitda_yoy
                  }
                />

                <MobileMetric
                  label="PAT"
                  actual={
                    result.pat
                  }
                  estimate={
                    result.pat_estimate
                  }
                  result={
                    result.pat_result
                  }
                  surprise={
                    result.pat_surprise_pct
                  }
                  yoy={
                    result.pat_yoy
                  }
                />

                <MobileMetric
                  label="EPS"
                  actual={
                    result.eps
                  }
                  estimate={
                    result.eps_estimate
                  }
                  result={
                    result.eps_result
                  }
                  surprise={
                    result.eps_surprise_pct
                  }
                  yoy={
                    result.eps_yoy
                  }
                  formatter={
                    formatEPS
                  }
                />

              </div>

            </div>

          ),
        )}

      </div>


      {/* =====================================================
          Source
      ===================================================== */}

      {latest.source_url && (

        <div
          className="
            border-t
            border-slate-800
            px-5
            py-4
          "
        >

          <a
            href={
              latest.source_url
            }
            target="_blank"
            rel="noopener noreferrer"
            className="
              text-sm
              text-blue-400
              hover:text-blue-300
            "
          >
            View latest filing →
          </a>

        </div>

      )}

    </div>
  );
}


// =========================================================
// Mobile metric
// =========================================================

interface MobileMetricProps {
  label: string;

  actual: number | null;

  estimate: number | null;

  result: string | null;

  surprise: number | null;

  yoy: number | null;

  formatter?: (
    value: number | null | undefined,
  ) => string;
}


function MobileMetric({
  label,
  actual,
  estimate,
  result,
  surprise,
  yoy,
  formatter = formatNumber,
}: MobileMetricProps) {

  return (
    <div
      className="
        rounded-lg
        bg-slate-950
        p-4
      "
    >

      <div
        className="
          text-xs
          font-medium
          text-slate-500
        "
      >
        {label}
      </div>


      <div
        className="
          mt-1
          text-lg
          font-semibold
          text-white
        "
      >
        {formatter(actual)}
      </div>


      <EstimateLine
        estimate={estimate}
        result={result}
        surprise={surprise}
        formatter={formatter}
      />


      {yoy !== null &&
        yoy !== undefined && (

        <div
          className={`
            mt-1
            text-xs
            font-medium
            ${growthClass(yoy)}
          `}
        >
          YoY {formatGrowth(yoy)}
        </div>

      )}

    </div>
  );
}
