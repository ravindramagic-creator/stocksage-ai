import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useHistory } from "../hooks/useHistory";

interface Props {
  symbol: string;
  period: string;
  interval: string;
}

function formatDate(
  timestamp: string,
  period: string,
): string {
  const date = new Date(timestamp);

  // 1 day - show time
  if (period === "1d") {
    return date.toLocaleTimeString(
      "en-IN",
      {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      },
    );
  }

  // 5 days - show day and month
  if (period === "5d") {
    return date.toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
      },
    );
  }

  // 1 month / 3 months / 6 months
  // Show month and year
  if (
    period === "1mo" ||
    period === "3mo" ||
    period === "6mo"
  ) {
    return date.toLocaleDateString(
      "en-IN",
      {
        month: "short",
        year: "numeric",
      },
    );
  }

  // 1 year
  if (period === "1y") {
    return date.toLocaleDateString(
      "en-IN",
      {
        month: "short",
        year: "numeric",
      },
    );
  }

  // 5 years / 10 years / MAX
  // Show only year
  if (
    period === "5y" ||
    period === "10y" ||
    period === "max"
  ) {
    return date.toLocaleDateString(
      "en-IN",
      {
        year: "numeric",
      },
    );
  }

  return date.toLocaleDateString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  );
}

export function PriceChart({
  symbol,
  period,
  interval,
}: Props) {
  const {
    data,
    isLoading,
    isError,
  } = useHistory(
    symbol,
    period,
    interval,
  );

  if (isLoading) {
    return (
      <div className="flex h-80 items-center justify-center text-slate-400">
        Loading chart...
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex h-80 items-center justify-center text-red-400">
        Unable to load price history.
      </div>
    );
  }

  const chartData = data.points
    .filter(
      (point) =>
        point.close !== null,
    )
    .map((point) => ({
      date: formatDate(
        point.timestamp,
        period,
      ),

      timestamp: point.timestamp,

      price: point.close,
    }));

  if (!chartData.length) {
    return (
      <div className="flex h-80 items-center justify-center text-slate-400">
        No historical data available.
      </div>
    );
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer
        width="100%"
        height="100%"
      >
        <LineChart data={chartData}>
          <CartesianGrid
            strokeDasharray="3 3"
            strokeOpacity={0.15}
          />

          <XAxis
            dataKey="date"
            tick={{
              fontSize: 12,
            }}
          />

          <YAxis
            domain={["auto", "auto"]}
            tick={{
              fontSize: 12,
            }}
          />

          <Tooltip
            labelFormatter={(
              _label,
              payload,
            ) => {
              if (
                payload &&
                payload.length > 0
              ) {
                const point =
                  payload[0]
                    .payload;

                return new Date(
                  point.timestamp,
                ).toLocaleDateString(
                  "en-IN",
                  {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                  },
                );
              }

              return "";
            }}
            formatter={(value) => [
              `₹${Number(
                value,
              ).toLocaleString(
                "en-IN",
                {
                  maximumFractionDigits: 2,
                },
              )}`,
              "Price",
            ]}
          />

          <Line
            type="monotone"
            dataKey="price"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
