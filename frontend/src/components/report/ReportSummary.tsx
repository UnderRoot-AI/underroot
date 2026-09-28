import { FileText, MapPin, CalendarDays } from "lucide-react";
import type { SoilReport } from "../../types/report";
import { formatDate } from "../../utils/formatDate";

export default function ReportSummary({ report }: { report: SoilReport }) {
  return (
    <div className="report-summary">
      <div className="report-icon"><FileText /></div>
      <div>
        <h3>{report.file_name || "Soil Report"}</h3>
        <div className="report-meta">
          <span><CalendarDays size={14}/> {formatDate(report.created_at)}</span>
          {report.status && <span>{report.status}</span>}
          <span><MapPin size={14}/> Soil analysis</span>
        </div>
      </div>
    </div>
  );
}
