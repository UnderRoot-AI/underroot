import { Bell, Menu, Search } from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { useLanguageStore, type Language } from "../../store/languageStore";
import { updateProfile } from "../../services/auth.api";
import { useT } from "../../i18n/useT";

export default function Header({ onMenu }: { onMenu?: () => void }) {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const language = useLanguageStore((s) => s.language);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const t = useT();

  async function changeLanguage(next: Language) {
    setLanguage(next);
    if (user) {
      try {
        const updated = await updateProfile({ language: next });
        setUser(updated);
      } catch { /* local language still works */ }
    }
  }

  return (
    <header className="header">
      <button className="mobile-menu" onClick={onMenu}><Menu size={22} /></button>
      <div className="header-search">
        <Search size={18} />
        <input placeholder={t("searchPlaceholder")} />
      </div>
      <div className="header-actions">
        <select
          aria-label={t("selectLanguage")}
          className="language-select"
          value={language}
          onChange={e => changeLanguage(e.target.value as Language)}
        >
          <option value="en">English</option>
          <option value="hi">हिन्दी</option>
          <option value="gu">ગુજરાતી</option>
          <option value="mr">मराठी</option>
        </select>
        <button className="icon-btn" aria-label="Notifications"><Bell size={19} /></button>
        <div className="header-user">
          <div className="avatar">{user?.name?.charAt(0)?.toUpperCase() || "U"}</div>
          <span>{user?.name || "Farmer"}</span>
        </div>
      </div>
    </header>
  );
}
