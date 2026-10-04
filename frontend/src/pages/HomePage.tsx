import { BestStocksScreener } from "../components/BestStocksScreener";
import { Dashboard } from "./Dashboard";

export function HomePage() {
  return (
    <>
      <Dashboard />
      <div className="bg-slate-950">
        <div className="mx-auto max-w-7xl px-6 pb-8">
          <BestStocksScreener />
        </div>
      </div>
    </>
  );
}
