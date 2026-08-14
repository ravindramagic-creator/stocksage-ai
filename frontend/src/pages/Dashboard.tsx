import { useState } from "react";

import { MarketSummary } from "../components/MarketSummary";
import { MarketSearchResults } from "../components/MarketSearchResults";
import { SearchBar } from "../components/SearchBar";
import { Subscriptions } from "../components/Subscriptions";

import { useMarketSearch } from "../hooks/useMarketSearch";


export function Dashboard() {

  const [
    searchQuery,
    setSearchQuery,
  ] = useState("");


  const {
    data,
    isLoading,
    isError,
  } = useMarketSearch(
    searchQuery,
  );


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

        <header className="mb-8">

          <h1
            className="
              text-3xl
              font-bold
              text-white
            "
          >
            StockSage AI
          </h1>

          <p
            className="
              mt-1
              text-slate-400
            "
          >
            Track the stocks
            that matter to you.
          </p>

        </header>


        <section className="mb-8">

          <div className="mb-4">

            <h2
              className="
                text-xl
                font-semibold
                text-white
              "
            >
              Indian Market
            </h2>

          </div>

          <MarketSummary />

        </section>


        <section className="mb-8">

          <div className="mb-4">

            <h2
              className="
                text-xl
                font-semibold
                text-white
              "
            >
              Find a Stock
            </h2>

            <p
              className="
                text-sm
                text-slate-500
              "
            >
              Search NSE stocks
              by company or symbol.
            </p>

          </div>


          <SearchBar
            onSearch={
              setSearchQuery
            }
          />


          {searchQuery && (

            <div className="mt-4">

              {isLoading && (

                <div
                  className="
                    text-slate-400
                  "
                >
                  Searching...
                </div>

              )}


              {isError && (

                <div
                  className="
                    text-red-400
                  "
                >
                  Unable to search
                  stocks right now.
                </div>

              )}


              {!isLoading &&
                !isError &&
                data && (

                  <MarketSearchResults
                    results={
                      data.results
                    }
                  />

                )}

            </div>

          )}

        </section>


        <section>

          <div className="mb-4">

            <h2
              className="
                text-xl
                font-semibold
                text-white
              "
            >
              My Subscriptions
            </h2>

            <p
              className="
                text-sm
                text-slate-500
              "
            >
              Stocks you'll receive
              updates about.
            </p>

          </div>


          <Subscriptions />

        </section>

      </div>

    </main>
  );
}
