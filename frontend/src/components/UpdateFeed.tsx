import { Link } from "react-router-dom";

import { useUpdates } from "../hooks/useUpdates";


interface Props {
  symbol?: string;
}


function formatTime(
  value: string,
) {
  return new Date(value).toLocaleString(
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

    case "BOARD_MEETING":
      return "🏢";

    case "BONUS":
      return "🎁";

    case "ACQUISITION":
      return "🤝";

    default:
      return "🔔";
  }
}


function priorityClass(
  priority: string,
) {
  switch (priority) {
    case "HIGH":
      return `
        bg-red-500/10
        text-red-400
      `;

    case "MEDIUM":
      return `
        bg-yellow-500/10
        text-yellow-400
      `;

    default:
      return `
        bg-slate-800
        text-slate-400
      `;
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

            {/* Event icon */}

            <div className="text-xl">
              {eventIcon(
                event.event_type
              )}
            </div>


            <div className="min-w-0 flex-1">

              {/* Symbol + Priority */}

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
                    hover:text-blue-300
                  "
                >
                  {event.symbol}
                </Link>


                <span
                  className={`
                    rounded
                    px-2
                    py-0.5
                    text-xs
                    ${priorityClass(
                      event.priority
                    )}
                  `}
                >
                  {event.priority}
                </span>


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


              {/* Title */}

              <h3
                className="
                  mt-1
                  font-medium
                  text-white
                "
              >
                {event.title}
              </h3>


              {/* Description */}

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


              {/* Source + Time */}

              <div
                className="
                  mt-2
                  flex
                  flex-wrap
                  items-center
                  gap-2
                  text-xs
                  text-slate-500
                "
              >

                <span>
                  {event.source ??
                    "StockSage AI"}
                </span>

                <span>•</span>

                <span>
                  {formatTime(
                    event.event_time
                  )}
                </span>

              </div>


              {/* Original source */}

              {event.source_url && (
                <a
                  href={event.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="
                    mt-2
                    inline-block
                    text-sm
                    text-blue-400
                    hover:text-blue-300
                  "
                >
                  View source →
                </a>
              )}

            </div>

          </div>

        </article>

      ))}

    </div>
  );
}
