interface Props {
  value: string;
  onChange: (
    period: string,
    interval: string,
  ) => void;
}

const ranges = [
  {
    label: "1D",
    period: "1d",
    interval: "5m",
  },
  {
    label: "5D",
    period: "5d",
    interval: "15m",
  },
  {
    label: "1M",
    period: "1mo",
    interval: "1d",
  },
  {
    label: "3M",
    period: "3mo",
    interval: "1d",
  },
  {
    label: "6M",
    period: "6mo",
    interval: "1d",
  },
  {
    label: "1Y",
    period: "1y",
    interval: "1d",
  },
];

export function ChartRangeSelector({
  value,
  onChange,
}: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {ranges.map((range) => (
        <button
          key={range.label}
          onClick={() =>
            onChange(
              range.period,
              range.interval,
            )
          }
          className={`
            rounded-lg
            px-3 py-1.5
            text-sm
            ${
              value === range.period
                ? "bg-blue-600 text-white"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700"
            }
          `}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
}
