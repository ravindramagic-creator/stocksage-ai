import { useState } from "react";

import { SearchBar } from "../components/SearchBar";
import { StockSearchResults } from "../components/StockSearchResults";
import { Watchlist } from "../components/Watchlist";
import { useStockSearch } from "../hooks/useStocks";

export function Dashboard() {
  const [searchQuery, setSearchQuery] =
    useState("");

  const {
    data: searchResults,
    isLoading: searchLoading,
  } = useStockSearch(searchQuery);

  return (
    <main className="min-h-screen bg-slate-950">
      <div className="mx-auto max-w-6xl px-6 py-8">

        <header className="mb-8">
          <h1 className="text-3xl font-bold text-white">
            StockSage AI
          </h1>

          <p className="mt-1 text-slate-400">
            Your personal stock intelligence dashboard
          </p>
        </header>

        <section className="mb-8">
          <SearchBar
            onSearch={setSearchQuery}
          />

          {searchQuery && (
            <div className="mt-4">
              {searchLoading ? (
                <div className="text-slate-400">
                  Searching...
                </div>
              ) : (
                <StockSearchResults
                  stocks={searchResults ?? []}
                />
              )}
            </div>
          )}
        </section>

        <section>
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-white">
              My Watchlist
            </h2>

            <p className="text-sm text-slate-500">
              Stocks you're following
            </p>
          </div>

          <Watchlist />
        </section>

      </div>
    </main>
  );
}
