import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Leaf, LockKeyhole, Mail } from "lucide-react";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import { developerApi } from "../../services/developer.api";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

export default function DeveloperLogin() {
  const navigate = useNavigate();
  const t = useT();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await developerApi.login(email, password);
      localStorage.setItem("developer_token", data.access_token);
      navigate(ROUTES.DEVELOPER);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Developer login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="auth-brand"><Leaf /> {t("brand")}</div>
        <div>
          <h1>{t("devLoginTitle")}</h1>
          <p>{t("devLoginSubtitle")}</p>
        </div>
        <div className="auth-feature-grid">
          <div>{t("devLoginFeature1")}</div>
          <div>{t("devLoginFeature2")}</div>
          <div>{t("devLoginFeature3")}</div>
          <div>{t("devLoginFeature4")}</div>
        </div>
      </div>
      <div className="auth-form-wrap">
        <form className="auth-form" onSubmit={submit}>
          <div className="mobile-auth-logo"><Leaf /> {t("brand")}</div>
          <h2>{t("devLoginHeading")}</h2>
          <p>{t("devLoginDesc")}</p>
          <ErrorAlert message={error} />
          <label>
            {t("email")}
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder={t("emailPlaceholder")} required />
            <Mail />
          </label>
          <label>
            {t("password")}
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder={t("passwordPlaceholder")} required />
            <LockKeyhole />
          </label>
          <Button type="submit" loading={loading}>{t("openDeveloperPanel")}</Button>
        </form>
      </div>
    </div>
  );
}
