import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "../App";
import Home from "../pages/Home";
// import AnalysisPage from "../pages/AnalysisPage"; // 준비되면 추가

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Home />} />
          <Route path="analysis" element={<AnalysisPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
