import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import { Dashboard } from "./pages/Dashboard";
import { StockPage } from "./pages/StockPage";
import { AutoSalesPage } from "./pages/AutoSalesPage";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/stock/:symbol" element={<StockPage />} />
        <Route path="/auto-sales" element={<AutoSalesPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
