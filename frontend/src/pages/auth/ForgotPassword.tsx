import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Leaf, Mail, ArrowLeft, CheckCircle } from "lucide-react";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import { authApi } from "../../services/auth.api";
import { ROUTES } from "../../constants/routes";
import { getErrorMessage } from "../../utils/errorHandler";
import { useT } from "../../i18n/useT";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const t = useT();

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(getErrorMessage(err, "Something went wrong. Please try again."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="auth-brand"><Leaf /> {t("brand")}</div>
        <div>
          <h1>{t("forgotPasswordTitle")}<br /><span>{t("forgotPasswordSubtitle")}</span></h1>
          <p>{t("forgotPasswordDesc")}</p>
        </div>
        <div className="auth-feature-grid">
          <div>{t("resetFeature1")}</div>
          <div>{t("resetFeature2")}</div>
          <div>{t("resetFeature3")}</div>
          <div>{t("resetFeature4")}</div>
        </div>
      </div>

      <div className="auth-form-wrap">
        <div className="auth-form">
          <div className="mobile-auth-logo"><Leaf /> {t("brand")}</div>

          {sent ? (
            <div style={{ textAlign: "center", padding: "20px 0" }}>
              <div style={{
                width: 64, height: 64, borderRadius: "50%",
                background: "var(--light)", color: "var(--green)",
                display: "flex", alignItems: "center", justifyContent: "center",
                margin: "0 auto 20px",
              }}>
                <CheckCircle size={32} />
              </div>
              <h2 style={{ marginBottom: 8 }}>{t("resetLinkSent")}</h2>
              <p style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.7, marginBottom: 24 }}>
                {t("resetLinkSentDesc")}
              </p>
              <div className="alert alert-success" style={{ textAlign: "left" }}>
                {t("checkSpam")}
              </div>
              <Link to={ROUTES.LOGIN} style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--green)", fontWeight: 700, fontSize: 13, justifyContent: "center", marginTop: 20 }}>
                <ArrowLeft size={14} /> {t("backToLogin")}
              </Link>
            </div>
          ) : (
            <>
              <h2>{t("forgotPasswordTitle")}</h2>
              <p>{t("forgotPasswordDesc")}</p>
              <ErrorAlert message={error} />
              <form onSubmit={submit}>
                <label>
                  {t("email")}
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder={t("emailPlaceholder")}
                    required
                    autoFocus
                  />
                  <Mail />
                </label>
                <Button type="submit" loading={loading} style={{ width: "100%", marginTop: 8 }}>
                  {t("sendResetLink")}
                </Button>
              </form>
              <p className="auth-switch">
                <Link to={ROUTES.LOGIN} style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                  <ArrowLeft size={13} /> {t("backToLogin")}
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
