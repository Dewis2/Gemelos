import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { ApplicationProvider } from "./presentation/ApplicationContext";
import "./styles.css";
import "leaflet/dist/leaflet.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ApplicationProvider>
      <App />
    </ApplicationProvider>
  </StrictMode>,
);
