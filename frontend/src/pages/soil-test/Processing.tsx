import { useEffect, useState } from "react";
import { CheckCircle2, FileSearch, LoaderCircle, AlertTriangle } from "lucide-react";
import { useSearchParams, useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { useOCR } from "../../hooks/useOCR";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

export default function Processing() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { process, loading, error } = useOCR();
  const reportId = params.get("report");
  const t = useT();

  const [done, setDone] = useState(false);
  const [ranOnce, setRanOnce] = useState(false);

  useEffect(() => {
    if (!reportId || ranOnce) return;
    setRanOnce(true);
    process(reportId)
      .then(() => {
        // OCR succeeded — wait a beat so the user sees "Analysis complete"
        setDone(true);
        setTimeout(() => navigate(`${ROUTES.VERIFY_DATA}?report=${reportId}`), 900);
      })
      .catch(() => {
        // error is already set in useOCR; don't navigate
        setDone(false);
      });
  }, [reportId]);          // eslint-disable-line react-hooks/exhaustive-deps

  const step = (label: string, state: "done" | "active" | "pending") => (
    <span className={state === "done" ? "done" : state === "active" ? "active" : ""}>
      {state === "done" ? <CheckCircle2 size={14} /> : <LoaderCircle size={14} className={state === "active" ? "spin" : ""} />}
      {" "}{label}
    </span>
  );

  return (
    <>
      <PageHeader title={t("processingTitle")} subtitle={t("processingSubtitle")} />
      <Card>
        <div className="processing">
          <div className="processing-icon">
            {error
              ? <AlertTriangle size={42} color="#d97706" />
              : done
                ? <CheckCircle2 size={42} color="#166534" />
                : <LoaderCircle className="spin" size={42} />
            }
          </div>

          <h2>
            {error
              ? t("processingFailed")
              : done
                ? t("processingComplete")
                : t("extractingData")}
          </h2>

          <p style={{ maxWidth: 460, margin: "0 auto" }}>
            {error
              ? error
              : done
                ? t("processingComplete")
                : t("processingSubtitle")}
          </p>

          <div className="process-steps">
            {step(t("processingStep1"), "done")}
            {step(t("processingStep2"), loading ? "active" : done || error ? "done" : "pending")}
            {step(t("processingStep3"), done ? "active" : "pending")}
          </div>

          {error && (
            <div style={{ marginTop: 24, display: "flex", gap: 10, justifyContent: "center", flexWrap: "wrap" }}>
              <div className="alert alert-error" style={{ maxWidth: 420, textAlign: "left" }}>
                {t("noParametersWarning")}
              </div>
              <Button onClick={() => navigate(`${ROUTES.VERIFY_DATA}?report=${reportId}`)}>
                {t("editParameters")} →
              </Button>
            </div>
          )}
        </div>
      </Card>
    </>
  );
}
