import { useEffect, useState } from "react";
import { CheckCircle2, AlertTriangle } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import Loading from "../../components/common/Loading";
import { SOIL_PARAMETERS } from "../../constants/soilParameters";
import { ROUTES } from "../../constants/routes";
import { reportApi, verifyReport } from "../../services/report.api";
import { useReportStore } from "../../store/reportStore";
import { getErrorMessage } from "../../utils/errorHandler";
import { useT } from "../../i18n/useT";

export default function VerifyData() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const reportId = params.get("report");
  const t = useT();
  const [values, setValues] = useState<Record<string, string>>({});
  const [location, setLocation] = useState("");
  const [coords, setCoords] = useState({ latitude: "", longitude: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [extractedCount, setExtractedCount] = useState(0);
  const setCurrentReport = useReportStore((s) => s.setCurrentReport);

  useEffect(() => {
    if (!reportId) { setLoading(false); return; }
    reportApi.get(reportId)
      .then(report => {
        setCurrentReport(report);
        const extracted = report.extracted_parameters || {};
        const filled = Object.fromEntries(
          Object.entries(extracted).map(([k, v]) => [k, v == null ? "" : String(v)])
        );
        setValues(filled);
        setExtractedCount(Object.values(filled).filter(v => v !== "").length);
      })
      .catch(e => setError(getErrorMessage(e)))
      .finally(() => setLoading(false));
  }, [reportId, setCurrentReport]);

  async function save() {
    if (!reportId) return;
    const filledCount = Object.values(values).filter(v => v !== "").length;
    if (filledCount === 0) {
      setError("Please enter at least one soil parameter before confirming.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const parameters = Object.fromEntries(
        Object.entries(values)
          .filter(([, v]) => v !== "")
          .map(([k, v]) => [k, Number(v)])
      );
      const report = await verifyReport(reportId, {
        parameters,
        location,
        latitude: coords.latitude ? Number(coords.latitude) : undefined,
        longitude: coords.longitude ? Number(coords.longitude) : undefined,
      });
      setCurrentReport(report);
      navigate(`${ROUTES.SOIL_ANALYZER}?test=${report.soil_test_id}`);
    } catch (e) {
      setError(getErrorMessage(e, "Could not verify report"));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <Loading label={t("loading")} />;

  const filledNow = Object.values(values).filter(v => v !== "").length;

  return (
    <>
      <PageHeader title={t("verifyDataTitle")} subtitle={t("verifyDataSubtitle")} />
      <Card>
        {extractedCount > 0 ? (
          <div className="verify-banner">
            <CheckCircle2 />
            <div>
              <b>{extractedCount} / {SOIL_PARAMETERS.length} {t("parametersExtracted")}</b>
              <span>{t("reviewBeforeAnalysis")}</span>
            </div>
          </div>
        ) : (
          <div className="verify-banner" style={{ background: "#fff8ec", borderColor: "#f6d860", color: "#865c00" }}>
            <AlertTriangle />
            <div>
              <b>{t("noParametersWarning")}</b>
            </div>
          </div>
        )}

        <div className="form-grid" style={{ marginTop: 16 }}>
          <label>
            {t("location")}
            <input value={location} onChange={e => setLocation(e.target.value)} placeholder="e.g. North Field" />
          </label>
          <div className="geo-row">
            <label>Latitude<input value={coords.latitude} onChange={e => setCoords({ ...coords, latitude: e.target.value })} placeholder="23.15" /></label>
            <label>Longitude<input value={coords.longitude} onChange={e => setCoords({ ...coords, longitude: e.target.value })} placeholder="72.03" /></label>
            <span />
          </div>
        </div>

        <div className="parameter-input-grid" style={{ marginTop: 16 }}>
          {SOIL_PARAMETERS.map(p => (
            <label key={p.key}>
              {p.label} {p.unit && <small>({p.unit})</small>}
              <input
                type="number" step="any" min={p.min} max={p.max}
                value={values[p.key] || ""}
                onChange={e => setValues({ ...values, [p.key]: e.target.value })}
                placeholder={`e.g. ${p.min ?? 0}–${p.max ?? "—"}`}
              />
            </label>
          ))}
        </div>

        <ErrorAlert message={error} />

        <div className="form-actions">
          <span className="muted" style={{ marginRight: "auto" }}>
            {filledNow} / {SOIL_PARAMETERS.length} {t("parametersExtracted")}
          </span>
          <Button loading={saving} onClick={save} disabled={filledNow === 0}>
            {t("confirmAndAnalyze")}
          </Button>
        </div>
      </Card>
    </>
  );
}
