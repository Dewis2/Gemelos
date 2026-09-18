import { createContext, type ReactNode, useContext } from "react";
import { DigitalTwinApplication } from "../application/DigitalTwinApplication";
import { FetchDigitalTwinGateway } from "../infrastructure/http/FetchDigitalTwinGateway";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
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
