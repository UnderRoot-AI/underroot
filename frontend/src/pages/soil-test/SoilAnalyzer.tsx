import { useEffect, useState } from "react";
import { BarChart3, Leaf, Sprout, AlertTriangle } from "lucide-react";
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useSearchParams, Link } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Loading from "../../components/common/Loading";
import RecommendationCard from "../../components/recommendation/RecommendationCard";
import SoilHealthGauge from "../../components/soil/SoilHealthGauge";
import { soilApi } from "../../services/soil.api";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

export default function SoilAnalyzer() {
  const [params] = useSearchParams();
  const testId = params.get("test");
  const t = useT();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!testId) { setLoading(false); setError(t("noTestsYet")); return; }
    setLoading(true);
    soilApi.analyze(testId)
      .then(setData)
      .catch((e) => setError(e.response?.data?.detail || t("error")))
      .finally(() => setLoading(false));
  }, [testId]);

  if (loading) return <Loading label={t("analyzing")} />;
  if (error) return (
    <>
      <PageHeader title={t("soilAnalyzerTitle")} subtitle={t("soilTestSubtitle")} />
      <Card><div className="alert alert-error">{error}</div></Card>
    </>
  );

  const soil = data?.soil_test;
  const analysis = data?.analysis;
  const chart = soil?.parameters
    ? Object.entries(soil.parameters).filter(([, v]) => typeof v === "number").map(([k, v]) => ({
        name: k.replace("organic_carbon", "OC").replace("nitrogen", "N").replace("phosphorus", "P").replace("potassium", "K").toUpperCase(),
        value: Number(v),
      }))
    : [];

  return (
    <>
      <PageHeader title={t("soilAnalyzerTitle")} subtitle={t("soilTestSubtitle")} />
      <div className="report-top-grid">
        <Card>
          <div className="card-heading"><div><h2>{t("soilHealth")}</h2><p>{soil?.location || "Current field"}</p></div></div>
          <SoilHealthGauge score={soil?.health_score || 0} />
        </Card>
        <Card>
          <div className="card-heading"><div><h2>{t("soilHealthScore")}</h2><p>{t("reviewBeforeAnalysis")}</p></div></div>
          <div className="summary-list">
            <div><span>Data completeness</span><b>{analysis?.completeness}%</b></div>
            <div><span>Analyzer score</span><b>{analysis?.screening_score}%</b></div>
            <div><span>Missing values</span><b>{analysis?.missing_parameters?.length || 0}</b></div>
          </div>
          {analysis?.missing_parameters?.length > 0 && (
            <div className="alert alert-error">
              <AlertTriangle size={15} /> {t("noParametersWarning")}
            </div>
          )}
        </Card>
      </div>
      <Card>
        <div className="card-heading"><div><h2>{t("soilParameters")}</h2><p>{t("soilTestSubtitle")}</p></div></div>
        <div className="parameter-grid">
          {analysis?.parameter_analysis?.map((x: any) => (
            <div className="parameter-card" key={x.key}>
              <div><span>{x.label}</span><b>{x.value == null ? "—" : x.value} {x.unit}</b></div>
              <small className={`badge ${x.status === "Good" ? "badge-green" : x.status === "Missing" ? "badge-red" : "badge-yellow"}`}>{x.status}</small>
              <p>{x.message}</p>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <div className="card-heading"><div><h2>{t("soilHealth")}</h2></div><BarChart3 size={19} /></div>
        <div style={{ height: 280 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" fontSize={10} />
              <YAxis fontSize={10} />
              <Tooltip />
              <Bar dataKey="value" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Card>
        <div className="card-heading"><div><h2>{t("cropRecTitle")}</h2></div><Sprout size={19} /></div>
        {analysis?.crop_recommendations?.length
          ? <div className="recommendation-list">{analysis.crop_recommendations.map((x: any, i: number) => <RecommendationCard key={i} item={x} />)}</div>
          : <p className="muted">{t("noCropRecs")}</p>}
        <Link className="btn btn-secondary" to={`${ROUTES.CROPS}?test=${soil?.id}`}>{t("getCropRecs")}</Link>
      </Card>
      <Card>
        <div className="card-heading"><div><h2>{t("fertRecTitle")}</h2></div><Leaf size={19} /></div>
        {analysis?.fertilizer_recommendations?.length
          ? <div className="recommendation-list">{analysis.fertilizer_recommendations.map((x: any, i: number) => <RecommendationCard key={i} item={x} />)}</div>
          : <p className="muted">{t("noFertRecs")}</p>}
        <Link className="btn btn-secondary" to={`${ROUTES.FERTILIZER}?test=${soil?.id}`}>{t("getFertRecs")}</Link>
      </Card>
    </>
  );
}
