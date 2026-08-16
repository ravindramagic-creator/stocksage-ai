import { useParams, Link } from "react-router-dom";
import { useState } from "react";

import { FinancialResultCard } from "../components/FinancialResultCard";
import { UpdateFeed } from "../components/UpdateFeed";
import { PriceChart } from "../components/PriceChart";


type StockTab =
  | "overview"
  | "news"
  | "dividend"
  | "split";


export function StockPage() {

  const { symbol } = useParams<{
    symbol: string;
  }>();

  const [
    activeTab,
    setActiveTab,
  ] = useState<StockTab>("overview");


  const stockSymbol =
    symbol?.toUpperCase() ?? "";


  if (!stockSymbol) {

    return (
      <main
        className="
          min-h-screen
          bg-slate-950
          p-8
          text-white
        "
      >
        Invalid stock symbol.
      </main>
    );
  }


  return (
    <main
      className="
        min-h-screen
        bg-slate-950
      "
    >

      <div
        className="
          mx-auto
          max-w-6xl
          px-6
          py-8
        "
      >

        {/* Back */}

        <Link
          to="/"
          className="
            text-sm
            text-slate-400
            hover:text-white
          "
        >
          ← Back to Dashboard
        </Link>


        {/* Stock Header */}

        <section className="mt-6">

          <h1
            className="
              text-3xl
              font-bold
              text-white
            "
          >
            {stockSymbol}
          </h1>

          <p
            className="
              mt-1
              text-slate-400
            "
          >
            Stock details and market updates
          </p>

        
        </section>
        {/* Stock Price Chart */}

         <section className="mt-6">

           <PriceChart
             symbol={stockSymbol}
             period="1mo"
             interval="1d"
            />

         </section>

        {/* Tabs */}

        <div
          className="
            mt-8
            border-b
            border-slate-800
          "
        >

          <div
            className="
              flex
              gap-6
              overflow-x-auto
            "
          >

            <Tab
              label="Overview"
              active={
                activeTab === "overview"
              }
              onClick={() =>
                setActiveTab("overview")
              }
            />

            <Tab
              label="News"
              active={
                activeTab === "news"
              }
              onClick={() =>
                setActiveTab("news")
              }
            />

            <Tab
              label="Dividend"
              active={
                activeTab === "dividend"
              }
              onClick={() =>
                setActiveTab("dividend")
              }
            />

            <Tab
              label="Stock Split"
              active={
                activeTab === "split"
              }
              onClick={() =>
                setActiveTab("split")
              }
            />

          </div>

        </div>


        {/* Tab Content */}

        <section className="mt-8">

          {activeTab === "overview" && (

            <div className="space-y-8">

              {/* Financial Results */}

              <div>

                <h2
                  className="
                    mb-4
                    text-xl
                    font-semibold
                    text-white
                  "
                >
                  Financial Results
                </h2>

                <FinancialResultCard
                  symbol={stockSymbol}
                />

              </div>


              {/* Recent Updates */}

              <div>

                <h2
                  className="
                    mb-4
                    text-xl
                    font-semibold
                    text-white
                  "
                >
                  Recent Updates
                </h2>

                <UpdateFeed
                  symbol={stockSymbol}
                />

              </div>

            </div>

          )}


          {activeTab === "news" && (

            <EventTab
              symbol={stockSymbol}
              eventType="NEWS"
              title="News"
            />

          )}


          {activeTab === "dividend" && (

            <EventTab
              symbol={stockSymbol}
              eventType="DIVIDEND"
              title="Dividend History"
            />

          )}


          {activeTab === "split" && (

            <EventTab
              symbol={stockSymbol}
              eventType="SPLIT"
              title="Stock Split History"
            />

          )}

        </section>

      </div>

    </main>
  );
}


/* ------------------------------------------ */
/* Tab                                      */
/* ------------------------------------------ */

interface TabProps {

  label: string;

  active: boolean;

  onClick: () => void;
}


function Tab({
  label,
  active,
  onClick,
}: TabProps) {

  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        border-b-2
        px-1
        pb-3
        text-sm
        font-medium
        transition
        ${
          active
            ? "border-blue-500 text-white"
            : "border-transparent text-slate-500 hover:text-slate-300"
        }
      `}
    >
      {label}
    </button>
  );
}


/* ------------------------------------------ */
/* Event Tab                                */
/* ------------------------------------------ */

interface EventTabProps {

  symbol: string;

  eventType:
    | "NEWS"
    | "DIVIDEND"
    | "SPLIT";

  title: string;
}


function EventTab({
  symbol,
  eventType,
  title,
}: EventTabProps) {

  return (
    <div>

      <h2
        className="
          mb-4
          text-xl
          font-semibold
          text-white
        "
      >
        {title}
      </h2>

      <UpdateFeed
        symbol={symbol}
        eventType={eventType}
      />

    </div>
  );
}
