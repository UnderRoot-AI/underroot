import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, XCircle, Leaf, Loader2, Mail, RefreshCw } from "lucide-react";
import { authApi } from "../../services/auth.api";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";
import { getErrorMessage } from "../../utils/errorHandler";

const RESEND_COOLDOWN_SECONDS = 60;

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const [state, setState] = useState<"loading" | "ok" | "error" | "already_verified">("loading");
  const [message, setMessage] = useState("");
  const t = useT();

  // Resend state
  const [resending, setResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [resendError, setResendError] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const cooldownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setState("error");
      setMessage("Verification token is missing from the link.");
      return;
    }
    authApi.verifyEmail(token)
      .then(r => {
        setState("ok");
        setMessage(r.message ?? t("emailVerified"));
      })
      .catch(e => {
        const detail: string = e.response?.data?.detail ?? "";
        if (detail.toLowerCase().includes("already")) {
          setState("already_verified");
          setMessage("Your email address is already verified.");
        } else {
          setState("error");
          setMessage(detail || "The verification link is invalid or has expired.");
        }
      });
  }, [params]); // eslint-disable-line react-hooks/exhaustive-deps

  function startCooldown() {
    setCooldown(RESEND_COOLDOWN_SECONDS);
    cooldownRef.current = setInterval(() => {
      setCooldown(prev => {
        if (prev <= 1) {
          clearInterval(cooldownRef.current!);
          return 0;
        }
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
      setResendError(getErrorMessage(err, "Failed to resend verification email. Please try again."));
    } finally {
      setResending(false);
    }
  }

  // Clean up interval on unmount
  useEffect(() => () => { if (cooldownRef.current) clearInterval(cooldownRef.current); }, []);

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

          {state === "loading" && (
            <div style={{ padding: "40px 0" }}>
              <Loader2 size={48} color="#166534" style={{ animation: "spin 1s linear infinite", margin: "0 auto 16px" }} />
              <p style={{ color: "var(--muted)", fontSize: 14 }}>{t("loading")}</p>
            </div>
          )}

          {state === "ok" && (
            <>
              <div style={{ width: 72, height: 72, borderRadius: "50%", background: "var(--light)", color: "var(--green)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
                <CheckCircle2 size={40} color="#166534" />
              </div>
              <h2 style={{ marginBottom: 8 }}>{t("emailVerified")}</h2>
              <p style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.7, marginBottom: 24 }}>{message}</p>
              <Link className="btn btn-primary" to={ROUTES.LOGIN}>
                {t("backToSignIn")}
              </Link>
            </>
          )}

          {state === "already_verified" && (
            <>
              <div style={{ width: 72, height: 72, borderRadius: "50%", background: "var(--light)", color: "var(--green)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
                <CheckCircle2 size={40} color="#166534" />
              </div>
              <h2 style={{ marginBottom: 8 }}>Already verified</h2>
              <p style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.7, marginBottom: 24 }}>
                Your email is already verified. You can sign in to your account.
              </p>
              <Link className="btn btn-primary" to={ROUTES.LOGIN}>
                {t("backToSignIn")}
              </Link>
            </>
          )}

          {state === "error" && (
            <>
              <div style={{ width: 72, height: 72, borderRadius: "50%", background: "#fff0ef", color: "#b42318", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
                <XCircle size={40} color="#b42318" />
              </div>
              <h2 style={{ marginBottom: 8 }}>{t("error")}</h2>
              <p style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.7, marginBottom: 24 }}>
                {message}
              </p>

              {/* Resend verification section */}
              <div style={{ background: "var(--surface, #f7f8fa)", border: "1px solid var(--border, #e5e7eb)", borderRadius: 10, padding: "16px 20px", marginBottom: 20, textAlign: "left" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <Mail size={16} color="#166534" />
                  <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text, #1f2328)" }}>
                    Resend verification email
                  </span>
                </div>
                <p style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.6, marginBottom: 12 }}>
                  If your link expired, request a new verification email. You must be signed in.
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
            </>
          )}
        </div>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
