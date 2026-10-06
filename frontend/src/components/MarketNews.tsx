import { useMarketNews } from "../hooks/useMarketNews";

function formatTime(value: string) {
  return new Date(value).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function importanceClass(value: string) {
  if (value === "HIGH") return "bg-red-500/10 text-red-400";
  if (value === "MEDIUM") return "bg-yellow-500/10 text-yellow-400";
  return "bg-slate-800 text-slate-400";
}

export function MarketNews() {
  const { data, isLoading, isError } = useMarketNews(12);

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-white">Important Market News</h2>
          <p className="mt-1 text-sm text-slate-500">India-focused market, macro, corporate and commodity headlines</p>
        </div>
        <div className="text-xs text-slate-500">Auto-refreshes every 5 minutes</div>
      </div>

      {isLoading && <div className="text-sm text-slate-400">Loading market news...</div>}
      {isError && <div className="text-sm text-red-400">Market news is temporarily unavailable.</div>}

      {!isLoading && !isError && data?.length === 0 && (
        <div className="rounded-lg border border-slate-800 bg-slate-950 p-5 text-center text-sm text-slate-500">
          No recent market headlines found.
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2">
        {(data ?? []).map((item) => (
          <a
            key={`${item.url}-${item.published_at}`}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-lg border border-slate-800 bg-slate-950/60 p-4 transition hover:border-slate-700 hover:bg-slate-950"
          >
            <div className="flex items-start gap-3">
              <div className="min-w-0 flex-1">
                <div className="mb-2 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-wide">
                  <span className="text-cyan-400">{item.category}</span>
                  <span className={`rounded px-2 py-0.5 ${importanceClass(item.importance)}`}>
                    {item.importance}
                  </span>
                </div>
                <h3 className="font-medium leading-6 text-white group-hover:text-cyan-300">
                  {item.title}
                </h3>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span>{item.source}</span>
                  <span>•</span>
                  <span>{formatTime(item.published_at)}</span>
                </div>
              </div>
              <div className="text-slate-600 group-hover:text-cyan-400">↗</div>
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}