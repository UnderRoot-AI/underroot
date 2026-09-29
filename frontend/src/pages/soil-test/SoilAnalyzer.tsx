import { useEffect, useState } from "react";
import { BarChart3, Leaf, Sprout, AlertTriangle, Download, FileText } from "lucide-react";
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Loading from "../../components/common/Loading";
import RecommendationCard from "../../components/recommendation/RecommendationCard";
import SoilHealthGauge from "../../components/soil/SoilHealthGauge";
import { soilApi } from "../../services/soil.api";
import { reportApi } from "../../services/report.api";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

const STATUS_BADGE: Record<string, string> = {
  Optimal: "badge-green",
  Low: "badge-yellow",
  High: "badge-yellow",
  Critical: "badge-red",
  Missing: "badge-red",
};

const BAR_COLOR: Record<string, string> = {
  Optimal:  "#166534",
  Low:      "#d97706",
  High:     "#d97706",
  Critical: "#dc2626",
  Missing:  "#9ca3af",
};

export default function SoilAnalyzer() {
  const [params] = useSearchParams();
  const testId = params.get("test");
  const t = useT();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState("");

  useEffect(() => {
    if (!testId) { setLoading(false); setError(t("noTestsYet")); return; }
    setLoading(true);
    soilApi.analyze(testId)
      .then(setData)
      .catch((e) => setError(e.response?.data?.detail || t("error")))
      .finally(() => setLoading(false));
  }, [testId]);

  async function downloadPdf() {
    if (!testId) return;
    setPdfLoading(true);
    setPdfError("");
    try {
      const report = await reportApi.generate(testId);
      const blob = await reportApi.downloadPdf(report.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `soil-report-${testId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      const msg =
        e.response?.data?.detail ||
        e.response?.statusText ||
        e.message ||
        "Could not download PDF. Try again.";
      setPdfError(msg);
    } finally {
      setPdfLoading(false);
    }
  }

  if (loading) return <Loading label={t("analyzing")} />;
  if (error) return (
    <>
      <PageHeader title={t("soilAnalyzerTitle")} subtitle={t("soilTestSubtitle")} />
      <Card><div className="alert alert-error">{error}</div></Card>
    </>
  );

  const soil = data?.soil_test;
  const analysis = data?.analysis;

  const chart = analysis?.parameter_analysis
    ? analysis.parameter_analysis
        .filter((x: any) => typeof x.value === "number")
        .map((x: any) => ({
          name: x.label.replace("Electrical Conductivity (EC)", "EC").replace("Soil Moisture", "Moisture").replace("Soil Temperature", "Temp").replace("Organic Carbon", "OC").replace("Nitrogen (N)", "N").replace("Phosphorus (P)", "P").replace("Potassium (K)", "K"),
          value: Number(x.value),
          status: x.status,
        }))
    : [];

  return (
    <>
      <PageHeader title={t("soilAnalyzerTitle")} subtitle={soil?.location || ""} />

      {/* Health + summary row */}
      <div className="report-top-grid">
        <Card>
          <div className="card-heading"><div><h2>{t("soilHealth")}</h2><p>{soil?.location || "Current field"}</p></div></div>
          <SoilHealthGauge score={soil?.health_score || 0} status={soil?.health_status} />
        </Card>
        <Card>
          <div className="card-heading"><div><h2>{t("soilHealthScore")}</h2><p>{t("reviewBeforeAnalysis")}</p></div></div>
          <div className="summary-list">
            <div><span>Data completeness</span><b>{analysis?.completeness}%</b></div>
            <div><span>Analyzer score</span><b>{analysis?.screening_score}%</b></div>
            <div><span>Missing values</span><b>{analysis?.missing_parameters?.length || 0}</b></div>
          </div>
          {analysis?.warnings?.length > 0 && (
            <div className="alert alert-error" style={{ marginTop: 8 }}>
              <AlertTriangle size={15} /> Critical parameters: {analysis.warnings.join(", ")}
            </div>
          )}
          {analysis?.deficiencies?.length > 0 && (
            <div className="alert alert-warning" style={{ marginTop: 6 }}>
              ↓ Below optimal: {analysis.deficiencies.join(", ")}
            </div>
          )}
          {analysis?.excesses?.length > 0 && (
            <div className="alert alert-warning" style={{ marginTop: 6 }}>
              ↑ Above optimal: {analysis.excesses.join(", ")}
            </div>
          )}
        </Card>
      </div>

      {/* Parameter cards */}
      <Card>
        <div className="card-heading"><div><h2>{t("soilParameters")}</h2><p>{t("soilTestSubtitle")}</p></div></div>
        <div className="parameter-grid">
          {analysis?.parameter_analysis?.map((x: any) => (
            <div className="parameter-card" key={x.key}>
              <div><span>{x.label}</span><b>{x.value == null ? "—" : x.value} {x.unit}</b></div>
              <small className={`badge ${STATUS_BADGE[x.status] || "badge-yellow"}`}>{x.status}</small>
              <p>{x.message}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Bar chart */}
      <Card>
        <div className="card-heading"><div><h2>{t("soilHealth")}</h2></div><BarChart3 size={19} /></div>
        <div style={{ height: 280 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" fontSize={10} />
              <YAxis fontSize={10} />
              <Tooltip formatter={(v, name, props) => [`${v} ${props?.payload?.unit || ""}`, props?.payload?.status || ""]} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {chart.map((entry: any, i: number) => (
                  <Cell key={i} fill={BAR_COLOR[entry.status] || "#166534"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Recommendations */}
      <Card>
        <div className="card-heading"><div><h2>{t("cropRecTitle")}</h2></div><Sprout size={19} /></div>
        {analysis?.crop_recommendations?.length
          ? <div className="recommendation-list">{analysis.crop_recommendations.map((x: any, i: number) => <RecommendationCard key={i} item={x} />)}</div>
          : <p className="muted">{t("noCropRecs")}</p>}
        <Link className="btn btn-secondary" style={{ marginTop: 12 }} to={`${ROUTES.CROPS}?test=${soil?.id}`}>{t("getCropRecs")}</Link>
      </Card>
      <Card>
        <div className="card-heading"><div><h2>{t("fertRecTitle")}</h2></div><Leaf size={19} /></div>
        {analysis?.fertilizer_recommendations?.length
          ? <div className="recommendation-list">{analysis.fertilizer_recommendations.map((x: any, i: number) => <RecommendationCard key={i} item={x} />)}</div>
          : <p className="muted">{t("noFertRecs")}</p>}
        <Link className="btn btn-secondary" style={{ marginTop: 12 }} to={`${ROUTES.FERTILIZER}?test=${soil?.id}`}>{t("getFertRecs")}</Link>
      </Card>

      {/* Download PDF */}
      <Card>
        <div className="card-heading"><div><h2>Report</h2><p>Download a PDF copy of this soil analysis</p></div><FileText size={19} /></div>
        {pdfError && <div className="alert alert-error" style={{ marginBottom: 8 }}>{pdfError}</div>}
        <div className="form-actions">
          <button
            className="btn btn-primary"
            disabled={pdfLoading}
            onClick={downloadPdf}
          >
            <Download size={16} /> {pdfLoading ? "Generating PDF…" : "Download PDF Report"}
          </button>
        </div>
      </Card>
    </>
  );
}
