import { NavLink } from "react-router-dom";
import { Bot, ClipboardList, FileText, History, Home, Leaf, Sprout, UserRound, Landmark, BarChart3 } from "lucide-react";
import { ROUTES } from "../../constants/routes";
import { useAuthStore } from "../../store/authStore";
import { useT } from "../../i18n/useT";

export default function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const t = useT();

  const links = [
    { to: ROUTES.DASHBOARD, label: t("navDashboard"), icon: Home },
    { to: ROUTES.SOIL_TEST, label: t("navNewTest"), icon: ClipboardList },
    { to: ROUTES.SOIL_ANALYZER, label: t("soilAnalyzerTitle"), icon: BarChart3 },
    { to: ROUTES.REPORT, label: t("soilReportTitle"), icon: FileText },
    { to: ROUTES.HISTORY, label: t("navHistory"), icon: History },
    { to: ROUTES.COMPARE, label: t("navCompare"), icon: History },
    { to: ROUTES.CROPS, label: t("navCropRec"), icon: Sprout },
    { to: ROUTES.FERTILIZER, label: t("navFertRec"), icon: Leaf },
    { to: ROUTES.ASSISTANT, label: t("navAssistant"), icon: Bot },
    { to: ROUTES.RESOURCES, label: t("navResources"), icon: Landmark },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Leaf size={21} /></div>
        <div>
          <strong>{t("brand")}</strong>
          <span>{t("tagline")}</span>
        </div>
      </div>
      <nav className="side-nav">
        <p className="nav-label">MAIN</p>
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            <Icon size={18} /><span>{label}</span>
          </NavLink>
        ))}
        <p className="nav-label">ACCOUNT</p>
        <NavLink to={ROUTES.PROFILE} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          <UserRound size={18} /><span>{t("navProfile")}</span>
        </NavLink>
      </nav>
      <div className="sidebar-bottom">
        <div className="user-mini">
          <div className="avatar">{user?.name?.charAt(0)?.toUpperCase() || "U"}</div>
          <div>
            <strong>{user?.name || "Farmer"}</strong>
            <small>{user?.email || ""}</small>
          </div>
        </div>
      </div>
    </aside>
  );
}
