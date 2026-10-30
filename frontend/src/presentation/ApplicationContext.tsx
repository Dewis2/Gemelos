import { createContext, type ReactNode, useContext } from "react";
import { DigitalTwinApplication } from "../application/DigitalTwinApplication";
import { FetchDigitalTwinGateway } from "../infrastructure/http/FetchDigitalTwinGateway";

// A hosted Vite build must target the deployed HTTPS backend, not localhost.
const configuredApiUrl = import.meta.env.VITE_API_URL?.trim().replace(/\/+$/, "");
const apiUrl = configuredApiUrl || (import.meta.env.DEV ? "http://localhost:8000" : "");
if (!apiUrl) {
  throw new Error("Falta VITE_API_URL: configura la URL HTTPS del backend en Staging.");
}
if (import.meta.env.PROD && !apiUrl.startsWith("https://")) {
  throw new Error("VITE_API_URL debe utilizar HTTPS en Staging.");
}
const defaultApplication = new DigitalTwinApplication(new FetchDigitalTwinGateway(apiUrl));
const ApplicationContext = createContext<DigitalTwinApplication | null>(null);

export function ApplicationProvider({ children, application = defaultApplication }: { children: ReactNode; application?: DigitalTwinApplication }) {
  return <ApplicationContext.Provider value={application}>{children}</ApplicationContext.Provider>;
}

export function useApplication(): DigitalTwinApplication {
  const application = useContext(ApplicationContext);
  if (!application) throw new Error("ApplicationProvider no está configurado.");
  return application;
}
