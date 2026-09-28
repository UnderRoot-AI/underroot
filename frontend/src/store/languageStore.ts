import { create } from "zustand";
import { persist } from "zustand/middleware";
import en from "../i18n/locales/en";
import hi from "../i18n/locales/hi";
import gu from "../i18n/locales/gu";
import mr from "../i18n/locales/mr";

export type Language = "en" | "hi" | "gu" | "mr";

// Keep the old flat-dict for backward compat with any remaining translate() calls
const translations: Record<Language, Record<string, string>> = { en, hi, gu, mr };

/** Legacy helper — prefer useT() for new code */
export function translate(language: Language, key: string): string {
  return (translations[language] as Record<string, string>)[key]
    ?? (translations.en as Record<string, string>)[key]
    ?? key;
}

interface LanguageStore {
  language: Language;
  setLanguage: (language: Language) => void;
}

export const useLanguageStore = create<LanguageStore>()(
  persist(
    (set) => ({
      language: "en",
      setLanguage: (language) => set({ language }),
    }),
    { name: "smart-soil-language" }
  )
);
