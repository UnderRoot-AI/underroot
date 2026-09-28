import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, XCircle, Leaf } from "lucide-react";
import { authApi } from "../../services/auth.api";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [message, setMessage] = useState("");
  const t = useT();

  useEffect(() => {
    const token = params.get("token");
    if (!token) { setState("error"); setMessage("Verification token is missing."); return; }
    authApi.verifyEmail(token)
      .then(r => { setState("ok"); setMessage(r.message); })
      .catch(e => { setState("error"); setMessage(e.response?.data?.detail || "The verification link is invalid or expired."); });
  }, [params]);

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
          {state === "loading" ? (
            <p>{t("loading")}</p>
          ) : state === "ok" ? (
            <>
              <CheckCircle2 size={55} color="#166534" />
              <h2>{t("emailVerified")}</h2>
              <p>{message}</p>
              <Link className="btn btn-primary" to={ROUTES.LOGIN}>
                {t("backToSignIn")}
              </Link>
            </>
          ) : (
            <>
              <XCircle size={55} color="#b42318" />
              <h2>{t("error")}</h2>
              <p>{message}</p>
              <Link className="btn btn-secondary" to={ROUTES.LOGIN}>
                {t("backToSignIn")}
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
