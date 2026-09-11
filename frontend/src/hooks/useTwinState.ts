import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { DigitalTwinState } from "../types/api";

export function useTwinState() {
  const [data, setData] = useState<DigitalTwinState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.twinState().then(setData).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Error desconocido");
    });
  }, []);
  return { data, error };
}

