import { useState } from "react";
import { ocrApi } from "../services/ocr.api";
import { getErrorMessage } from "../utils/errorHandler";

export function useOCR() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const process = async (reportId: number | string) => {
    setLoading(true);
    setError("");
    try {
      return await ocrApi.process(reportId);
    } catch (e) {
      const message = getErrorMessage(e);
      setError(message);
      throw e;
    } finally {
      setLoading(false);
    }
  };
  return { process, loading, error };
}
