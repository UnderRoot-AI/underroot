import { useCallback, useState } from "react";
import { soilApi } from "../services/soil.api";
import { useSoilStore } from "../store/soilStore";
import type { SoilTestPayload } from "../types/soil";
import { getErrorMessage } from "../utils/errorHandler";

export function useSoil() {
  const { currentTest, tests, setCurrentTest, setTests } = useSoilStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await soilApi.list();
      setTests(data);
      // Always update currentTest to the first (latest) result so the
      // assistant and other pages never hold a stale reference to an older test.
      if (data.length > 0) setCurrentTest(data[0]);
      return data;
    } catch (e) {
      setError(getErrorMessage(e));
      return [];
    } finally {
      setLoading(false);
    }
  }, [setCurrentTest, setTests]);

  const create = async (payload: SoilTestPayload) => {
    setLoading(true);
    setError("");
    try {
      const data = await soilApi.create(payload);
      setCurrentTest(data);
      setTests([data, ...tests]);
      return data;
    } catch (e) {
      setError(getErrorMessage(e));
      throw e;
    } finally {
      setLoading(false);
    }
  };

  return { currentTest, tests, loading, error, load, create, setCurrentTest };
}
