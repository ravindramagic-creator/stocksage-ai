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
    .filter((point) => point.close !== null)
    .map((point) => ({
      date: new Date(
        point.timestamp,
      ).toLocaleDateString(
        "en-IN",
        {
          day: "2-digit",
          month: "short",
        },
      ),

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
            tick={{ fontSize: 12 }}
          />

          <YAxis
            domain={["auto", "auto"]}
            tick={{ fontSize: 12 }}
          />

          <Tooltip
            formatter={(value) => [
              `₹${Number(value).toLocaleString(
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
