import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import AnalysisPage from "../pages/AnalysisPage";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analysis" element={<AnalysisPage />} />
      </Routes>
    </BrowserRouter>
  );
}
