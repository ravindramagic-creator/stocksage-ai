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
    return "text-emerald-400";
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

  return value.toLocaleString(
    "en-IN",
    {
      maximumFractionDigits: 2,
    },
  );
}


function formatPeriod(
  value: string | null,
): string {

  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
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


function formatPeriodType(
  result: FinancialResult,
): string {

  if (
    result.period_type
  ) {
    return result.period_type;
  }

  return "Quarter";
}


export function FinancialResultCard({
  symbol,
}: Props) {

  const [
    results,
    setResults,
  ] = useState<FinancialResult[]>([]);

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
      .then((data) => {

        if (!cancelled) {
          setResults(data);
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


  const latestResult =
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

      {/* Header */}

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


        {latestResult.market_view && (

          <span
            className="
              rounded-full
              bg-blue-500/10
              px-3
              py-1
              text-xs
              font-medium
              text-blue-400
            "
          >
            {latestResult.market_view}
          </span>

        )}

      </div>


      {/* Latest Result Summary */}

      {latestResult.summary && (

        <div
          className="
            border-b
            border-slate-800
            px-5
            py-4
          "
        >

          <p
            className="
              text-sm
              leading-6
              text-slate-300
            "
          >
            {latestResult.summary}
          </p>

        </div>

      )}


      {/* Desktop Table */}

      <div className="hidden overflow-x-auto md:block">

        <table
          className="
            w-full
            min-w-[1000px]
            text-left
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
                  px-5
                  py-3
                  text-xs
                  font-medium
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
                  font-medium
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
                  font-medium
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                Rev YoY
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-right
                  text-xs
                  font-medium
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
                  font-medium
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                EBITDA YoY
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-right
                  text-xs
                  font-medium
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
                  font-medium
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                PAT YoY
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-right
                  text-xs
                  font-medium
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >
                EPS
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
                    border-slate-800/70
                    transition-colors
                    hover:bg-slate-800/40
                  "
                >

                  {/* Period */}

                  <td
                    className="
                      px-5
                      py-4
                    "
                  >

                    <div
                      className="
                        font-medium
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
                      {formatPeriodType(
                        result,
                      )}

                      {result.consolidated
                        ? " • Consolidated"
                        : " • Standalone"}
                    </div>

                  </td>


                  {/* Revenue */}

                  <td
                    className="
                      px-4
                      py-4
                      text-right
                      font-medium
                      text-slate-200
                    "
                  >
                    {formatNumber(
                      result.revenue,
                    )}
                  </td>


                  {/* Revenue YoY */}

                  <td
                    className={`
                      px-4
                      py-4
                      text-right
                      font-medium
                      ${growthClass(
                        result.revenue_yoy,
                      )}
                    `}
                  >
                    {formatGrowth(
                      result.revenue_yoy,
                    )}
                  </td>


                  {/* EBITDA */}

                  <td
                    className="
                      px-4
                      py-4
                      text-right
                      font-medium
                      text-slate-200
                    "
                  >
                    {formatNumber(
                      result.ebitda,
                    )}
                  </td>


                  {/* EBITDA YoY */}

                  <td
                    className={`
                      px-4
                      py-4
                      text-right
                      font-medium
                      ${growthClass(
                        result.ebitda_yoy,
                      )}
                    `}
                  >
                    {formatGrowth(
                      result.ebitda_yoy,
                    )}
                  </td>


                  {/* PAT */}

                  <td
                    className="
                      px-4
                      py-4
                      text-right
                      font-medium
                      text-slate-200
                    "
                  >
                    {formatNumber(
                      result.pat,
                    )}
                  </td>


                  {/* PAT YoY */}

                  <td
                    className={`
                      px-4
                      py-4
                      text-right
                      font-medium
                      ${growthClass(
                        result.pat_yoy,
                      )}
                    `}
                  >
                    {formatGrowth(
                      result.pat_yoy,
                    )}
                  </td>


                  {/* EPS */}

                  <td
                    className="
                      px-4
                      py-4
                      text-right
                      font-semibold
                      text-white
                    "
                  >
                    {result.eps !== null &&
                    result.eps !== undefined
                      ? Number(
                          result.eps,
                        ).toFixed(2)
                      : "—"}
                  </td>

                </tr>

              ),
            )}

          </tbody>

        </table>

      </div>


      {/* Mobile Cards */}

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
              className="
                p-5
              "
            >

              <div
                className="
                  mb-4
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
                    {formatPeriodType(
                      result,
                    )}

                    {result.consolidated
                      ? " • Consolidated"
                      : " • Standalone"}
                  </div>

                </div>


                <div
                  className="
                    text-right
                  "
                >

                  <div
                    className="
                      text-xs
                      text-slate-500
                    "
                  >
                    EPS
                  </div>

                  <div
                    className="
                      font-semibold
                      text-white
                    "
                  >
                    {result.eps !== null &&
                    result.eps !== undefined
                      ? Number(
                          result.eps,
                        ).toFixed(2)
                      : "—"}
                  </div>

                </div>

              </div>


              <div
                className="
                  grid
                  grid-cols-2
                  gap-3
                "
              >

                <MobileMetric
                  label="Revenue"
                  value={formatNumber(
                    result.revenue,
                  )}
                />

                <MobileMetric
                  label="Revenue YoY"
                  value={formatGrowth(
                    result.revenue_yoy,
                  )}
                  className={growthClass(
                    result.revenue_yoy,
                  )}
                />

                <MobileMetric
                  label="EBITDA"
                  value={formatNumber(
                    result.ebitda,
                  )}
                />

                <MobileMetric
                  label="EBITDA YoY"
                  value={formatGrowth(
                    result.ebitda_yoy,
                  )}
                  className={growthClass(
                    result.ebitda_yoy,
                  )}
                />

                <MobileMetric
                  label="PAT"
                  value={formatNumber(
                    result.pat,
                  )}
                />

                <MobileMetric
                  label="PAT YoY"
                  value={formatGrowth(
                    result.pat_yoy,
                  )}
                  className={growthClass(
                    result.pat_yoy,
                  )}
                />

              </div>

            </div>

          ),
        )}

      </div>


      {/* Source */}

      {latestResult.source_url && (

        <div
          className="
            border-t
            border-slate-800
            px-5
            py-4
          "
        >

          <a
            href={latestResult.source_url}
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


interface MobileMetricProps {
  label: string;
  value: string;
  className?: string;
}


function MobileMetric({
  label,
  value,
  className = "text-slate-200",
}: MobileMetricProps) {

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
          font-semibold
          ${className}
        `}
      >
        {value}
      </div>

    </div>
  );
}
