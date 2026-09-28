import { useState } from "react";
import { reportApi } from "../services/report.api";
import { uploadApi } from "../services/upload.api";
import { useReportStore } from "../store/reportStore";
import { getErrorMessage } from "../utils/errorHandler";

export function useReport() {
  const { currentReport, setCurrentReport } = useReportStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const upload = async (file: File) => {
    setLoading(true);
    setError("");
    try {
      const data = await uploadApi.report(file);
      setCurrentReport(data);
      return data;
    } catch (e) {
      setError(getErrorMessage(e));
      throw e;
    } finally {
      setLoading(false);
    }
  };

  const generate = async (soilTestId: number | string) => {
    setLoading(true);
    try {
      const data = await reportApi.generate(soilTestId);
      setCurrentReport(data);
      return data;
    } catch (e) {
      setError(getErrorMessage(e));
      throw e;
    } finally {
      setLoading(false);
    }
  };

  return { currentReport, loading, error, upload, generate };
}
