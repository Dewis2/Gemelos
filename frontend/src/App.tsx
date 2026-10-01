import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { LoginPage, StatusPage } from "./presentation/pages/ProductPages";
import { ArchitecturePage } from "./presentation/pages/ArchitecturePage";
import { PredictionPage } from "./presentation/pages/PredictionPage";
import { ScenariosPage } from "./presentation/pages/ScenariosPage";
import { DemoPeruPage } from "./pages/DemoPeruPage";
import { DashboardPage } from "./presentation/pages/DashboardPage";
import { CorridorMapPage } from "./presentation/pages/CorridorMapPage";
import { HistoricalPage } from "./presentation/pages/HistoricalPage";
import { SourcesPage } from "./presentation/pages/SourcesPage";

export default function App() {
  return <BrowserRouter><Routes><Route path="/login" element={<LoginPage />} /><Route element={<Layout />}><Route index element={<DashboardPage />} /><Route path="mapa" element={<CorridorMapPage />} /><Route path="historico" element={<HistoricalPage />} /><Route path="prediccion" element={<PredictionPage />} /><Route path="escenarios" element={<ScenariosPage />} /><Route path="fuentes" element={<SourcesPage />} /><Route path="sistema" element={<ArchitecturePage />} /><Route path="estado" element={<StatusPage />} /><Route path="demo-peru" element={<DemoPeruPage />} /></Route></Routes></BrowserRouter>;
}
