import { useEffect } from "react";
import { Eye, History as HistoryIcon } from "lucide-react";
import { Link } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Loading from "../../components/common/Loading";
import EmptyState from "../../components/common/EmptyState";
import { useSoil } from "../../hooks/useSoil";
import { formatDate } from "../../utils/formatDate";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

export default function History() {
  const { tests, load, loading } = useSoil();
  const t = useT();
  useEffect(() => { load(); }, [load]);

  return (
    <>
      <PageHeader
        title={t("historyTitle")}
        subtitle={t("historySubtitle")}
        action={<Link to={ROUTES.COMPARE}><button className="btn btn-secondary">{t("compareTitle")}</button></Link>}
      />
      <Card>
        {loading ? <Loading /> : tests.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t("testOn")}</th>
                  <th>{t("location")}</th>
                  <th>{t("testDate")}</th>
                  <th>{t("healthScore")}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {tests.map(t2 => (
                  <tr key={t2.id}>
                    <td><b>#{t2.id}</b></td>
                    <td>{t2.location || t2.field_name || "—"}</td>
                    <td>{formatDate(t2.tested_at || t2.created_at)}</td>
                    <td>
                      <Badge tone={(t2.health_score || 0) >= 75 ? "green" : (t2.health_score || 0) >= 50 ? "yellow" : "red"}>
                        {t2.health_score ?? "—"}/100
                      </Badge>
                    </td>
                    <td><Link to={`${ROUTES.SOIL_ANALYZER}?test=${t2.id}`}><Eye size={17} /></Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState icon={<HistoryIcon />} title={t("noHistoryYet")} text={t("noHistoryDesc")} />
        )}
      </Card>
    </>
  );
}
