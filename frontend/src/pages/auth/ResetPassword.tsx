import { useState, type FormEvent } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { Leaf, LockKeyhole, Eye, EyeOff, CheckCircle, AlertCircle } from "lucide-react";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import { authApi } from "../../services/auth.api";
import { ROUTES } from "../../constants/routes";
import { getErrorMessage } from "../../utils/errorHandler";
import { useT } from "../../i18n/useT";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const t = useT();

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  // Password strength
  const strength = (() => {
    if (password.length === 0) return 0;
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    return score;
  })();
  const strengthLabel = ["", t("weak"), t("fair"), t("good"), t("strong")][strength];
  const strengthColor = ["", "#dc2626", "#d97706", "#2563eb", "#166534"][strength];

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!token) { setError(t("invalidResetLink")); return; }
    if (password !== confirm) { setError(t("passwordsDoNotMatch")); return; }
    if (password.length < 6) { setError(t("passwordTooShort")); return; }
    setLoading(true);
    try {
      await authApi.resetPassword(token, password);
      setDone(true);
      setTimeout(() => navigate(ROUTES.LOGIN), 3000);
    } catch (err) {
      setError(getErrorMessage(err, t("resetFailed")));
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <div className="auth-page">
        <div className="auth-visual">
          <div className="auth-brand"><Leaf /> {t("brand")}</div>
          <div><h1>{t("invalidLink")}</h1></div>
        </div>
        <div className="auth-form-wrap">
          <div className="auth-form">
            <div style={{ textAlign: "center" }}>
              <div style={{ width: 64, height: 64, borderRadius: "50%", background: "#fff0ef", color: "#b42318", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
                <AlertCircle size={32} />
              </div>
              <h2>{t("invalidLink")}</h2>
              <p style={{ color: "var(--muted)", fontSize: 13 }}>{t("invalidLinkDesc")}</p>
              <Link to={ROUTES.FORGOT_PASSWORD} className="btn btn-primary" style={{ display: "inline-flex", marginTop: 16 }}>
                {t("requestNewLink")}
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="auth-brand"><Leaf /> {t("brand")}</div>
        <div>
          <h1>{t("resetPasswordTitle")}<br /></h1>
          <p>{t("resetPasswordDesc")}</p>
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

          {done ? (
            <div style={{ textAlign: "center", padding: "20px 0" }}>
              <div style={{ width: 64, height: 64, borderRadius: "50%", background: "var(--light)", color: "var(--green)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
                <CheckCircle size={32} />
              </div>
              <h2 style={{ marginBottom: 8 }}>{t("passwordUpdated")}</h2>
              <p style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.7 }}>
                {t("passwordUpdatedDesc")}
              </p>
              <div className="alert alert-success" style={{ marginTop: 16 }}>
                {t("confirmationEmailSent")}
              </div>
            </div>
          ) : (
            <>
              <h2>{t("setNewPassword")}</h2>
              <p>{t("resetPasswordDesc")}</p>
              <ErrorAlert message={error} />
              <form onSubmit={submit}>
                <label>
                  {t("newPasswordLabel")}
                  <input
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder={t("passwordPlaceholder")}
                    required
                    minLength={6}
                    autoFocus
                    style={{ paddingRight: 38 }}
                  />
                  <button
                    type="button"
                    tabIndex={-1}
                    onClick={() => setShowPw(v => !v)}
                    style={{ position: "absolute", right: 12, bottom: 10, background: "none", border: "none", cursor: "pointer", color: "#93a097", padding: 0 }}
                  >
                    {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </label>

                {/* strength bar */}
                {password.length > 0 && (
                  <div style={{ marginTop: -6, marginBottom: 8 }}>
                    <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
                      {[1, 2, 3, 4].map(i => (
                        <div key={i} style={{ flex: 1, height: 4, borderRadius: 3, background: i <= strength ? strengthColor : "#dce6de", transition: ".2s" }} />
                      ))}
                    </div>
                    <div style={{ fontSize: 10, color: strengthColor, fontWeight: 700 }}>{strengthLabel}</div>
                  </div>
                )}

                <label style={{ marginTop: 12 }}>
                  {t("confirmPasswordLabel")}
                  <input
                    type={showPw ? "text" : "password"}
                    value={confirm}
                    onChange={e => setConfirm(e.target.value)}
                    placeholder={t("passwordPlaceholder")}
                    required
                  />
                  <LockKeyhole />
                </label>

                {confirm && password !== confirm && (
                  <div style={{ fontSize: 11, color: "#b42318", marginTop: -6, marginBottom: 4 }}>
                    {t("passwordsDoNotMatch")}
                  </div>
                )}

                <Button type="submit" loading={loading} style={{ width: "100%", marginTop: 10 }}>
                  {t("resetButton")}
                </Button>
              </form>
              <p className="auth-switch">
                <Link to={ROUTES.LOGIN}>{t("backToSignIn")}</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
