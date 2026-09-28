import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CheckCircle2, Leaf, Phone } from "lucide-react";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import { authApi } from "../../services/auth.api";
import { useAuthStore } from "../../store/authStore";
import { ROUTES } from "../../constants/routes";
import { getErrorMessage } from "../../utils/errorHandler";
import { useT } from "../../i18n/useT";

export default function VerifyPhone() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const t = useT();
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [devOtp, setDevOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  useEffect(() => {
    if (!user?.phone || user.phone_verified) {
      if (user?.phone_verified) navigate(ROUTES.DASHBOARD);
      return;
    }
    send();
  }, []);

  async function send() {
    if (!user?.phone) return;
    setError(""); setMessage("");
    try {
      const r = await authApi.requestPhoneOtp(user.phone);
      setSent(true);
      setMessage(r.message);
      setDevOtp(r.development_otp || "");
    } catch (e) {
      setError(getErrorMessage(e, "Could not send verification code"));
    }
  }

  async function verify(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await authApi.verifyPhoneOtp(otp);
      const fresh = await authApi.me();
      useAuthStore.getState().setUser(fresh);
      navigate(ROUTES.DASHBOARD);
    } catch (e) {
      setError(getErrorMessage(e, "Invalid verification code"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="auth-brand"><Leaf /> {t("brand")}</div>
        <div>
          <h1>{t("verifyPhoneTitle")}<br /><span>{t("verifyPhoneSubtitle")}</span></h1>
          <p>{t("verifyPhoneSubtitle")}</p>
        </div>
      </div>
      <div className="auth-form-wrap">
        <form className="auth-form" onSubmit={verify}>
          <div className="mobile-auth-logo"><Leaf /> {t("brand")}</div>
          <h2>{t("phoneVerification")}</h2>
          <p>{t("phoneSentTo")} {user?.phone || "your phone"}.</p>
          <ErrorAlert message={error} />
          {message && (
            <div className="alert alert-success">
              {message}
              {devOtp && <><br /><b>{t("developmentOtp")} {devOtp}</b></>}
            </div>
          )}
          <label>
            {t("verificationCode")}
            <input
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={otp}
              onChange={e => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="6-digit code"
              required
            />
            <Phone />
          </label>
          <Button type="submit" loading={loading}>{t("verifyPhone")}</Button>
          {sent && (
            <button type="button" className="btn btn-secondary" style={{ marginTop: 10 }} onClick={send}>
              {t("sendNewCode")}
            </button>
          )}
          <p className="auth-switch">
            <Link to={ROUTES.DASHBOARD}>{t("continueLater")}</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
