import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Leaf, LockKeyhole, Mail, UserRound, Phone } from "lucide-react";
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
  const [verificationUrl, setVerificationUrl] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await authApi.signup(form);
      localStorage.setItem("access_token", data.access_token);
      setUser(data.user);
      setLanguage((data.user.language || "en") as any);
      if (form.phone) {
        navigate(ROUTES.VERIFY_PHONE);
      } else if (data.verification_url) {
        setVerificationUrl(data.verification_url);
      } else {
        navigate(ROUTES.DASHBOARD);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Signup failed"));
    } finally {
      setLoading(false);
    }
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
            <div className="alert alert-success">
              <b>{t("signupTitle")}</b><br />
              <a href={verificationUrl}>{verificationUrl}</a><br />
              <button type="button" className="btn btn-secondary" style={{ marginTop: 10 }} onClick={() => navigate(ROUTES.DASHBOARD)}>
                Continue
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
