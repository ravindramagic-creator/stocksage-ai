import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useHistory } from "../hooks/useHistory";

interface Props {
  symbol: string;
}

type IndicatorPoint = {
  timestamp: string;
  close: number;
  volume: number;
  rsi: number | null;
};

function ema(values: number[], period: number): number[] {
  if (values.length === 0) return [];
  const multiplier = 2 / (period + 1);
  const result = Array<number>(values.length).fill(NaN);
  if (values.length < period) return result;

  let seed = 0;
  for (let i = 0; i < period; i += 1) seed += values[i];
  result[period - 1] = seed / period;

  for (let i = period; i < values.length; i += 1) {
    result[i] =
      (values[i] - result[i - 1]) * multiplier + result[i - 1];
  }
  return result;
}

function sma(values: number[], period: number): number[] {
  const result = Array<number>(values.length).fill(NaN);
  if (values.length < period) return result;
  let sum = 0;
  for (let i = 0; i < values.length; i += 1) {
    sum += values[i];
    if (i >= period) sum -= values[i - period];
    if (i >= period - 1) result[i] = sum / period;
  }
  return result;
}

function rsi(values: number[], period = 14): number[] {
  const result = Array<number>(values.length).fill(NaN);
  if (values.length <= period) return result;

  let gains = 0;
  let losses = 0;
  for (let i = 1; i <= period; i += 1) {
    const change = values[i] - values[i - 1];
    if (change >= 0) gains += change;
    else losses -= change;
  }

  let avgGain = gains / period;
  let avgLoss = losses / period;
  result[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);

  for (let i = period + 1; i < values.length; i += 1) {
    const change = values[i] - values[i - 1];
    const gain = Math.max(change, 0);
    const loss = Math.max(-change, 0);
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    result[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return result;
}

function formatValue(value: number | null, suffix = "") {
  if (value === null || !Number.isFinite(value)) return "—";
  return `${value.toFixed(2)}${suffix}`;
}

function rsiLabel(value: number | null) {
  if (value === null) return "Insufficient data";
  if (value >= 70) return "Overbought zone";
  if (value <= 30) return "Oversold zone";
  if (value >= 60) return "Strong momentum";
  if (value < 40) return "Weak momentum";
  return "Neutral momentum";
}

export function TechnicalIndicators({ symbol }: Props) {
  const { data, isLoading, isError } = useHistory(symbol, "1y", "1d");

  if (isLoading) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-400">Loading technical indicators...</div>;
  }

  if (isError || !data) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-red-400">Unable to load technical indicators.</div>;
  }

  const points = data.points
    .filter((point) => point.close !== null)
    .map((point) => ({
      timestamp: point.timestamp,
      close: Number(point.close),
      volume: Number(point.volume ?? 0),
    }));

  if (points.length < 30) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-400">Not enough daily price history to calculate technical indicators.</div>;
  }

  const closes = points.map((point) => point.close);
  const volumes = points.map((point) => point.volume);
  const rsiValues = rsi(closes, 14);
  const sma20 = sma(closes, 20);
  const sma50 = sma(closes, 50);
  const sma200 = sma(closes, 200);
  const ema12 = ema(closes, 12);
  const ema26 = ema(closes, 26);
  const macd = closes.map((_, i) =>
    Number.isFinite(ema12[i]) && Number.isFinite(ema26[i]) ? ema12[i] - ema26[i] : NaN,
  );
  const macdSignal = ema(macd.filter(Number.isFinite), 9);
  const last = closes.length - 1;
  const current = closes[last];
  const currentRsi = Number.isFinite(rsiValues[last]) ? rsiValues[last] : null;
  const currentSma20 = sma20[last];
  const currentSma50 = sma50[last];
  const currentSma200 = sma200[last];
  const currentMacd = macd[last];
  const signalIndex = macd.filter(Number.isFinite).length - 1;
  const currentSignal = signalIndex >= 0 ? macdSignal[signalIndex] : NaN;
  const avgVolume20 = volumes.slice(-20).reduce((sum, value) => sum + value, 0) / 20;
  const volumeRatio = avgVolume20 > 0 ? volumes[last] / avgVolume20 : NaN;

  const recent = closes.slice(-20);
  const support = Math.min(...recent);
  const resistance = Math.max(...recent);

  const chartData: IndicatorPoint[] = points.map((point, index) => ({
    ...point,
    rsi: Number.isFinite(rsiValues[index]) ? rsiValues[index] : null,
  })).slice(-120);

  const trend = Number.isFinite(currentSma200)
    ? current > currentSma200 ? "Above 200-DMA" : "Below 200-DMA"
    : Number.isFinite(currentSma50)
      ? current > currentSma50 ? "Above 50-DMA" : "Below 50-DMA"
      : "Trend unavailable";

  const macdState = Number.isFinite(currentMacd) && Number.isFinite(currentSignal)
    ? currentMacd > currentSignal ? "Bullish MACD momentum" : "Bearish MACD momentum"
    : "MACD unavailable";

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-white">Technical Analysis</h2>
          <p className="mt-1 text-sm text-slate-400">Daily data · RSI(14), moving averages, MACD and volume</p>
        </div>
        <div className="text-right">
          <div className="text-xs uppercase tracking-wide text-slate-500">Trend</div>
          <div className="text-sm font-medium text-slate-200">{trend}</div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <IndicatorCard title="RSI (14)" value={formatValue(currentRsi)} detail={rsiLabel(currentRsi)} />
        <IndicatorCard title="MACD" value={formatValue(currentMacd)} detail={macdState} />
        <IndicatorCard title="Volume vs 20D Avg" value={formatValue(volumeRatio, "x")} detail="Current / average volume" />
        <IndicatorCard title="20D Support" value={`₹${support.toFixed(2)}`} detail={`Resistance ₹${resistance.toFixed(2)}`} />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <MovingAverage title="20-DMA" value={currentSma20} price={current} />
        <MovingAverage title="50-DMA" value={currentSma50} price={current} />
        <MovingAverage title="200-DMA" value={currentSma200} price={current} />
      </div>

      <div className="mt-6 h-64 w-full">
        <div className="mb-2 text-sm font-medium text-slate-300">RSI(14) — last 120 trading sessions</div>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.12} />
            <XAxis dataKey="timestamp" hide />
            <YAxis domain={[0, 100]} ticks={[0, 30, 50, 70, 100]} tick={{ fontSize: 11 }} />
            <ReferenceLine y={70} strokeDasharray="4 4" strokeOpacity={0.4} />
            <ReferenceLine y={30} strokeDasharray="4 4" strokeOpacity={0.4} />
            <Tooltip
              labelFormatter={(label: unknown) => {
                if (typeof label !== "string" && typeof label !== "number") return "";
                return new Date(label).toLocaleDateString("en-IN", {
                  day: "2-digit",
                  month: "short",
                  year: "numeric",
                });
              }}
              formatter={(value) => [formatValue(Number(value)), "RSI"]}
            />
            <Line type="monotone" dataKey="rsi" dot={false} connectNulls={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/50 p-3 text-xs text-slate-400">
        RSI above 70 indicates strong recent momentum and an overbought zone; below 30 indicates weak recent momentum and an oversold zone. These are indicators, not standalone buy/sell signals.
      </div>
    </section>
  );
}

function IndicatorCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{title}</div>
      <div className="mt-2 text-xl font-semibold text-white">{value}</div>
      <div className="mt-1 text-xs text-slate-400">{detail}</div>
    </div>
  );
}

function MovingAverage({ title, value, price }: { title: string; value: number; price: number }) {
  const available = Number.isFinite(value);
  const relation = available ? (price >= value ? "Price above" : "Price below") : "Insufficient history";
  return (
    <div className="rounded-xl border border-slate-800 p-4">
      <div className="text-sm text-slate-400">{title}</div>
      <div className="mt-1 text-lg font-semibold text-white">{available ? `₹${value.toFixed(2)}` : "—"}</div>
      <div className="mt-1 text-xs text-slate-500">{relation}</div>
    </div>
  );
}
