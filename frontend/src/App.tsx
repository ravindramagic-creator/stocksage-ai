import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import { Dashboard } from "./pages/Dashboard";
import { StockPage } from "./pages/StockPage";


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
          element={<StockPage />}
        />

      </Routes>

    </BrowserRouter>
  );
}


export default App;
