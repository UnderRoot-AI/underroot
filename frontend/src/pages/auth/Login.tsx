import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { LockKeyhole, Mail, RefreshCw } from "lucide-react";
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
  // When true: the error is specifically because of an unverified email
  const [showResend, setShowResend] = useState(false);
  const [resending, setResending] = useState(false);
  const [resendDone, setResendDone] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setShowResend(false);
    setResendDone(false);
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
      // Phone verification is not part of the login flow.
      navigate(ROUTES.DASHBOARD);
    } catch (err: any) {
      const detail: string = err?.response?.data?.detail ?? "";
      if (detail.toLowerCase().includes("verify your email")) {
        setError("Please verify your email address before signing in. Check your inbox for the verification link.");
        setShowResend(true);  // show resend button so the user can get a new link
      } else {
        setError(getErrorMessage(err, "Invalid email or password"));
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    if (!form.email || resending) return;
    setResending(true);
    setResendDone(false);
    try {
      await authApi.resendVerificationByEmail(form.email);
      setResendDone(true);
    } catch {
      // Endpoint always returns 200; silently ignore network errors
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="auth-brand">
          <img
            src="/underroot-logo.png"
            alt="UnderRoot"
            style={{ width: 120, height: "auto", maxWidth: "100%", display: "block" }}
          />
        </div>
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
          <div className="mobile-auth-logo">
            <img
              src="/underroot-logo.png"
              alt="UnderRoot"
              style={{ width: 96, height: "auto", maxWidth: "100%", display: "block" }}
            />
          </div>
          <h2>{t("loginTitle")}</h2>
          <p>{t("loginSubtitle")}</p>
          <ErrorAlert message={error} />

          {/* Resend verification — shown only when blocked due to unverified email */}
          {showResend && !resendDone && (
            <div style={{
              background: "var(--surface, #f7f8fa)",
              border: "1px solid var(--border, #e5e7eb)",
              borderRadius: 10,
              padding: "12px 16px",
              marginBottom: 14,
              fontSize: 13,
            }}>
              <p style={{ margin: "0 0 10px", color: "var(--text, #1f2328)" }}>
                Need a new verification link?
              </p>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleResend}
                disabled={resending || !form.email}
                style={{ fontSize: 13, display: "inline-flex", alignItems: "center", gap: 6 }}
              >
                <RefreshCw size={13} />
                {resending ? "Sending…" : "Resend verification email"}
              </button>
            </div>
          )}

          {resendDone && (
            <div className="alert alert-success" style={{ marginBottom: 14, fontSize: 13 }}>
              ✓ Verification email sent. Check your inbox and spam folder.
            </div>
          )}

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
