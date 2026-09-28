import { create } from "zustand";
import type { SoilTest } from "../types/soil";

interface SoilState {
  currentTest: SoilTest | null;
  tests: SoilTest[];
  setCurrentTest: (test: SoilTest | null) => void;
  setTests: (tests: SoilTest[]) => void;
}

export const useSoilStore = create<SoilState>((set) => ({
  currentTest: null,
  tests: [],
  setCurrentTest: (currentTest) => set({ currentTest }),
  setTests: (tests) => set({ tests })
}));
