import { useState, useRef, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Leaf, LockKeyhole, Mail, UserRound, Phone, CheckCircle, RefreshCw, Loader2 } from "lucide-react";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import { authApi } from "../../services/auth.api";
import { useAuthStore } from "../../store/authStore";
import { useLanguageStore } from "../../store/languageStore";
import { ROUTES } from "../../constants/routes";
import { getErrorMessage } from "../../utils/errorHandler";
import { useT } from "../../i18n/useT";

export default function Signup() {
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const t = useT();

  const [form, setForm] = useState({
    name: "", email: "", password: "", phone: "",
    state: "", district: "", city_village: "", language: "en",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  // verification_url is only present in dev when SMTP is not configured
  const [verificationUrl, setVerificationUrl] = useState("");
  // emailSent: SMTP is configured — email was dispatched, no raw URL returned
  const [emailSent, setEmailSent] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState("");

  // Resend state (shown on the emailSent screen)
  const RESEND_COOLDOWN = 60;
  const [resending, setResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [resendError, setResendError] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const cooldownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function startCooldown() {
    setCooldown(RESEND_COOLDOWN);
    cooldownRef.current = setInterval(() => {
      setCooldown(prev => {
        if (prev <= 1) { clearInterval(cooldownRef.current!); return 0; }
        return prev - 1;
      });
    }, 1000);
  }

  async function handleResend() {
    if (cooldown > 0 || resending) return;
    setResending(true);
    setResendError("");
    setResendSuccess(false);
    try {
      await authApi.resendVerification();
      setResendSuccess(true);
      startCooldown();
    } catch (err) {
      setResendError(getErrorMessage(err, "Failed to resend. Please try again."));
    } finally {
      setResending(false);
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await authApi.signup(form);
      localStorage.setItem("access_token", data.access_token);
      setUser(data.user);
      setLanguage((data.user.language || "en") as any);
      setRegisteredEmail(form.email);

      if (form.phone) {
        navigate(ROUTES.VERIFY_PHONE);
      } else if (data.verification_url) {
        // Dev mode: SMTP not configured, raw URL returned for convenience
        setVerificationUrl(data.verification_url);
      } else if (data.verification_required) {
        // Production mode: email was sent via SMTP, show check-inbox state
        setEmailSent(true);
      } else {
        navigate(ROUTES.DASHBOARD);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Signup failed"));
    } finally {
      setLoading(false);
    }
  }

  // Production: email dispatched via SMTP — show check-inbox screen, block dashboard access
  if (emailSent) {
    return (
      <div className="auth-page">
        <div className="auth-visual">
          <div className="auth-brand"><Leaf /> {t("brand")}</div>
          <div>
            <h1>{t("verifyEmailTitle")}<br /><span>{t("verifyEmailSubtitle")}</span></h1>
            <p>{t("verifyEmailDesc")}</p>
          </div>
          <div className="auth-feature-grid">
            <div>{t("verifyEmailFeature1")}</div>
            <div>{t("verifyEmailFeature2")}</div>
            <div>{t("verifyEmailFeature3")}</div>
            <div>{t("verifyEmailFeature4")}</div>
          </div>
        </div>
        <div className="auth-form-wrap">
          <div className="auth-form" style={{ textAlign: "center" }}>
            <div className="mobile-auth-logo"><Leaf /> {t("brand")}</div>
            <div style={{ width: 72, height: 72, borderRadius: "50%", background: "var(--light)", color: "var(--green)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
              <CheckCircle size={40} />
            </div>
            <h2 style={{ marginBottom: 8 }}>Check your email</h2>
            <p style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.7, marginBottom: 16 }}>
              We sent a verification link to <strong>{registeredEmail}</strong>.
              Click the link to activate your account.
            </p>
            <div className="alert alert-success" style={{ textAlign: "left", marginBottom: 16, fontSize: 13 }}>
              {t("checkSpam")}
            </div>

            {/* Resend section */}
            <div style={{ background: "var(--surface, #f7f8fa)", border: "1px solid var(--border, #e5e7eb)", borderRadius: 10, padding: "16px 20px", marginBottom: 20, textAlign: "left" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <Mail size={16} color="#166534" />
                <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text, #1f2328)" }}>
                  {t("resendVerification")}
                </span>
              </div>
              <p style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.6, marginBottom: 12 }}>
                Didn't receive it? Check spam, or request a new link after 60 seconds.
                Links expire in 24 hours.
              </p>
              {resendSuccess && (
                <div className="alert alert-success" style={{ marginBottom: 10, fontSize: 12 }}>
                  ✓ A new verification email has been sent. Check your inbox.
                </div>
              )}
              {resendError && (
                <div className="alert alert-error" style={{ marginBottom: 10, fontSize: 12 }}>
                  {resendError}
                </div>
              )}
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleResend}
                disabled={cooldown > 0 || resending}
                style={{ fontSize: 13, display: "inline-flex", alignItems: "center", gap: 6 }}
              >
                {resending ? (
                  <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Sending…</>
                ) : cooldown > 0 ? (
                  <><RefreshCw size={14} /> {t("resendCooldown")} {cooldown}{t("seconds")}</>
                ) : (
                  <><RefreshCw size={14} /> {t("resendVerification")}</>
                )}
              </button>
            </div>

            <Link className="btn btn-secondary" to={ROUTES.LOGIN} style={{ display: "inline-block" }}>
              {t("backToSignIn")}
            </Link>
          </div>
        </div>
        <style>{`
          @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        `}</style>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="auth-brand"><Leaf /> {t("brand")}</div>
        <div>
          <h1>{t("signupTitle")}<br /><span>{t("signupSubtitle")}</span></h1>
        </div>
      </div>
      <div className="auth-form-wrap">
        <form className="auth-form" onSubmit={submit}>
          <div className="mobile-auth-logo"><Leaf /> {t("brand")}</div>
          <h2>{t("signupTitle")}</h2>
          <p>{t("signupSubtitle")}</p>
          <ErrorAlert message={error} />
          {verificationUrl ? (
            // Dev mode fallback: show raw URL when SMTP is not configured
            <div className="alert alert-success">
              <b>Account created!</b> SMTP is not configured — use this link to verify your email:<br />
              <a href={verificationUrl} style={{ wordBreak: "break-all" }}>{verificationUrl}</a><br />
              <button type="button" className="btn btn-secondary" style={{ marginTop: 10 }} onClick={() => navigate(ROUTES.DASHBOARD)}>
                Continue to Dashboard
              </button>
            </div>
          ) : (
            <>
              <label>
                {t("name")}
                <input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder={t("namePlaceholder")} />
                <UserRound />
              </label>
              <label>
                {t("email")}
                <input required type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder={t("emailPlaceholder")} />
                <Mail />
              </label>
              <label>
                {t("phone")}
                <input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder={t("phonePlaceholder")} />
                <Phone />
              </label>
              <div className="form-grid">
                <label>
                  {t("stateLabel")}
                  <input value={form.state} onChange={e => setForm({ ...form, state: e.target.value })} placeholder={t("statePlaceholder")} />
                </label>
                <label>
                  {t("districtLabel")}
                  <input value={form.district} onChange={e => setForm({ ...form, district: e.target.value })} placeholder={t("districtPlaceholder")} />
                </label>
                <label>
                  {t("villageLabel")}
                  <input value={form.city_village} onChange={e => setForm({ ...form, city_village: e.target.value })} placeholder={t("villagePlaceholder")} />
                </label>
                <label>
                  Language
                  <select value={form.language} onChange={e => setForm({ ...form, language: e.target.value })}>
                    <option value="en">English</option>
                    <option value="hi">हिन्दी</option>
                    <option value="gu">ગુજરાતી</option>
                    <option value="mr">मराठी</option>
                  </select>
                </label>
              </div>
              <label>
                {t("password")}
                <input required minLength={6} type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder={t("passwordPlaceholder")} />
                <LockKeyhole />
              </label>
              <Button type="submit" loading={loading}>{t("signupButton")}</Button>
              <p className="auth-switch">
                {t("alreadyHaveAccount")} <Link to={ROUTES.LOGIN}>{t("signIn")}</Link>
              </p>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
