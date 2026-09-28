import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Leaf, LockKeyhole, Mail } from "lucide-react";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import { authApi } from "../../services/auth.api";
import { developerApi } from "../../services/developer.api";
import { useAuthStore } from "../../store/authStore";
import { ROUTES } from "../../constants/routes";
import { getErrorMessage } from "../../utils/errorHandler";
import { useLanguageStore } from "../../store/languageStore";
import { useT } from "../../i18n/useT";

export default function Login() {
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const t = useT();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      // 1. Try admin/developer credentials first
      try {
        const devData = await developerApi.login(form.email, form.password);
        localStorage.setItem("developer_token", devData.access_token);
        localStorage.removeItem("access_token");
        navigate(ROUTES.DEVELOPER);
        return;
      } catch {
        // Not a developer — continue to normal user login below
      }

      // 2. Normal user login
      const data = await authApi.login(form);
      localStorage.setItem("access_token", data.access_token);
      if (data.user) {
        setUser(data.user);
        setLanguage((data.user.language || "en") as any);
      } else {
        setUser(await authApi.me());
      }
      if (data.user?.phone && !data.user.phone_verified) {
        navigate(ROUTES.VERIFY_PHONE);
      } else {
        navigate(ROUTES.DASHBOARD);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Invalid email or password"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="auth-brand"><Leaf /> {t("brand")}</div>
        <div>
          <h1>{t("loginTitle")}<br /><span>{t("loginSubtitle")}</span></h1>
        </div>
        <div className="auth-feature-grid">
          <div>{t("loginFeature1")}</div>
          <div>{t("loginFeature2")}</div>
          <div>{t("loginFeature3")}</div>
          <div>{t("loginFeature4")}</div>
        </div>
      </div>
      <div className="auth-form-wrap">
        <form className="auth-form" onSubmit={submit}>
          <div className="mobile-auth-logo"><Leaf /> {t("brand")}</div>
          <h2>{t("loginTitle")}</h2>
          <p>{t("loginSubtitle")}</p>
          <ErrorAlert message={error} />
          <label>
            {t("email")}
            <input
              type="email"
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              placeholder={t("emailPlaceholder")}
              required
            />
            <Mail />
          </label>
          <label>
            {t("password")}
            <input
              type="password"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder={t("passwordPlaceholder")}
              required
            />
            <LockKeyhole />
          </label>
          <Button type="submit" loading={loading}>{t("loginButton")}</Button>
          <p style={{ textAlign: "right", marginTop: 8, marginBottom: 0 }}>
            <Link to={ROUTES.FORGOT_PASSWORD} style={{ fontSize: 12, color: "var(--muted)" }}>
              {t("forgotPassword")}
            </Link>
          </p>
          <p className="auth-switch">
            {t("dontHaveAccount")} <Link to={ROUTES.SIGNUP}>{t("signUp")}</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
