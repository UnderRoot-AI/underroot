import { useEffect, useState } from "react";
import { Eye, FileText } from "lucide-react";
import { Link } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Loading from "../../components/common/Loading";
import EmptyState from "../../components/common/EmptyState";
import Badge from "../../components/ui/Badge";
import { reportStoreApi, type StoredSoilReport } from "../../services/reportStore.api";
import { ROUTES } from "../../constants/routes";
import { formatDate } from "../../utils/formatDate";
import { useT } from "../../i18n/useT";

export default function SoilReport() {
  const [rows, setRows] = useState<StoredSoilReport[]>([]);
  const [loading, setLoading] = useState(true);
  const t = useT();

  useEffect(() => {
    reportStoreApi.list().then(setRows).finally(() => setLoading(false));
  }, []);

  return (
    <>
      <PageHeader title={t("soilReportTitle")} subtitle={t("soilReportSubtitle")} />
      <Card>
        {loading ? <Loading /> : rows.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t("soilReportTitle")}</th>
                  <th>File</th>
                  <th>{t("status")}</th>
                  <th>{t("parameterName")}</th>
                  <th>{t("testDate")}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map(r => (
                  <tr key={r.id}>
                    <td><b>#{r.id}</b></td>
                    <td>{r.file_name || "Generated soil analysis"}</td>
                    <td>
                      <Badge tone={r.status === "verified" ? "green" : r.status === "processed" ? "blue" : "yellow"}>
                        {r.status}
                      </Badge>
                    </td>
                    <td>{r.extracted_parameters ? Object.keys(r.extracted_parameters).length : "0"} values</td>
                    <td>{formatDate(r.created_at)}</td>
                    <td>
                      {r.soil_test_id
                        ? <Link to={`${ROUTES.SOIL_ANALYZER}?test=${r.soil_test_id}`} title={t("viewReport")}><Eye size={17} /></Link>
                        : <FileText size={17} />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState icon={<FileText />} title={t("noHistoryYet")} text={t("noHistoryDesc")} />
        )}
      </Card>
    </>
  );
}
