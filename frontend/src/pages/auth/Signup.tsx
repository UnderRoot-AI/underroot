import { useState, useRef, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Leaf, LockKeyhole, Mail, UserRound, Phone, CheckCircle, RefreshCw, Loader2, MapPin } from "lucide-react";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import { authApi } from "../../services/auth.api";
import { useAuthStore } from "../../store/authStore";
import { useLanguageStore } from "../../store/languageStore";
import { ROUTES } from "../../constants/routes";
import { getErrorMessage } from "../../utils/errorHandler";
import { useT } from "../../i18n/useT";
import { INDIA_STATES, getDistricts } from "../../constants/indiaLocations";

// ── Client-side validation ────────────────────────────────────────────────────
interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  state?: string;
  district?: string;
  phone?: string;
}

function validateForm(form: {
  name: string; email: string; password: string; confirmPassword: string;
  state: string; district: string; phone: string;
}): FormErrors {
  const errors: FormErrors = {};
  if (!form.name.trim() || form.name.trim().length < 2)
    errors.name = "Name must be at least 2 characters";
  if (!form.email.trim())
    errors.email = "Email is required";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
    errors.email = "Enter a valid email address";
  if (!form.password)
    errors.password = "Password is required";
  else if (form.password.length < 6)
    errors.password = "Password must be at least 6 characters";
  if (!form.confirmPassword)
    errors.confirmPassword = "Please confirm your password";
  else if (form.password !== form.confirmPassword)
    errors.confirmPassword = "Passwords do not match";
  if (!form.state)
    errors.state = "Please select your state";
  if (!form.district)
    errors.district = "Please select your district";
  if (form.phone.trim()) {
    const cleaned = form.phone.trim();
    if (!/^(\+91[-\s]?|0)?[6-9]\d{9}$/.test(cleaned))
      errors.phone = "Enter a valid 10-digit Indian mobile number (e.g. 9876543210)";
  }
  return errors;
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function Signup() {
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const t = useT();

  const [form, setForm] = useState({
    name: "", email: "", password: "", confirmPassword: "",
    phone: "", state: "", district: "", city_village: "", language: "en",
  });
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [verificationUrl, setVerificationUrl] = useState("");
  const [emailSent, setEmailSent] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState("");

  // Derived: districts for the selected state
  const districts = getDistricts(form.state);

  // Resend state
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
    setResending(true); setResendError(""); setResendSuccess(false);
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

  function handleStateChange(newState: string) {
    setForm(f => ({ ...f, state: newState, district: "" }));
    setFieldErrors(e => ({ ...e, state: undefined, district: undefined }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");

    const errors = validateForm(form);
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    setLoading(true);
    try {
      const payload = {
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        phone: form.phone.trim() || undefined,
        state: form.state,
        district: form.district,
        city_village: form.city_village.trim() || undefined,
        language: form.language,
      };
      const data = await authApi.signup(payload);
      localStorage.setItem("access_token", data.access_token);
      setUser(data.user);
      setLanguage((data.user.language || "en") as any);
      setRegisteredEmail(form.email.trim());

      // Flow: Signup → email verification → login.
      // Phone OTP is NOT part of this flow regardless of whether phone was provided.
      if (data.verification_url) {
        // Dev mode: SMTP not configured, raw URL returned for convenience
        setVerificationUrl(data.verification_url);
      } else if (data.verification_required) {
        // Production mode: email dispatched via SMTP, show check-inbox screen
        setEmailSent(true);
      } else {
        // Email already verified (shouldn't happen for new signups)
        navigate(ROUTES.DASHBOARD);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Signup failed"));
    } finally {
      setLoading(false);
    }
  }

  // ── Post-signup: email dispatched (SMTP configured) ───────────────────────
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
              Click the link to activate your account before signing in.
            </p>
            <div className="alert alert-success" style={{ textAlign: "left", marginBottom: 16, fontSize: 13 }}>
              {t("checkSpam")}
            </div>
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
                {resending
                  ? <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Sending…</>
                  : cooldown > 0
                    ? <><RefreshCw size={14} /> {t("resendCooldown")} {cooldown}{t("seconds")}</>
                    : <><RefreshCw size={14} /> {t("resendVerification")}</>
                }
              </button>
            </div>
            <Link className="btn btn-secondary" to={ROUTES.LOGIN} style={{ display: "inline-block" }}>
              {t("backToSignIn")}
            </Link>
          </div>
        </div>
        <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  // ── Signup form ──────────────────────────────────────────────────────────
  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="auth-brand"><Leaf /> {t("brand")}</div>
        <div>
          <h1>{t("signupTitle")}<br /><span>{t("signupSubtitle")}</span></h1>
        </div>
      </div>
      <div className="auth-form-wrap">
        <form className="auth-form" onSubmit={submit} noValidate>
          <div className="mobile-auth-logo"><Leaf /> {t("brand")}</div>
          <h2>{t("signupTitle")}</h2>
          <p>{t("signupSubtitle")}</p>
          <ErrorAlert message={error} />

          {verificationUrl ? (
            // Dev mode: SMTP not configured — raw link shown for convenience
            <div className="alert alert-success">
              <b>Account created!</b> SMTP is not configured — use this link to verify your email:<br />
              <a href={verificationUrl} style={{ wordBreak: "break-all" }}>{verificationUrl}</a>
            </div>
          ) : (
            <>
              {/* Name */}
              <label>
                {t("name")} <span style={{ color: "var(--red, #dc2626)" }}>*</span>
                <input
                  required
                  value={form.name}
                  onChange={e => { setForm({ ...form, name: e.target.value }); setFieldErrors(fe => ({ ...fe, name: undefined })); }}
                  placeholder={t("namePlaceholder")}
                />
                <UserRound />
                {fieldErrors.name && <span className="field-error">{fieldErrors.name}</span>}
              </label>

              {/* Email */}
              <label>
                {t("email")} <span style={{ color: "var(--red, #dc2626)" }}>*</span>
                <input
                  required
                  type="email"
                  value={form.email}
                  onChange={e => { setForm({ ...form, email: e.target.value }); setFieldErrors(fe => ({ ...fe, email: undefined })); }}
                  placeholder={t("emailPlaceholder")}
                />
                <Mail />
                {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
              </label>

              {/* Phone — optional */}
              <label>
                Mobile Number <span style={{ color: "var(--muted)", fontSize: 11, fontWeight: 400 }}>(Optional)</span>
                <input
                  value={form.phone}
                  onChange={e => { setForm({ ...form, phone: e.target.value }); setFieldErrors(fe => ({ ...fe, phone: undefined })); }}
                  placeholder="e.g. 9876543210"
                  inputMode="tel"
                />
                <Phone />
                {fieldErrors.phone && <span className="field-error">{fieldErrors.phone}</span>}
              </label>

              {/* State dropdown */}
              <label>
                {t("stateLabel")} <span style={{ color: "var(--red, #dc2626)" }}>*</span>
                <div style={{ position: "relative" }}>
                  <select
                    required
                    value={form.state}
                    onChange={e => handleStateChange(e.target.value)}
                    style={{ paddingLeft: 36 }}
                  >
                    <option value="">Select your state</option>
                    {INDIA_STATES.map(s => (
                      <option key={s.name} value={s.name}>{s.name}</option>
                    ))}
                  </select>
                  <MapPin size={15} style={{ position: "absolute", left: 11, top: "50%", transform: "translateY(-50%)", color: "var(--muted)", pointerEvents: "none" }} />
                </div>
                {fieldErrors.state && <span className="field-error">{fieldErrors.state}</span>}
              </label>

              {/* District dropdown */}
              <label>
                {t("districtLabel")} <span style={{ color: "var(--red, #dc2626)" }}>*</span>
                <select
                  required
                  value={form.district}
                  disabled={!form.state}
                  onChange={e => { setForm({ ...form, district: e.target.value }); setFieldErrors(fe => ({ ...fe, district: undefined })); }}
                >
                  <option value="">{form.state ? "Select your district" : "Select a state first"}</option>
                  {districts.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
                {fieldErrors.district && <span className="field-error">{fieldErrors.district}</span>}
              </label>

              {/* City/Village — optional */}
              <label>
                {t("villageLabel")} <span style={{ color: "var(--muted)", fontSize: 11, fontWeight: 400 }}>(Optional)</span>
                <input
                  value={form.city_village}
                  onChange={e => setForm({ ...form, city_village: e.target.value })}
                  placeholder={t("villagePlaceholder")}
                />
              </label>

              {/* Language */}
              <label>
                Language
                <select value={form.language} onChange={e => setForm({ ...form, language: e.target.value })}>
                  <option value="en">English</option>
                  <option value="hi">हिन्दी</option>
                  <option value="gu">ગુજરાતી</option>
                  <option value="mr">मराठी</option>
                </select>
              </label>

              {/* Password */}
              <label>
                {t("password")} <span style={{ color: "var(--red, #dc2626)" }}>*</span>
                <input
                  required
                  minLength={6}
                  type="password"
                  value={form.password}
                  onChange={e => { setForm({ ...form, password: e.target.value }); setFieldErrors(fe => ({ ...fe, password: undefined, confirmPassword: undefined })); }}
                  placeholder={t("passwordPlaceholder")}
                />
                <LockKeyhole />
                {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
              </label>

              {/* Confirm password */}
              <label>
                Confirm Password <span style={{ color: "var(--red, #dc2626)" }}>*</span>
                <input
                  required
                  type="password"
                  value={form.confirmPassword}
                  onChange={e => { setForm({ ...form, confirmPassword: e.target.value }); setFieldErrors(fe => ({ ...fe, confirmPassword: undefined })); }}
                  placeholder="Re-enter your password"
                />
                <LockKeyhole />
                {fieldErrors.confirmPassword && <span className="field-error">{fieldErrors.confirmPassword}</span>}
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
