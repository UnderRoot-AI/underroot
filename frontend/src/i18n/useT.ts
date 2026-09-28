import { useLanguageStore } from "../store/languageStore";
import en, { type TranslationKeys } from "./locales/en";
import hi from "./locales/hi";
import gu from "./locales/gu";
import mr from "./locales/mr";

const locales = { en, hi, gu, mr } as const;

/**
 * useT — returns a typed t(key) function.
 * Falls back to English if a key is missing in the active locale.
 *
 * Usage:
 *   const t = useT();
 *   <h1>{t("loginTitle")}</h1>
 */
export function useT(): (key: TranslationKeys) => string {
  const language = useLanguageStore((s) => s.language);
  const locale = locales[language] ?? en;
  return (key: TranslationKeys) => (locale as Record<TranslationKeys, string>)[key] ?? en[key];
}
