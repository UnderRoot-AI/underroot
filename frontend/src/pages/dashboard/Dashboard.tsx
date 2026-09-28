import { useEffect, useMemo } from "react";
import { ArrowRight, CalendarDays, Leaf, Plus, TrendingUp } from "lucide-react";
import { BarChart, Bar, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { Link } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatCard from "../../components/ui/StatCard";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Loading from "../../components/common/Loading";
import EmptyState from "../../components/common/EmptyState";
import SoilHealthGauge from "../../components/soil/SoilHealthGauge";
import { useSoil } from "../../hooks/useSoil";
import { ROUTES } from "../../constants/routes";
import { formatDate } from "../../utils/formatDate";
import { useT } from "../../i18n/useT";

export default function Dashboard() {
  const { tests, load, loading } = useSoil();
  const t = useT();
  useEffect(() => { load(); }, [load]);
  const latest = tests[0];
  const average = useMemo(() =>
    tests.length ? Math.round(tests.reduce((a, b) => a + (b.health_score || 0), 0) / tests.length) : 0,
    [tests]
  );

  if (loading && !tests.length) return <Loading label={t("loading")} />;

  return (
    <>
      <PageHeader
        title={t("welcomeBack")}
        subtitle={t("dashboardSubtitle")}
        action={
          <Link to={ROUTES.SOIL_TEST}>
            <Button><Plus size={17} /> {t("newSoilTest")}</Button>
          </Link>
        }
      />
      <div className="stats-grid">
        <StatCard label={t("totalTests")} value={tests.length} helper={t("soilTests")} icon={<Leaf />} />
        <StatCard label={t("healthScore")} value={`${average}/100`} helper={t("soilHealth")} icon={<TrendingUp />} />
        <StatCard
          label={t("latestTest")}
          value={latest ? formatDate(latest.tested_at || latest.created_at) : "—"}
          helper={latest?.location || t("noTestsYet")}
          icon={<CalendarDays />}
        />
      </div>
      <div className="dashboard-grid">
        <Card>
          <div className="card-heading">
            <div>
              <h2>{t("soilHealth")}</h2>
              <p>{t("recentActivity")}</p>
            </div>
            <Link to={ROUTES.HISTORY}>{t("viewHistory")} <ArrowRight size={15} /></Link>
          </div>
          {latest ? (
            <div className="latest-health">
              <SoilHealthGauge score={latest.health_score} />
              <div className="latest-details">
                <h3>{latest.field_name || latest.location || "Current field"}</h3>
                <p>Tested {formatDate(latest.tested_at || latest.created_at)}</p>
                <div className="mini-values">
                  <span>pH <b>{latest.parameters.ph ?? "—"}</b></span>
                  <span>N <b>{latest.parameters.nitrogen ?? "—"}</b></span>
                  <span>P <b>{latest.parameters.phosphorus ?? "—"}</b></span>
                  <span>K <b>{latest.parameters.potassium ?? "—"}</b></span>
                </div>
                <div style={{ height: 150, width: "100%", minWidth: 280, marginTop: 12 }}>
                  <ResponsiveContainer>
                    <BarChart data={Object.entries(latest.parameters).filter(([, v]) => typeof v === "number").map(([k, v]) => ({ name: k.replace("nitrogen", "N").replace("phosphorus", "P").replace("potassium", "K").replace("organic_carbon", "OC"), value: Number(v) }))}>
                      <XAxis dataKey="name" fontSize={9} />
                      <Tooltip />
                      <Bar dataKey="value" radius={[5, 5, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          ) : (
            <EmptyState title={t("noTestsYet")} text={t("noTestsYetDesc")} />
          )}
        </Card>
        <Card>
          <div className="card-heading">
            <div>
              <h2>{t("quickActions")}</h2>
              <p>{t("recommendations")}</p>
            </div>
          </div>
          <div className="quick-actions">
            <Link to={ROUTES.SOIL_TEST}><span>➜</span><div><b>{t("newSoilTest")}</b><small>{t("soilTestSubtitle")}</small></div></Link>
            <Link to={ROUTES.UPLOAD_REPORT}><span>↑</span><div><b>{t("uploadReport")}</b><small>{t("uploadReportSubtitle")}</small></div></Link>
            <Link to={ROUTES.ASSISTANT}><span>✦</span><div><b>{t("askAssistant")}</b><small>{t("assistantSubtitle")}</small></div></Link>
            <Link to={ROUTES.RESOURCES}><span>⌂</span><div><b>{t("resourcesTitle")}</b><small>{t("resourcesSubtitle")}</small></div></Link>
          </div>
        </Card>
      </div>
    </>
  );
}
