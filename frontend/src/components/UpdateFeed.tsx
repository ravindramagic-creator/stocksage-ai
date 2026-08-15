import { Link } from "react-router-dom";

import { useUpdates } from "../hooks/useUpdates";


interface Props {
  symbol?: string;
}


function formatTime(
  value: string,
) {

  return new Date(value)
    .toLocaleString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      },
    );
}


function eventIcon(
  eventType: string,
) {

  switch (eventType) {

    case "PRICE_MOVE":
      return "📈";

    case "NEWS":
      return "📰";

    case "DIVIDEND":
      return "💰";

    case "SPLIT":
      return "🔀";

    case "RESULT":
      return "📊";

    case "ORDER":
      return "📦";

    default:
      return "🔔";
  }
}


export function UpdateFeed({
  symbol,
}: Props) {

  const {
    data,
    isLoading,
    isError,
  } = useUpdates(symbol);


  if (isLoading) {

    return (
      <div className="text-slate-400">
        Loading updates...
      </div>
    );
  }


  if (isError) {

    return (
      <div className="text-red-400">
        Unable to load updates.
      </div>
    );
  }


  if (!data?.length) {

    return (
      <div
        className="
          rounded-xl
          border border-slate-800
          bg-slate-900
          p-6
          text-center
          text-slate-400
        "
      >
        No updates yet.
      </div>
    );
  }


  return (
    <div className="space-y-3">

      {data.map((event) => (

        <article
          key={event.id}
          className="
            rounded-xl
            border
            border-slate-800
            bg-slate-900
            p-4
          "
        >

          <div
            className="
              flex
              items-start
              gap-3
            "
          >

            <div className="text-xl">
              {eventIcon(
                event.event_type
              )}
            </div>


            <div className="min-w-0 flex-1">

              <div
                className="
                  flex
                  flex-wrap
                  items-center
                  gap-2
                "
              >

                <Link
                  to={`/stock/${event.symbol}`}
                  className="
                    font-semibold
                    text-blue-400
                  "
                >
                  {event.symbol}
                </Link>

                <span
                  className="
                    rounded
                    bg-slate-800
                    px-2
                    py-0.5
                    text-xs
                    text-slate-400
                  "
                >
                  {event.event_type}
                </span>

              </div>


              <h3
                className="
                  mt-1
                  font-medium
                  text-white
                "
              >
                {event.title}
              </h3>


              {event.description && (

                <p
                  className="
                    mt-1
                    text-sm
                    text-slate-400
                  "
                >
                  {event.description}
                </p>

              )}


              <div
                className="
                  mt-2
                  text-xs
                  text-slate-500
                "
              >
                {event.source ?? "StockSage AI"}
                {" • "}
                {formatTime(
                  event.event_time
                )}
              </div>

            </div>

          </div>

        </article>

      ))}

    </div>
  );
}
