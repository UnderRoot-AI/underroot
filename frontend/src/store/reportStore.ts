import { create } from "zustand";
import type { SoilReport } from "../types/report";

interface ReportState {
  currentReport: SoilReport | null;
  setCurrentReport: (report: SoilReport | null) => void;
}

export const useReportStore = create<ReportState>((set) => ({
  currentReport: null,
  setCurrentReport: (currentReport) => set({ currentReport })
}));
