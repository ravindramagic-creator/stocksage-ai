import {
  BrowserRouter,
  Route,
  Routes,
} from "react-router-dom";

import { Dashboard } from "./pages/Dashboard";
import { StockDetail } from "./pages/StockDetail";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<Dashboard />}
        />

        <Route
          path="/stock/:symbol"
          element={<StockDetail />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
