import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PriceChart } from "../components/PriceChart";
import { useQuote } from "../hooks/useQuote";
import { UpdateFeed } from "../components/UpdateFeed";

function formatNumber(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  return value.toLocaleString(
    "en-IN",
    {
      maximumFractionDigits: 2,
    },
  );
}

function formatVolume(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  if (value >= 1_000_000) {
    return `${(
      value / 1_000_000
    ).toFixed(2)}M`;
  }

  if (value >= 1_000) {
    return `${(
      value / 1_000
    ).toFixed(2)}K`;
  }

  return value.toString();
}

export function StockDetail() {
  const {
    symbol = "",
  } = useParams();

  const [period, setPeriod] =
    useState("1mo");

  const [interval, setInterval] =
    useState("1d");

  const {
    data: quote,
    isLoading,
    isError,
  } = useQuote(symbol);

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-950 p-8">
        <div className="text-slate-400">
          Loading {symbol}...
        </div>
      </main>
    );
  }

  if (isError || !quote) {
    return (
      <main className="min-h-screen bg-slate-950 p-8">
        <div className="text-red-400">
          Unable to load market data for{" "}
          {symbol}.
        </div>
      </main>
    );
  }

  const positive =
    (quote.change_percent ?? 0) >= 0;

  return (
    <main className="min-h-screen bg-slate-950">
      <div className="mx-auto max-w-6xl px-6 py-8">

        {/* Back */}
        <Link
          to="/"
          className="text-sm text-blue-400 hover:text-blue-300"
        >
          ← Back to Dashboard
        </Link>

        {/* Header */}
        <header className="mb-6 mt-6">
          <div className="text-sm text-slate-500">
            NSE
          </div>

          <h1 className="text-3xl font-bold text-white">
            {quote.symbol}
          </h1>

          <p className="mt-1 text-slate-400">
            Stock details and market updates
          </p>
        </header>

        {/* Stock information */}
        <section
          className="
            rounded-2xl
            border border-slate-800
            bg-slate-900
            p-6
          "
        >
          <div className="flex flex-wrap items-end gap-4">

            <div>
              <div className="text-4xl font-bold text-white">
                ₹{formatNumber(quote.price)}
              </div>

              <div
                className={
                  positive
                    ? "mt-2 text-emerald-400"
                    : "mt-2 text-red-400"
                }
              >
                {positive ? "+" : ""}
                {formatNumber(
                  quote.change,
                )}{" "}
                ({positive ? "+" : ""}
                {formatNumber(
                  quote.change_percent,
                )}
                %)
              </div>
            </div>

          </div>

          {/* Metrics */}
          <div
            className="
              mt-8
              grid
              grid-cols-2
              gap-4
              md:grid-cols-5
            "
          >
            <Metric
              label="Previous Close"
              value={formatNumber(
                quote.previous_close,
              )}
            />

            <Metric
              label="Open"
              value={formatNumber(
                quote.open,
              )}
            />

            <Metric
              label="Day High"
              value={formatNumber(
                quote.day_high,
              )}
            />

            <Metric
              label="Day Low"
              value={formatNumber(
                quote.day_low,
              )}
            />

            <Metric
              label="Volume"
              value={formatVolume(
                quote.volume,
              )}
            />
          </div>
        </section>

        {/* ===================================================== */}
        {/* PRICE HISTORY */}
        {/* ===================================================== */}

        <section
          className="
            mt-6
            rounded-2xl
            border border-slate-800
            bg-slate-900
            p-6
          "
        >

          {/* Title */}
          <h2
            className="
              mb-5
              text-xl
              font-semibold
              text-white
            "
          >
            Price History
          </h2>

          {/* ================================================= */}
          {/* RANGE BUTTONS */}
          {/* ================================================= */}

          <div
            className="
              mb-6
              flex
              w-full
              flex-wrap
              gap-2
            "
          >

            {/* 1 DAY */}
            <button
              type="button"
              onClick={() => {
                setPeriod("1d");
                setInterval("5m");
              }}
              className={
                period === "1d"
                  ? `
                    rounded-lg
                    border
                    border-blue-500
                    bg-blue-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                  `
                  : `
                    rounded-lg
                    border
                    border-slate-700
                    bg-slate-800
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-slate-300
                    hover:bg-slate-700
                    hover:text-white
                  `
              }
            >
              1D
            </button>

            {/* 5 DAYS */}
            <button
              type="button"
              onClick={() => {
                setPeriod("5d");
                setInterval("15m");
              }}
              className={
                period === "5d"
                  ? `
                    rounded-lg
                    border
                    border-blue-500
                    bg-blue-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                  `
                  : `
                    rounded-lg
                    border
                    border-slate-700
                    bg-slate-800
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-slate-300
                    hover:bg-slate-700
                    hover:text-white
                  `
              }
            >
              5D
            </button>

            {/* 1 MONTH */}
            <button
              type="button"
              onClick={() => {
                setPeriod("1mo");
                setInterval("1d");
              }}
              className={
                period === "1mo"
                  ? `
                    rounded-lg
                    border
                    border-blue-500
                    bg-blue-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                  `
                  : `
                    rounded-lg
                    border
                    border-slate-700
                    bg-slate-800
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-slate-300
                    hover:bg-slate-700
                    hover:text-white
                  `
              }
            >
              1M
            </button>

            {/* 3 MONTHS */}
            <button
              type="button"
              onClick={() => {
                setPeriod("3mo");
                setInterval("1d");
              }}
              className={
                period === "3mo"
                  ? `
                    rounded-lg
                    border
                    border-blue-500
                    bg-blue-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                  `
                  : `
                    rounded-lg
                    border
                    border-slate-700
                    bg-slate-800
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-slate-300
                    hover:bg-slate-700
                    hover:text-white
                  `
              }
            >
              3M
            </button>

            {/* 6 MONTHS */}
            <button
              type="button"
              onClick={() => {
                setPeriod("6mo");
                setInterval("1d");
              }}
              className={
                period === "6mo"
                  ? `
                    rounded-lg
                    border
                    border-blue-500
                    bg-blue-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                  `
                  : `
                    rounded-lg
                    border
                    border-slate-700
                    bg-slate-800
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-slate-300
                    hover:bg-slate-700
                    hover:text-white
                  `
              }
            >
              6M
            </button>

            {/* 1 YEAR */}
            <button
              type="button"
              onClick={() => {
                setPeriod("1y");
                setInterval("1d");
              }}
              className={
                period === "1y"
                  ? `
                    rounded-lg
                    border
                    border-blue-500
                    bg-blue-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                  `
                  : `
                    rounded-lg
                    border
                    border-slate-700
                    bg-slate-800
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-slate-300
                    hover:bg-slate-700
                    hover:text-white
                  `
              }
            >
              1Y
            </button>

            {/* 5 YEARS */}
            <button
              type="button"
              onClick={() => {
                setPeriod("5y");
                setInterval("1wk");
              }}
              className={
                period === "5y"
                  ? `
                    rounded-lg
                    border
                    border-blue-500
                    bg-blue-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                  `
                  : `
                    rounded-lg
                    border
                    border-slate-700
                    bg-slate-800
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-slate-300
                    hover:bg-slate-700
                    hover:text-white
                  `
              }
            >
              5Y
            </button>

            {/* 10 YEARS */}
            <button
              type="button"
              onClick={() => {
                setPeriod("10y");
                setInterval("1mo");
              }}
              className={
                period === "10y"
                  ? `
                    rounded-lg
                    border
                    border-blue-500
                    bg-blue-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                  `
                  : `
                    rounded-lg
                    border
                    border-slate-700
                    bg-slate-800
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-slate-300
                    hover:bg-slate-700
                    hover:text-white
                  `
              }
            >
              10Y
            </button>

            {/* MAX */}
            <button
              type="button"
              onClick={() => {
                setPeriod("max");
                setInterval("1mo");
              }}
              className={
                period === "max"
                  ? `
                    rounded-lg
                    border
                    border-blue-500
                    bg-blue-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                  `
                  : `
                    rounded-lg
                    border
                    border-slate-700
                    bg-slate-800
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-slate-300
                    hover:bg-slate-700
                    hover:text-white
                  `
              }
            >
              MAX
            </button>

          </div>

          {/* ================================================= */}
          {/* PRICE CHART */}
          {/* ================================================= */}

          <PriceChart
            symbol={symbol}
            period={period}
            interval={interval}
          />

        </section>

        {/* ===================================================== */}
        {/* LATEST UPDATES */}
        {/* ===================================================== */}

        <section
          className="
            mt-6
            rounded-2xl
            border
            border-slate-800
            bg-slate-900
            p-6
          "
        >

          <div className="mb-5">

            <h2
              className="
                text-xl
                font-semibold
                text-white
              "
            >
              Latest Updates
            </h2>

          </div>

          <UpdateFeed
            symbol={symbol}
          />

        </section>

      </div>
    </main>
  );
}

interface MetricProps {
  label: string;
  value: string;
}

function Metric({
  label,
  value,
}: MetricProps) {
  return (
    <div>
      <div className="text-sm text-slate-500">
        {label}
      </div>

      <div className="mt-1 font-medium text-slate-200">
        {value}
      </div>
    </div>
  );
}
