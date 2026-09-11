import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ComparisonPage, Dashboard, LoginPage, MapPage, PredictionPage, ScenariosPage, SourcesPage, StatusPage } from "./pages/Pages";

export default function App() {
  return <BrowserRouter><Routes><Route path="/login" element={<LoginPage />} /><Route element={<Layout />}><Route index element={<Dashboard />} /><Route path="mapa" element={<MapPage />} /><Route path="prediccion" element={<PredictionPage />} /><Route path="escenarios" element={<ScenariosPage />} /><Route path="comparacion" element={<ComparisonPage />} /><Route path="fuentes" element={<SourcesPage />} /><Route path="estado" element={<StatusPage />} /></Route></Routes></BrowserRouter>;
}

